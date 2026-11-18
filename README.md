# Casino — Python Terminal Game

A complete Python migration of the original console casino number-guessing game. Requires Python 3.10+; runtime uses only the standard library. No frontend, API, database, or external service is needed.

## What the game does
- Prints the game rules.
- Prompts the player for a name and starting balance.
- Requires a minimum balance and minimum bet of 100.
- Lets the player guess a number from 1 to 10.
- Pays out 10x the bet on a correct guess.
- Ends when the player chooses to stop or the balance drops below 100.

## Run
From the repository root, use either equivalent entry point:

```bash
python3 main.py
python3 -m casino
```
On Windows, use `py -3` in place of `python3`. Enter your name, deposit, bet, guess, and then y/n to continue. EOF (Ctrl-D on Unix, Ctrl-Z then Enter on Windows) or Ctrl-C exits cleanly.

## Install and verify
No runtime package installation is necessary. For tests, create a virtual environment outside the checkout:

```bash
python3 -m venv --copies "$HOME/venvs/casino"
"$HOME/venvs/casino/bin/python" -m pip install -r requirements-dev.txt
"$HOME/venvs/casino/bin/python" -m pytest -q
"$HOME/venvs/casino/bin/python" -m compileall -q casino main.py
```
On Windows, create a venv under your home directory and use its `Scripts/python.exe`. `requirements.txt` records the dependency-free runtime; `requirements-dev.txt` pins pytest. Tests include rule/validation checks and real subprocess terminal journeys with timeouts.

## Compatibility and migration
- A winning round adds **10 × bet** to the existing balance, with no initial stake deduction: balance 500, bet 100, correct guess → 1500. A loss gives 400.
- Deposits and bets accept strict ASCII signed 32-bit integers, optional leading whitespace/sign, but no trailing whitespace or junk. Guess range is 1–10; continuation accepts only y/Y/n/N. Nonempty names retain spaces.
- Python balance arithmetic avoids the old C++ overflow; EOF no longer causes an endless prompt loop. These changes were approved with the migration scope.
- Random numbers remain uniform over 1–10; Python and C++ random sequences are not byte-for-byte identical.
- `casino/game.py` replaces core rules; `casino/cli.py` replaces input and session handling. `main.py` and `casino/__main__.py` are thin launch adapters. Python tests replace the C++ harness.
- `main (1).cpp` and `tests.cpp` have been retired from the current tree. The original source is available at Git revision `879d6ca51f7af7054c6c88e7ba226d442a90876f`, for example `git show '879d6ca:main (1).cpp'`.
- No saved data or configuration migration is required. No environment variables or secrets are used.

This is a toy guessing game, not a real-money gambling system.