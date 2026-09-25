"""
Pricing module: calculates subtotals, tax, and totals for orders.
"""

TAX_RATE = 0.08  # 8% tax


def calculate_subtotal(items):
    """
    Sum the price * quantity for each item in the list.

    Each item is a dict with at least 'price' and 'quantity' keys.
    Returns a float representing the pre-tax total.
    """
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return round(total, 2)


def calculate_tax(amount):
    """
    Apply the standard tax rate to *amount* and return the tax portion.
    """
    return round(amount * TAX_RATE, 2)


def calculate_total(items):
    """
    Full pipeline: subtotal → tax → total.

    Returns a dict with keys:
        subtotal, tax, total
    """
    subtotal = calculate_subtotal(items)
    tax = calculate_tax(subtotal)
    total = round(subtotal + tax, 2)

    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
