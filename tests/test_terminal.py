"""Specify real subprocess journeys; execute only after test-critic approval."""

from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = [("main.py",), ("-m", "casino")]


def run_terminal(adapter: tuple[str, ...], lines: list[str]) -> str:
    """Launch an unmodified application and close stdin after the responses.

    Args:
        adapter: Script or module launch arguments.
        lines: Real stdin lines supplied to the session.

    Returns:
        Captured stdout after a successful, bounded, stderr-free exit.
    """
    result = subprocess.run(
        [sys.executable, *adapter], cwd=ROOT,
        input="".join(line + "\n" for line in lines),
        capture_output=True, text=True, encoding="utf-8", timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Traceback" not in result.stdout
    return result.stdout


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_real_session_validates_input_and_settles_multiple_random_rounds(adapter: tuple[str, ...]) -> None:
    """Verify actual random outcomes and carried balances through both adapters."""
    output = run_terminal(adapter, [
        "", "Ada Lovelace", "bad", "99", "500", "bad", "501", "99", "100",
        "bad", "0", "11", "1", "yes", "Y", "100", "10", "n",
    ])
    assert "Rules\n1) Enter a number between 1 to 10.\n" in output
    assert "Name cannot be empty.\n" in output
    assert output.count("Please enter a valid whole number.\n") == 3
    assert "Minimum starting balance is 100.\n" in output
    assert "Money exceeds your balance.\n" in output
    assert output.count("(minimum 100): Minimum bet is 100.\n") == 1
    assert output.count("Number exceeds the range.\n") == 2
    assert "Please enter y or n.\n" in output
    assert "Your current balance is 500\n\n" in output
    rounds = list(re.finditer(
        r"You have won: (\d+)\n\nYou have won (\d+) as total\.\nYour new balance is: (\d+)\n\n"
        r"|You have lost (\d+)\n\nThe correct number was (\d+)\n\nNow you have (\d+) as balance\.\n\n",
        output,
    ))
    assert len(rounds) == 2
    balance = 500
    for match, guess in zip(rounds, [1, 10]):
        win_bet, winnings, win_balance, loss_bet, secret, loss_balance = match.groups()
        if win_bet is not None:
            assert int(win_bet) == 100
            assert int(winnings) == 1000
            balance += 1000
            assert int(win_balance) == balance
        else:
            assert int(loss_bet) == 100
            assert 1 <= int(secret) <= 10
            assert int(secret) != guess
            balance -= 100
            assert int(loss_balance) == balance
    assert output.count("Do you want to continue? (y/n): ") == 3
    assert output.endswith("Do you want to continue? (y/n): Have a nice day.\n")
    assert "Input ended" not in output


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("lines,prompt", [
    ([], "Enter your name: "),
    ([""], "Enter your name: "),
    (["Ada"], "Enter the money to deposit for the game: "),
    (["Ada", "bad"], "Enter the money to deposit for the game: "),
    (["Ada", "99"], "Enter the money to deposit for the game: "),
    (["Ada", "500"], "Ada, enter the money to bet (minimum 100): "),
    (["Ada", "500", "bad"], "Ada, enter the money to bet (minimum 100): "),
    (["Ada", "500", "501"], "Ada, enter the money to bet (minimum 100): "),
    (["Ada", "500", "99"], "Ada, enter the money to bet (minimum 100): "),
    (["Ada", "500", "100"], "Guess a number between 1 to 10: "),
    (["Ada", "500", "100", "bad"], "Guess a number between 1 to 10: "),
    (["Ada", "500", "100", "11"], "Guess a number between 1 to 10: "),
    (["Ada", "500", "100", "1"], "Do you want to continue? (y/n): "),
    (["Ada", "500", "100", "1", "yes"], "Do you want to continue? (y/n): "),
    (["Ada", "500", "100", "1", "y"], "Ada, enter the money to bet (minimum 100): "),
])
def test_real_eof_terminates_at_each_session_stage(adapter: tuple[str, ...], lines: list[str], prompt: str) -> None:
    """Close real stdin at each stage and reject looping or tracebacks."""
    output = run_terminal(adapter, lines)
    assert output.endswith(prompt + "\nInput ended. Have a nice day.\n")
