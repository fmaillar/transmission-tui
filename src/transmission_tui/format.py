"""Formatting helpers for the TUI."""

from __future__ import annotations


def human_bytes(value: int | float) -> str:
    """Format a byte count using decimal SI units."""
    value = float(value)
    units = ("B", "kB", "MB", "GB", "TB", "PB")
    for unit in units:
        if abs(value) < 1000.0 or unit == units[-1]:
            if unit == "B":
                return f"{value:.0f} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1000.0
    raise AssertionError("unreachable")


def human_rate(value: int | float) -> str:
    """Format a byte-per-second rate."""
    return f"{human_bytes(value)}/s"
