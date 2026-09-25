"""
Shipping module: calculates shipping costs based on weight and destination.
"""

# Base rates per kg by destination zone
ZONE_RATES = {
    "domestic": 2.50,
    "international": 7.00,
}

# Minimum shipping charge
MIN_SHIPPING = 5.00


def calculate_shipping(weight, destination):
    """
    Calculate the base shipping cost for a given weight (kg) and destination.

    destination must be one of: 'domestic', 'international'.
    Raises ValueError for unknown destinations.
    """
    if destination not in ZONE_RATES:
        raise ValueError(f"Unknown destination zone: {destination!r}")
    rate = ZONE_RATES[destination]
    cost = weight * rate
    return round(max(cost, MIN_SHIPPING), 2)


def calculate_shipping_with_discount(weight, destination, discount):
    """
    Apply a flat discount amount to the shipping cost.

    discount is a non-negative float (e.g. 2.00 reduces cost by $2).
    The result will never be negative.
    """
    base = calculate_shipping(weight, destination)
    discounted = max(base - discount, 0.0)
    return round(discounted, 2)
