#!/bin/sh
set -e
c++ -std=c++23 -O2 -Wall -Wextra -I. src/main.cpp -o snake
