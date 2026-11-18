"""Expose terminal-independent casino rules for callers."""

from casino.game import (
    RoundOutcome,
    calculate_winnings,
    can_continue_with_balance,
    generate_secret_number,
    resolve_round,
)

__all__ = [
    "RoundOutcome",
    "calculate_winnings",
    "can_continue_with_balance",
    "generate_secret_number",
    "resolve_round",
]
