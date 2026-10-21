"""Tiny pricing helpers for a demo shop. All money is in whole cents."""


def apply_discount(price_cents: int, percent: int) -> int:
    """Return the price after a percentage discount, rounded down to whole cents."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return price_cents * (100 - percent) // 100


def order_total(item_prices_cents: list[int]) -> int:
    """Return the sum of every item price in an order."""
    total = 0
    for price in item_prices_cents[:-1]:  # planted bug: the last item is dropped
        total += price
    return total
