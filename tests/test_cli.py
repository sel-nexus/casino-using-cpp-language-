"""Lock down exact terminal text, input validation, and clean exit branches."""

import random

import pytest

from casino.cli import main, parse_integer, write_stdout

EXPECTED_RULES = (
    "-------------------------------------------------------\nRules\n"
    "1) Enter a number between 1 to 10.\n"
    "2) If you win, you will get 10 times your bet.\n"
    "3) If you lose, you will lose your bet.\n"
    "4) Minimum bet is 100.\n"
    "5) The game continues until your balance drops below 100 or you choose to stop.\n"
    "-------------------------------------------------------\n\n\n"
)


def session(lines: list[str], seed: int = 42, end: type[EOFError] | type[KeyboardInterrupt] = EOFError) -> str:
    """Run a real session with deterministic input and random draws.

    Args:
        lines: Responses consumed in prompt order.
        seed: Random seed for reproducible unit rounds.
        end: Exception raised once supplied responses are exhausted.

    Returns:
        The complete output of a successfully terminated session.
    """
    responses = iter(lines)
    output: list[str] = []

    def read() -> str:
        """Read the next response or simulate terminal termination."""
        try:
            return next(responses)
        except StopIteration:
            raise end() from None

    assert main(read, output.append, random.Random(seed)) == 0
    return "".join(output)


@pytest.mark.parametrize("raw,expected", [
    ("250", 250), (" +100", 100), ("\t\r\v\f-10", -10),
    ("-2147483648", -2147483648), ("2147483647", 2147483647),
    ("-0", 0), ("0" * 5000 + "100", 100),
])
def test_integer_parser_accepts_only_valid_ascii_signed32_forms(raw: str, expected: int) -> None:
    """Accept baseline signs, leading whitespace, zeros, and boundaries."""
    assert parse_integer(raw) == expected


@pytest.mark.parametrize("raw", [
    "", " ", "+", "-", "25x", "100 ", "100\t", "100\n", "1.0", "1_000",
    "0x10", "1 0", "++1", "+ 1", "١٠٠", "１００", "\u00a0100",
    "2147483648", "-2147483649", "9" * 5000,
])
def test_integer_parser_rejects_malformed_unicode_and_overflow_lines(raw: str) -> None:
    """Reject trailing input, non-ASCII digits, and signed32 overflow."""
    assert parse_integer(raw) is None


def test_full_win_session_matches_baseline_exactly() -> None:
    """Preserve every prompt, blank line, and winning payout message."""
    assert session(["Ada Lovelace", "500", "100", "2", "n"]) == (
        EXPECTED_RULES + "Enter your name: \n"
        "Enter the money to deposit for the game: \nYour current balance is 500\n\n"
        "Ada Lovelace, enter the money to bet (minimum 100): \n"
        "Guess a number between 1 to 10: \n"
        "You have won: 100\n\nYou have won 1000 as total.\n"
        "Your new balance is: 1500\n\n"
        "Do you want to continue? (y/n): Have a nice day.\n"
    )


def test_full_loss_session_matches_baseline_exactly() -> None:
    """Reveal the actual secret and deduct the losing stake."""
    assert session(["Ada", "500", "100", "3", "N"]) == (
        EXPECTED_RULES + "Enter your name: \n"
        "Enter the money to deposit for the game: \nYour current balance is 500\n\n"
        "Ada, enter the money to bet (minimum 100): \n"
        "Guess a number between 1 to 10: \n"
        "You have lost 100\n\nThe correct number was 2\n\n"
        "Now you have 400 as balance.\n\n"
        "Do you want to continue? (y/n): Have a nice day.\n"
    )


def test_session_retries_every_validation_branch_and_preserves_name_spaces() -> None:
    """Retry empty names, syntax, limits, and invalid continuation responses."""
    output = session([
        "", "  Ada Lovelace  ", "bad", "99", " +500", "bad", "501", "99", "100",
        "bad", "0", "11", "2", "", "yes", " y", "n ", "x", "N",
    ])
    assert output.count("Name cannot be empty.\n") == 1
    assert output.count("Please enter a valid whole number.\n") == 3
    assert output.count("Minimum starting balance is 100.\n") == 1
    assert output.count("Money exceeds your balance.\n") == 1
    assert output.count("(minimum 100): Minimum bet is 100.\n") == 1
    assert output.count("Number exceeds the range.\n") == 2
    assert output.count("Please enter y or n.\n") == 5
    assert output.count("  Ada Lovelace  , enter the money to bet (minimum 100): ") == 4
    assert "Your new balance is: 1500\n\n" in output
    assert output.endswith("Have a nice day.\n")


def test_whitespace_only_name_is_nonempty_and_accepted() -> None:
    """Keep the baseline's nonempty rather than nonblank name rule."""
    output = session([" ", "100", "100", "1"])
    assert "Name cannot be empty" not in output
    assert " , enter the money to bet" in output
    assert "Now you have 0 as balance." in output


def test_multiple_rounds_use_updated_balance_and_case_insensitive_yes() -> None:
    """Carry a loss at the threshold into a win and then another loss."""
    output = session(["Ada", "200", "100", "3", "Y", "101", "100", "1", "y", "1100", "3"])
    assert "Now you have 100 as balance." in output
    assert "Money exceeds your balance." in output
    assert "Your new balance is: 1100" in output
    assert "Now you have 0 as balance." in output
    assert output.count("Do you want to continue? (y/n): ") == 2
    assert output.endswith("Your balance is less than 100. You can't continue playing. Have a nice day.\n")


@pytest.mark.parametrize("deposit,ending", [(100, 0), (199, 99)])
def test_low_balance_stops_without_continuation_prompt(deposit: int, ending: int) -> None:
    """Stop immediately when a loss leaves less than the minimum."""
    output = session(["Ada", str(deposit), "100", "1"])
    assert f"Now you have {ending} as balance." in output
    assert "Do you want to continue?" not in output
    assert output.endswith("Your balance is less than 100. You can't continue playing. Have a nice day.\n")


def test_maximum_input_win_uses_arbitrary_precision_balance() -> None:
    """Avoid fixed-width overflow when a maximum signed32 stake wins."""
    output = session(["Ada", "2147483647", "2147483647", "2", "n"])
    assert "You have won 21474836470 as total." in output
    assert "Your new balance is: 23622320117" in output


@pytest.mark.parametrize("end,exit_text", [(EOFError, "Input ended"), (KeyboardInterrupt, "Game interrupted")])
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
    (["Ada", "500", "100", "2"], "Do you want to continue? (y/n): "),
    (["Ada", "500", "100", "2", "yes"], "Do you want to continue? (y/n): "),
    (["Ada", "500", "100", "2", "y"], "Ada, enter the money to bet (minimum 100): "),
])
def test_eof_and_interruption_exit_cleanly_at_every_prompt(lines: list[str], prompt: str, end: type[EOFError] | type[KeyboardInterrupt], exit_text: str) -> None:
    """Terminate both initial and retry prompts instead of looping."""
    output = session(lines, end=end)
    assert output.endswith(prompt + f"\n{exit_text}. Have a nice day.\n")
    assert "Traceback" not in output


def test_unexpected_input_failure_is_not_silently_swallowed() -> None:
    """Allow programming or I/O failures other than friendly exits to surface."""
    def fail() -> str:
        """Simulate an unexpected input failure."""
        raise OSError("input failed")

    with pytest.raises(OSError, match="input failed"):
        main(fail, lambda text: None)


def test_default_stdout_writer_emits_without_extra_newline(capsys: pytest.CaptureFixture[str]) -> None:
    """Flush the exact supplied text to the production output boundary."""
    write_stdout("prompt: ")
    captured = capsys.readouterr()
    assert captured.out == "prompt: "
    assert captured.err == ""


def test_default_input_boundary_handles_eof(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Resolve the production input function at launch and catch EOF."""
    def eof() -> str:
        """Simulate a closed production input stream."""
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == EXPECTED_RULES + "Enter your name: \nInput ended. Have a nice day.\n"
    assert captured.err == ""
