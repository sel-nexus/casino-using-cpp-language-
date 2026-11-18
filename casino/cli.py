"""Run the baseline casino session with clean terminal termination."""

from collections.abc import Callable
import random
import re
import sys

from casino.game import can_continue_with_balance, generate_secret_number, resolve_round

RULES = (
    "-------------------------------------------------------\n"
    "Rules\n"
    "1) Enter a number between 1 to 10.\n"
    "2) If you win, you will get 10 times your bet.\n"
    "3) If you lose, you will lose your bet.\n"
    "4) Minimum bet is 100.\n"
    "5) The game continues until your balance drops below 100 or you choose to stop.\n"
    "-------------------------------------------------------\n"
)
INTEGER_PATTERN = re.compile(r"[ \t\n\r\v\f]*([+-]?)([0-9]+)", re.ASCII)


def parse_integer(raw_value: str) -> int | None:
    """Parse the strict ASCII signed-32-bit input accepted by the baseline.

    Args:
        raw_value: A line without its terminal newline.

    Returns:
        The integer, or None for malformed or out-of-range input. Leading
        ASCII whitespace and a sign are accepted; trailing whitespace is not.
    """
    match = INTEGER_PATTERN.fullmatch(raw_value)
    if match is None:
        return None
    sign, digits = match.groups()
    digits = digits.lstrip("0") or "0"
    limit = "2147483648" if sign == "-" else "2147483647"
    if len(digits) > len(limit) or (len(digits) == len(limit) and digits > limit):
        return None
    value = int(digits)
    return -value if sign == "-" else value


def write_stdout(text: str) -> None:
    """Write session text immediately, including prompts without newlines.

    Args:
        text: Exact terminal output to emit.
    """
    sys.stdout.write(text)
    sys.stdout.flush()


class Terminal:
    """Collect validated session input using injectable terminal boundaries."""

    def __init__(
        self, read: Callable[[], str], write: Callable[[str], None]
    ) -> None:
        """Bind input and output without owning external resources.

        Args:
            read: Read one line, raising EOFError or KeyboardInterrupt on exit.
            write: Emit text verbatim, without adding newlines.
        """
        self.read = read
        self.write = write

    def prompt(self, message: str) -> str:
        """Display a prompt and read its untrimmed response.

        Args:
            message: Prompt to display.

        Returns:
            The response with all name spaces preserved.

        Raises:
            EOFError: If the input stream closes.
            KeyboardInterrupt: If the user interrupts input.
        """
        self.write(message)
        return self.read()

    def integer(self, message: str) -> int:
        """Retry malformed integer input until a valid line is supplied.

        Args:
            message: Prompt to repeat for each attempt.

        Returns:
            A parsed signed-32-bit integer.

        Raises:
            EOFError: If input closes while prompting.
            KeyboardInterrupt: If prompting is interrupted.
        """
        while True:
            value = parse_integer(self.prompt(message))
            if value is not None:
                return value
            self.write("Please enter a valid whole number.\n")

    def deposit(self) -> int:
        """Request enough starting money for at least one round.

        Returns:
            A starting balance of at least 100.

        Raises:
            EOFError: If input closes.
            KeyboardInterrupt: If input is interrupted.
        """
        while True:
            value = self.integer("Enter the money to deposit for the game: ")
            if can_continue_with_balance(value):
                return value
            self.write("Minimum starting balance is 100.\n")

    def bet(self, balance: int, name: str) -> int:
        """Request an affordable stake, preserving validation precedence.

        Args:
            balance: Money available to wager.
            name: Untrimmed player name for the prompt.

        Returns:
            A stake from 100 through the available balance.

        Raises:
            EOFError: If input closes.
            KeyboardInterrupt: If input is interrupted.
        """
        while True:
            value = self.integer(f"{name}, enter the money to bet (minimum 100): ")
            if value > balance:
                self.write("Money exceeds your balance.\n")
            elif value < 100:
                self.write("Minimum bet is 100.\n")
            else:
                return value

    def guess(self) -> int:
        """Request a number within the inclusive guessing range.

        Returns:
            A guess from 1 through 10.

        Raises:
            EOFError: If input closes.
            KeyboardInterrupt: If input is interrupted.
        """
        while True:
            value = self.integer("Guess a number between 1 to 10: ")
            if 1 <= value <= 10:
                return value
            self.write("Number exceeds the range.\n")

    def continue_playing(self) -> bool:
        """Request a single ASCII y or n, accepting either letter case.

        Returns:
            Whether the player wants another round.

        Raises:
            EOFError: If input closes.
            KeyboardInterrupt: If input is interrupted.
        """
        while True:
            value = self.prompt("Do you want to continue? (y/n): ")
            if value in ("y", "Y"):
                return True
            if value in ("n", "N"):
                return False
            self.write("Please enter y or n.\n")


def play_game(terminal: Terminal, generator: random.Random | None = None) -> None:
    """Play repeated rounds with the exact baseline prompts and messages.

    Args:
        terminal: Input and output boundary for this session.
        generator: Optional source for reproducible secret numbers.

    Raises:
        EOFError: If the input stream closes at any prompt.
        KeyboardInterrupt: If the session is interrupted.
    """
    name = terminal.prompt("Enter your name: ")
    while not name:
        terminal.write("Name cannot be empty.\n")
        name = terminal.prompt("Enter your name: ")
    terminal.write("\n")
    balance = terminal.deposit()
    terminal.write(f"\nYour current balance is {balance}\n\n")
    while can_continue_with_balance(balance):
        bet = terminal.bet(balance, name)
        terminal.write("\n")
        secret = generate_secret_number(generator)
        guess = terminal.guess()
        terminal.write("\n")
        outcome = resolve_round(balance, bet, guess, secret)
        balance = outcome.ending_balance
        if outcome.won:
            terminal.write(
                f"You have won: {bet}\n\n"
                f"You have won {outcome.balance_change} as total.\n"
                f"Your new balance is: {balance}\n\n"
            )
        else:
            terminal.write(
                f"You have lost {bet}\n\n"
                f"The correct number was {secret}\n\n"
                f"Now you have {balance} as balance.\n\n"
            )
        if not can_continue_with_balance(balance):
            terminal.write(
                "Your balance is less than 100. You can't continue playing. Have a nice day.\n"
            )
            break
        if not terminal.continue_playing():
            terminal.write("Have a nice day.\n")
            break
        terminal.write("\n")


def main(
    read: Callable[[], str] | None = None,
    write: Callable[[str], None] | None = None,
    generator: random.Random | None = None,
) -> int:
    """Run one session and turn EOF or interruption into a friendly exit.

    Args:
        read: Optional replacement for line-based terminal input.
        write: Optional replacement for immediate terminal output.
        generator: Optional random source for deterministic unit sessions.

    Returns:
        Zero after normal completion, EOF, or user interruption.
    """
    terminal = Terminal(
        read if read is not None else input,
        write if write is not None else write_stdout,
    )
    try:
        terminal.write(RULES + "\n\n")
        play_game(terminal, generator)
    except EOFError:
        terminal.write("\nInput ended. Have a nice day.\n")
    except KeyboardInterrupt:
        terminal.write("\nGame interrupted. Have a nice day.\n")
    return 0
