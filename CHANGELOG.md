# Changelog

## Python migration

### Added and changed
- Converted the entire application to Python 3.10+ with no runtime dependencies, frontend, API, or database.
- Added `casino/game.py` for settlement and random rules, `casino/cli.py` for validated terminal interaction, and package/entry adapters (`casino/__init__.py`, `casino/__main__.py`, `main.py`).
- Added pytest rule, CLI, terminal-subprocess, and migration tests under `tests/`, plus `pytest.ini`, `requirements.txt`, and pinned `requirements-dev.txt`.
- Updated README with launch, installation, compatibility and verification instructions. Updated `.gitignore` for Python caches and pipeline artifacts; refreshed the code graph.
- Preserved prompts, thresholds, random range and payout semantics: wins add 10× the bet to the balance; losses subtract the bet.

### Approved behavior fixes
- EOF and Ctrl-C now end the game cleanly; the previous EOF prompt loop was confirmed with a subprocess timeout.
- Python arbitrary-precision balance arithmetic avoids undefined C++ integer overflow. Terminal numeric input retains the strict signed-32-bit baseline syntax.

### Breaking changes and migration notes
- Retired `main (1).cpp` and `tests.cpp` from the current tree after Python verification. Source remains in Git history at `879d6ca51f7af7054c6c88e7ba226d442a90876f`.
- Replace C++ compilation / `./casino_app` with `python3 main.py` or `python3 -m casino`; no C++ compiler is required.
- No data or configuration migration; no environment variables. Random range is equivalent, not the C++ PRNG sequence.
- Owner approved the scope, retirement and behavior fixes before implementation. Historical release notes below describe the earlier C++ revision only.

## test 43

### Changed
- Refactored `main (1).cpp` from one monolithic gameplay routine into smaller helper functions for parsing input, validating bets, generating the secret number, and resolving round outcomes.
- Replaced per-turn `srand(time(0))` seeding with a single `std::mt19937` generator seeded once at runtime.
- Added stricter validation for empty player names, invalid numeric input, out-of-range guesses, under-minimum deposits, under-minimum bets, and invalid continue decisions.

### Added
- `tests.cpp` automated test harness covering winnings, win/loss balance updates, minimum-balance continuation rules, integer parsing, and random-number range guarantees.
- `README.md` with build, run, and test instructions.

### Verification
- Compiled the application with `g++ -std=c++17 "main (1).cpp" -o casino_app`.
- Compiled and ran tests with `g++ -std=c++17 tests.cpp -o casino_tests` and `./casino_tests`.
- Performed a scripted smoke run of the interactive game flow.

### Notes
- The discovery PRD available in the task workspace describes an unrelated HireHub React application. This run used the actual checked-out repository as the source of truth and applied brownfield improvements to the existing C++ console game instead.
- No breaking interface changes were introduced beyond stronger input validation and internal refactoring.
