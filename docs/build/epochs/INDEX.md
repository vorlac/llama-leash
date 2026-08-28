# Epoch index — the same prompts, vanilla against llama-leash

One directory per epoch, newest last. Each holds `REVIEW.md`: the prompt as it
was fed that epoch, the changes committed since the previous one, and then per
arm the produced code, the cost by phase, every sub-agent's dispatch prompt, and
the full transcript.

- **`baseline`** — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied
- **`doctrine`** — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions
- **`conductor`** — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

## Epochs

| # | epoch | started | cells | review |
|---:|---|---|---:|---|
| 1 | `20260822-024521` | 2026-08-22 02:45 | 4 | [REVIEW](01-20260822-024521/REVIEW.md) |
| 2 | `20260822-044746` | 2026-08-22 04:47 | 2 | [REVIEW](02-20260822-044746/REVIEW.md) |
| 3 | `20260822-052306` | 2026-08-22 05:23 | 5 | [REVIEW](03-20260822-052306/REVIEW.md) |
| 4 | `20260822-062146` | 2026-08-22 06:21 | 10 | [REVIEW](04-20260822-062146/REVIEW.md) |
| 5 | `20260822-154753` | 2026-08-22 15:47 | 2 | [REVIEW](05-20260822-154753/REVIEW.md) |
| 6 | `20260822-160012` | 2026-08-22 16:00 | 12 | [REVIEW](06-20260822-160012/REVIEW.md) |
| 7 | `20260822-204552` | 2026-08-22 20:45 | 12 | [REVIEW](07-20260822-204552/REVIEW.md) |
| 8 | `20260823-012116` | 2026-08-23 01:21 | 3 | [REVIEW](08-20260823-012116/REVIEW.md) |
| 9 | `20260823-110952` | 2026-08-23 11:09 | 5 | [REVIEW](09-20260823-110952/REVIEW.md) |
| 10 | `20260823-121514` | 2026-08-23 12:15 | 12 | [REVIEW](10-20260823-121514/REVIEW.md) |
| 11 | `20260823-164300` | 2026-08-23 16:43 | 12 | [REVIEW](11-20260823-164300/REVIEW.md) |
| 12 | `20260824-175241` | 2026-08-24 17:52 | 12 | [REVIEW](12-20260824-175241/REVIEW.md) |
| 13 | `20260824-225834` | 2026-08-24 22:58 | 12 | [REVIEW](13-20260824-225834/REVIEW.md) |
| 14 | `20260825-172722` | 2026-08-25 17:27 | 20 | [REVIEW](14-20260825-172722/REVIEW.md) |
| 15 | `step1-euler001` | 2026-08-26 19:49 | 5 | [REVIEW](15-step1-euler001/REVIEW.md) |
| 16 | `step2-euler001-postfix` | 2026-08-26 21:08 | 3 | [REVIEW](16-step2-euler001-postfix/REVIEW.md) |
| 17 | `step3-euler001-d45` | 2026-08-26 22:38 | 3 | [REVIEW](17-step3-euler001-d45/REVIEW.md) |
| 18 | `step4-grid2048` | 2026-08-27 00:37 | 3 | [REVIEW](18-step4-grid2048/REVIEW.md) |
| 19 | `step5-grid2048-nodeadline` | 2026-08-27 00:37 | 3 | [REVIEW](19-step5-grid2048-nodeadline/REVIEW.md) |
| 20 | `step6-grid2048-8h` | 2026-08-27 00:37 | 3 | [REVIEW](20-step6-grid2048-8h/REVIEW.md) |
| 21 | `step7-plan-terminates` | 2026-08-27 00:37 | 2 | [REVIEW](21-step7-plan-terminates/REVIEW.md) |
| 22 | `step8-context-128k` | 2026-08-28 01:44 | 2 | [REVIEW](22-step8-context-128k/REVIEW.md) |

## What changed across epochs

One row per task and arm. `–` is an epoch that did not run that cell, which
is not the same fact as a failure and does not share its word.

| task | arm | `20260822-024521` | `20260822-044746` | `20260822-052306` | `20260822-062146` | `20260822-154753` | `20260822-160012` | `20260822-204552` | `20260823-012116` | `20260823-110952` | `20260823-121514` | `20260823-164300` | `20260824-175241` | `20260824-225834` | `20260825-172722` | `step1-euler001` | `step2-euler001-postfix` | `step3-euler001-d45` | `step4-grid2048` | `step5-grid2048-nodeadline` | `step6-grid2048-8h` | `step7-plan-terminates` | `step8-context-128k` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `clock-inject-py` | `baseline` | – | – | – | FAIL 34.9m 0t | – | PASS 4.9m 3126t | PASS 5.2m 3810t | – | – | PASS 5.7m 4416t | PASS 4.7m 3593t | PASS 3.3m 2308t | PASS 3.9m 2751t | PASS x3 3.4–4.9m 3079–4521t | – | – | – | – | – | – | – | – |
| `clock-inject-py` | `conductor` | – | – | – | – | – | TIMEOUT 60.0m 42660t | TIMEOUT 60.0m 37806t | – | – | FAIL 33.8m 27511t | TIMEOUT 60.0m 42111t | TIMEOUT 60.0m 24821t | TIMEOUT 60.0m 36312t | TIMEOUT 60.0m 41691t | – | – | – | – | – | – | – | – |
| `clock-inject-py` | `doctrine` | – | – | – | – | – | PASS 9.2m 5742t | PASS 9.1m 7672t | – | – | PASS 11.8m 8667t | PASS 19.0m 14848t | PASS 12.4m 9944t | PASS 9.0m 6308t | PASS 11.6m 8446t | – | – | – | – | – | – | – | – |
| `euler-001-py` | `baseline` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | PASS x3 3.0–4.9m 1718–3335t | PASS 5.0m 3655t | PASS 3.3m 2133t | – | – | – | – | – |
| `euler-001-py` | `conductor` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | TIMEOUT 45.0m 27636t | TIMEOUT 45.0m 24090t | TIMEOUT 45.0m 17476t | – | – | – | – | – |
| `euler-001-py` | `doctrine` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | PASS 9.4m 5939t | PASS 11.6m 7439t | FAIL 3.1m 499t | – | – | – | – | – |
| `euler-cli-py` | `baseline` | – | – | PASS 4.4m 3250t | FAIL 8.2m 3019t | – | PASS 6.0m 4365t | PASS 7.0m 5964t | – | PASS 4.5m 3890t | PASS 4.9m 3494t | PASS 8.7m 6866t | PASS 7.8m 6286t | PASS 5.9m 4632t | PASS/FAIL x3 4.0–4.6m 2875–3770t | – | – | – | – | – | – | – | – |
| `euler-cli-py` | `conductor` | – | – | – | TIMEOUT 45.0m 18898t | – | TIMEOUT 45.0m 19193t | TIMEOUT 45.0m 20044t | – | – | TIMEOUT 45.0m 21133t | TIMEOUT 45.0m 26790t | TIMEOUT 45.0m 19569t | TIMEOUT 45.0m 18346t | TIMEOUT 45.0m 12559t | – | – | – | – | – | – | – | – |
| `euler-cli-py` | `doctrine` | – | – | FAIL 2.8m 870t | PASS 17.5m 14139t | – | PASS 11.1m 7418t | PASS 17.7m 13621t | – | PASS 12.2m 8896t | PASS 12.5m 9230t | PASS 11.5m 8333t | PASS 13.6m 9817t | PASS 18.9m 13859t | PASS 19.4m 14700t | – | – | – | – | – | – | – | – |
| `grid2048-headless-py` | `baseline` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | PASS 40.5m 27997t | PASS 40.5m 27997t | PASS 40.5m 27997t | PASS 40.5m 27997t | PASS 20.2m 16685t |
| `grid2048-headless-py` | `conductor` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | TIMEOUT 60.0m 16720t | TIMEOUT 60.0m 30634t | TIMEOUT 480.0m 307031t | – | – |
| `grid2048-headless-py` | `doctrine` | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | PASS 40.4m 27604t | PASS 40.4m 27604t | PASS 40.4m 27604t | PASS 40.4m 27604t | PASS 30.6m 21833t |
| `logfmt-lenses-ts` | `baseline` | – | – | – | PASS 5.3m 3945t | – | PASS 5.0m 3534t | PASS 4.6m 3423t | – | – | PASS 4.7m 3490t | PASS 5.3m 3999t | PASS 4.6m 3272t | PASS 4.7m 3485t | PASS x3 3.0–3.9m 2674–2978t | – | – | – | – | – | – | – | – |
| `logfmt-lenses-ts` | `conductor` | – | – | – | FAIL 86.8m 10221t | – | TIMEOUT 60.0m 27924t | TIMEOUT 60.0m 22659t | – | – | TIMEOUT 60.0m 15915t | TIMEOUT 60.0m 35006t | TIMEOUT 60.0m 12120t | TIMEOUT 60.0m 21410t | FAIL 52.3m 38619t | – | – | – | – | – | – | – | – |
| `logfmt-lenses-ts` | `doctrine` | – | – | – | PASS 22.3m 15800t | – | PASS 17.3m 12563t | PASS 13.6m 10098t | – | – | PASS 11.0m 7524t | PASS 22.3m 17355t | PASS 15.5m 11492t | PASS 13.7m 10410t | PASS 25.2m 18402t | – | – | – | – | – | – | – | – |
| `retry-ts` | `baseline` | PASS 5.1m 3439t | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| `slugify-ts` | `baseline` | PASS 7.0m 5535t | PASS 7.3m 4279t | PASS 3.8m 2044t | PASS 5.3m 1552t | PASS 3.9m 1570t | PASS 2.0m 1522t | PASS 2.5m 1839t | PASS 2.3m 1690t | PASS 3.1m 1637t | PASS 1.7m 1073t | PASS 2.1m 1519t | PASS 7.8m 7286t | PASS 1.7m 1044t | PASS x3 1.7–3.6m 1574–2029t | – | – | – | – | – | – | – | – |
| `slugify-ts` | `conductor` | FAIL 30.0m 14998t | – | TIMEOUT 30.0m 15493t | TIMEOUT 30.0m 12369t | – | TIMEOUT 30.0m 15391t | TIMEOUT 30.0m 16475t | TIMEOUT 30.0m 10765t | TIMEOUT 30.0m 13233t | TIMEOUT 30.0m 21394t | TIMEOUT 30.0m 17499t | TIMEOUT 30.0m 11784t | TIMEOUT 30.0m 11266t | TIMEOUT 30.0m 15020t | – | – | – | – | – | – | – | – |
| `slugify-ts` | `doctrine` | FAIL 30.0m 21385t | PASS 18.8m 12859t | PASS 10.4m 7198t | PASS 21.0m 15437t | FAIL 3.2m 2787t | PASS 11.0m 7523t | PASS 17.1m 13185t | PASS 8.5m 5764t | PASS 11.8m 8938t | PASS 5.9m 3581t | PASS 10.0m 7260t | TIMEOUT 30.0m 22628t | PASS 22.9m 17707t | PASS 12.2m 9035t | – | – | – | – | – | – | – | – |

