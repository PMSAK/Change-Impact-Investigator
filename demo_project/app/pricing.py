"""
Pricing module: calculates subtotals, discounts, tax, and totals for orders.
"""

TAX_RATE = 0.08  # 8% tax

DISCOUNT_RATES = {
    "regular": 0.0,
    "member": 0.05,
    "vip": 0.10,
}


def calculate_subtotal(items):
    """
    Sum the price * quantity for each item in the list.

    Each item is a dict with at least 'price' and 'quantity' keys.
    Returns a float representing the pre-discount, pre-tax total.
    """
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return round(total, 2)


def calculate_discount(subtotal, customer_type):
    """
    Return the discount amount (not the reduced price) for the given subtotal
    and customer type.

    customer_type must be one of: 'regular', 'member', 'vip'.
    Unknown customer types receive no discount.
    """
    rate = DISCOUNT_RATES.get(customer_type, 0.0)
    return round(subtotal * rate, 2)


def calculate_tax(amount):
    """
    Apply the standard tax rate to *amount* and return the tax portion.
    """
    return round(amount * TAX_RATE, 2)


def calculate_total(items, customer_type):
    """
    Full pipeline: subtotal → discount → tax → total.

    Returns a dict with keys:
        subtotal, discount, taxable_amount, tax, total
    """
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal, customer_type)
    taxable_amount = round(subtotal - discount, 2)
    tax = calculate_tax(taxable_amount)
    total = round(taxable_amount + tax, 2)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "taxable_amount": taxable_amount,
        "tax": tax,
        "total": total,
    }
