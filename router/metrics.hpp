// =============================================================================
// Task 11.7 — llama-router `metrics`: the §4.4 per-request JSONL ledger plus
// the in-memory aggregate served by /conductor/metrics.
//
// Exactly two exports, mirroring affinity.hpp's dependency-light shape:
// RequestRecord (one request's ledger line under the pinned camelCase keys)
// and MetricsLedger (the per-request append plus the aggregate). NO httplib
// here — the two /conductor routes stay registered in router.hpp, where every
// other route lives, so the endpoints keep the pool-exhaustion property 11.4
// proved rather than acquiring a second server surface.
//
// G5 fail-soft governs the file: a ledger write failure is logged at warn,
// naming the configured ledgerPath, and NEVER thrown — the proxied response
// crosses unchanged and the in-memory counters still advance, so the endpoint
// does not silently under-count what the file lost. Each append is a single
// write of `<compact json>\n`, flushed per line: a crash loses at most the
// in-flight line, and the module only ever appends, never rewrites, so a
// pre-existing ledger is preserved byte-for-byte. The aggregate is in-memory
// since construction — a prior run's lines contribute nothing to summary(),
// which is why Phase 14's bench reads the FILE rather than the endpoint.
//
// Header-only, matching config.hpp / router.hpp / admission.hpp / affinity.hpp.
// =============================================================================

#pragma once

#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <system_error>
#include <vector>

#include "router/config.hpp"

namespace conductor::router {

    namespace detail {

        // The ledger's wall-clock stamp, UTC, to the millisecond:
        // `2026-08-26T21:35:12.482+00:00`. Pure, so it is pinned by an exact
        // string rather than by a range around the clock.
        //
        // The offset is spelled `+00:00` and not `Z`. Both are valid ISO-8601
        // and only one of them parses under /usr/bin/python3, the 3.9
        // interpreter scripts/test-conductor.sh pins: its
        // datetime.fromisoformat rejects a trailing `Z`. Every program that
        // reads this file is one of those scripts.
        //
        // Lexicographic order is chronological order in this format, so the
        // ledger sorts with no parser at all.
        [[nodiscard]] inline std::string formatLedgerTimestamp(
            std::chrono::system_clock::time_point instant) {
            const auto stamp = std::chrono::floor<std::chrono::milliseconds>(instant);
            const auto midnight = std::chrono::floor<std::chrono::days>(stamp);
            const std::chrono::year_month_day date{ midnight };
            const std::chrono::hh_mm_ss<std::chrono::milliseconds> clock{ stamp - midnight };

            char text[32];
            std::snprintf(text, sizeof(text), "%04d-%02u-%02uT%02d:%02d:%02d.%03d+00:00",
                          static_cast<int>(date.year()), static_cast<unsigned>(date.month()),
                          static_cast<unsigned>(date.day()),
                          static_cast<int>(clock.hours().count()),
                          static_cast<int>(clock.minutes().count()),
                          static_cast<int>(clock.seconds().count()),
                          static_cast<int>(clock.subseconds().count()));

            return std::string(text);
        }

    }  // namespace detail

    // ONE request's ledger line, exactly §4.4's field set (plan lines
    // 1680-1684) under the pinned camelCase keys. Every key is PRESENT on
    // every serialized line; absence is JSON null, never a missing key, so a
    // downstream reader parses the ledger with a fixed column set.
    struct RequestRecord {
        std::string model;                         // body `model`; "" per SG-3
        std::optional<std::string> role;           // RequestTags verbatim
        std::optional<std::string> group;          // RequestTags verbatim
        std::string priority;                      // RESOLVED class, SG-4
        std::int64_t queueWaitMs{ 0 };             // measured across admit()
        std::optional<std::int64_t> upstreamMs;    // null when never attempted
        std::optional<std::int64_t> promptTokens;  // from `usage`
        std::optional<std::int64_t> completionTokens;
        nlohmann::json timings;                    // VERBATIM copy; null absent
        std::optional<bool> schemaMissing;         // caller-supplied (11.6)
        std::optional<bool> schemaConformed;       // caller-supplied (11.6)
        int status{ 0 };                           // as returned to the client
    };

    /**
     * Per-request append + in-memory aggregate, one mutex over both so the
     * file and the counters can never disagree. Non-copyable. The constructor
     * creates ledgerPath's parent directory when missing and the file is
     * opened APPEND-only; each append is a single write of `<compact json>\n`
     * flushed per line. A write failure is logged at warn and NEVER thrown —
     * G5's fail-soft law — while the in-memory counters still advance.
     */
    class MetricsLedger {
    public:
        explicit MetricsLedger(const RouterConfig& config)
            : ledgerPath_(config.metrics.ledgerPath) {
            // Created here so the very first append cannot fail on a fresh
            // deployment. A failure is not yet a lost line: the append path
            // retries the open and warns per line it could not write.
            std::error_code ec;
            const std::filesystem::path parent =
                std::filesystem::path(ledgerPath_).parent_path();
            if (!parent.empty())
                std::filesystem::create_directories(parent, ec);

            out_.open(ledgerPath_, std::ios::binary | std::ios::app);
        }

        MetricsLedger(const MetricsLedger&) = delete;
        MetricsLedger& operator=(const MetricsLedger&) = delete;

        void record(const RequestRecord& entry) {
            // Read before the lock: under contention the wait would land in the
            // stamp, and the stamp is what every rate question divides by.
            const auto completedAt = std::chrono::system_clock::now();

            const std::lock_guard<std::mutex> lock(mutex_);
            accumulate(entry);
            appendLine(entry, completedAt);
        }

        // The union aggregate both /conductor/metrics and the fan-out side
        // read. The first six names are byte-identical to the COMMITTED
        // conductor/adapter/router-client.ts MetricsSummary, which casts the
        // parsed object without validating.
        [[nodiscard]] nlohmann::json summary() const {
            const std::lock_guard<std::mutex> lock(mutex_);

            nlohmann::json statusCounts = nlohmann::json::object();
            for (const auto& [status, count] : statusCounts_)
                statusCounts[std::to_string(status)] = count;

            nlohmann::json out;
            out["totalRequests"] = totalRequests_;
            out["schemaMissing"] = schemaMissingTrue_;
            out["schemaConformed"] = schemaConformedTrue_;
            out["statusCounts"] = std::move(statusCounts);
            out["promptTokens"] = promptTokensTotal_;
            out["completionTokens"] = completionTokensTotal_;
            out["waitMsP50"] = percentile(50);
            out["waitMsP95"] = percentile(95);
            if (schemaVerdicts_ == 0) {
                // Zero verdicts exist: null, which a 0 would misreport as
                // "nothing ever conformed".
                out["schemaConformanceRate"] = nullptr;
            }
            else {
                out["schemaConformanceRate"] = static_cast<double>(schemaConformedTrue_) /
                                               static_cast<double>(schemaVerdicts_);
            }

            return out;
        }

    private:
        // Counters advance whatever the file does (G5: a lost line must not
        // under-count the endpoint). Called under mutex_.
        void accumulate(const RequestRecord& entry) {
            ++totalRequests_;
            ++statusCounts_[entry.status];
            waits_.push_back(entry.queueWaitMs);

            if (entry.promptTokens)
                promptTokensTotal_ += *entry.promptTokens;

            if (entry.completionTokens)
                completionTokensTotal_ += *entry.completionTokens;

            if (entry.schemaMissing && *entry.schemaMissing)
                ++schemaMissingTrue_;

            if (entry.schemaConformed) {
                ++schemaVerdicts_;
                if (*entry.schemaConformed)
                    ++schemaConformedTrue_;
            }
        }

        // ONE write of `<compact json>\n`, flushed, under mutex_ — concurrent
        // completions can never tear or interleave a line. Every failure mode
        // becomes a warn naming the configured path, never a throw.
        void appendLine(const RequestRecord& entry,
                        std::chrono::system_clock::time_point completedAt) {
            std::string line;
            try {
                // The replace handler keeps a client-supplied byte sequence
                // that is not valid UTF-8 from failing the serialization —
                // the request it rode in on was still served (G5).
                line = toJson(entry, completedAt).dump(
                    -1, ' ', false, nlohmann::json::error_handler_t::replace);
            } catch (const std::exception& failure) {
                spdlog::warn(
                    "router: could not serialize a metrics ledger line for {}: {} — "
                    "the response was served anyway",
                    ledgerPath_, failure.what());

                return;
            }

            line.push_back('\n');

            if (!out_.is_open()) {
                out_.clear();
                out_.open(ledgerPath_, std::ios::binary | std::ios::app);
            }

            if (out_.is_open()) {
                out_.write(line.data(), static_cast<std::streamsize>(line.size()));
                out_.flush();
            }

            if (!out_.is_open() || out_.fail()) {
                spdlog::warn(
                    "router: could not append a metrics ledger line to {} — "
                    "the response was served anyway",
                    ledgerPath_);

                out_.clear();
                if (out_.is_open())
                    out_.close();
            }
        }

        // Every pinned key present on every line; absence is JSON null.
        //
        // completedAt is the instant the request FINISHED, which is when the
        // record guard fires. The interval it belongs to is recoverable from
        // the line itself: the request began completedAt - queueWaitMs -
        // upstreamMs. One field is therefore enough to answer every rate and
        // concurrency question the file previously could not.
        [[nodiscard]] static nlohmann::json toJson(
            const RequestRecord& entry, std::chrono::system_clock::time_point completedAt) {
            nlohmann::json line;
            line["completedAt"] = detail::formatLedgerTimestamp(completedAt);
            line["model"] = entry.model;
            line["role"] = entry.role ? nlohmann::json(*entry.role) : nlohmann::json();
            line["group"] = entry.group ? nlohmann::json(*entry.group) : nlohmann::json();
            line["priority"] = entry.priority;
            line["queueWaitMs"] = entry.queueWaitMs;
            line["upstreamMs"] =
                entry.upstreamMs ? nlohmann::json(*entry.upstreamMs) : nlohmann::json();
            line["promptTokens"] =
                entry.promptTokens ? nlohmann::json(*entry.promptTokens) : nlohmann::json();
            line["completionTokens"] = entry.completionTokens
                                         ? nlohmann::json(*entry.completionTokens)
                                         : nlohmann::json();
            line["timings"] = entry.timings;
            line["schemaMissing"] =
                entry.schemaMissing ? nlohmann::json(*entry.schemaMissing) : nlohmann::json();
            line["schemaConformed"] = entry.schemaConformed
                                        ? nlohmann::json(*entry.schemaConformed)
                                        : nlohmann::json();
            line["status"] = entry.status;
            return line;
        }

        // NEAREST-RANK over the sorted queueWaitMs samples: N > 0 sorted
        // ascending 1-indexed, rank ceil(percent/100 * N) in exact integer
        // arithmetic; 0 when N == 0. Called under mutex_.
        [[nodiscard]] std::int64_t percentile(std::size_t percent) const {
            if (waits_.empty())
                return 0;

            std::vector<std::int64_t> sorted = waits_;
            std::sort(sorted.begin(), sorted.end());

            const std::size_t rank = (percent * sorted.size() + 99) / 100;
            return sorted[rank == 0 ? 0 : rank - 1];
        }

        std::string ledgerPath_;

        mutable std::mutex mutex_;
        std::ofstream out_;

        std::uint64_t totalRequests_{ 0 };
        std::uint64_t schemaMissingTrue_{ 0 };
        std::uint64_t schemaConformedTrue_{ 0 };
        std::uint64_t schemaVerdicts_{ 0 };
        std::int64_t promptTokensTotal_{ 0 };
        std::int64_t completionTokensTotal_{ 0 };
        std::map<int, std::uint64_t> statusCounts_;
        std::vector<std::int64_t> waits_;
    };

}  // namespace conductor::router
