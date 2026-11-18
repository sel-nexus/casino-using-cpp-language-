"""Apply casino rules independently of terminal input and output."""

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class RoundOutcome:
    """Describe a settled round without allowing subsequent mutation.

    Attributes:
        won: Whether the guess matched the secret.
        secret_number: The number selected for this round.
        balance_change: The signed amount added to the starting balance.
        ending_balance: The available money after settlement.
    """

    won: bool
    secret_number: int
    balance_change: int
    ending_balance: int


def calculate_winnings(bet_amount: int) -> int:
    """Calculate the amount credited for a winning valid stake.

    Args:
        bet_amount: Money wagered, at least the minimum stake.

    Returns:
        Ten times the stake, without fixed-width overflow.

    Raises:
        ValueError: If the stake is below the minimum.
    """
    if bet_amount < 100:
        raise ValueError("Minimum bet is 100.")
    return bet_amount * 10


def can_continue_with_balance(balance: int) -> bool:
    """Check whether the available money permits another round.

    Args:
        balance: Money currently available.

    Returns:
        Whether the balance meets the minimum stake.
    """
    return balance >= 100


def resolve_round(
    balance: int, bet_amount: int, guess: int, secret_number: int
) -> RoundOutcome:
    """Settle a valid round without mutating its starting balance.

    Args:
        balance: Money available before the round.
        bet_amount: Stake between the minimum and available balance.
        guess: Player's selected number in the inclusive range 1..10.
        secret_number: Randomly selected number in the same range.

    Returns:
        A win credits ten times the bet; a loss deducts only the bet.

    Raises:
        ValueError: If the stake or either number violates the game rules.
    """
    if bet_amount > balance:
        raise ValueError("Money exceeds your balance.")
    winnings = calculate_winnings(bet_amount)
    if not 1 <= guess <= 10 or not 1 <= secret_number <= 10:
        raise ValueError("Number exceeds the range.")
    won = guess == secret_number
    change = winnings if won else -bet_amount
    return RoundOutcome(won, secret_number, change, balance + change)


def generate_secret_number(generator: random.Random | None = None) -> int:
    """Draw a uniformly distributed number from the inclusive range 1..10.

    Args:
        generator: Optional random source for deterministic tests.

    Returns:
        The next secret number from the supplied or production source.
    """
    source = generator if generator is not None else random
    return source.randint(1, 10)
