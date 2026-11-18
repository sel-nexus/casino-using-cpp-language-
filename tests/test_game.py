"""Verify settlement, minimum stakes, and production random boundaries."""

from dataclasses import FrozenInstanceError
import random

import pytest

from casino.game import (
    calculate_winnings, can_continue_with_balance, generate_secret_number,
    resolve_round,
)


@pytest.mark.parametrize("bet", [100, 500, 2147483647, 10**50])
def test_winnings_credit_ten_times_stake_without_overflow(bet: int) -> None:
    """Credit the full multiplier even beyond signed integer capacity."""
    assert calculate_winnings(bet) == bet * 10


@pytest.mark.parametrize("bet", [-1, 0, 99])
def test_winnings_reject_below_minimum_stakes(bet: int) -> None:
    """Reject a stake that cannot start a round."""
    with pytest.raises(ValueError, match="Minimum bet is 100"):
        calculate_winnings(bet)


@pytest.mark.parametrize("balance,expected", [(-1, False), (0, False), (99, False), (100, True), (101, True), (10**50, True)])
def test_continuation_requires_at_least_one_minimum_stake(balance: int, expected: bool) -> None:
    """Allow exactly the minimum and reject smaller balances."""
    assert can_continue_with_balance(balance) is expected


@pytest.mark.parametrize("balance,bet,number", [(500, 100, 7), (100, 100, 1), (2147483647, 2147483647, 10)])
def test_winning_round_preserves_stake_and_adds_full_credit(balance: int, bet: int, number: int) -> None:
    """Settle a win without first subtracting its stake."""
    outcome = resolve_round(balance, bet, number, number)
    assert outcome.won is True
    assert outcome.secret_number == number
    assert outcome.balance_change == bet * 10
    assert outcome.ending_balance == balance + bet * 10
    with pytest.raises(FrozenInstanceError):
        outcome.ending_balance = 0  # type: ignore[misc]


@pytest.mark.parametrize("balance,bet,ending", [(500, 100, 400), (100, 100, 0), (199, 100, 99), (200, 100, 100)])
def test_losing_round_deducts_only_the_stake(balance: int, bet: int, ending: int) -> None:
    """Settle losses including exhausted and threshold balances."""
    outcome = resolve_round(balance, bet, 1, 10)
    assert outcome.won is False
    assert outcome.secret_number == 10
    assert outcome.balance_change == -bet
    assert outcome.ending_balance == ending


@pytest.mark.parametrize("balance,bet,guess,secret,message", [
    (500, 501, 1, 1, "Money exceeds"),
    (500, 99, 1, 1, "Minimum bet"),
    (500, 100, 0, 1, "Number exceeds"),
    (500, 100, 11, 1, "Number exceeds"),
    (500, 100, 1, 0, "Number exceeds"),
    (500, 100, 1, 11, "Number exceeds"),
])
def test_round_rejects_invalid_stakes_and_numbers(balance: int, bet: int, guess: int, secret: int, message: str) -> None:
    """Reject each violated rule before settlement."""
    with pytest.raises(ValueError, match=message):
        resolve_round(balance, bet, guess, secret)


def test_seeded_random_source_is_repeatable_and_covers_endpoints() -> None:
    """Draw reproducibly within the full inclusive number range."""
    first = random.Random(42)
    second = random.Random(42)
    numbers = [generate_secret_number(first) for _ in range(100)]
    assert numbers == [generate_secret_number(second) for _ in range(100)]
    assert set(numbers) == set(range(1, 11))


def test_production_random_source_stays_in_range() -> None:
    """Exercise the default random source without requiring a specific draw."""
    assert all(1 <= generate_secret_number() <= 10 for _ in range(100))
