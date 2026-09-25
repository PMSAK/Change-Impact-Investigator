"""
Checkout module: assembles an order from items, pricing, and shipping.
"""

from app.pricing import calculate_total
from app.shipping import calculate_shipping


def create_order(items, customer_type, weight, destination):
    """
    Build an order summary dict from the provided cart items, customer type,
    package weight and shipping destination.

    Calls:
        pricing.calculate_total   – for subtotal, discount, tax, and total
        shipping.calculate_shipping – for the base shipping cost

    Returns a dict with keys:
        items, customer_type, subtotal, discount, taxable_amount,
        tax, items_total, shipping, order_total
    """
    pricing = calculate_total(items, customer_type)
    shipping_cost = calculate_shipping(weight, destination)

    order = {
        "items": items,
        "customer_type": customer_type,
        "subtotal": pricing["subtotal"],
        "discount": pricing["discount"],
        "taxable_amount": pricing["taxable_amount"],
        "tax": pricing["tax"],
        "items_total": pricing["total"],
        "shipping": shipping_cost,
        "order_total": round(pricing["total"] + shipping_cost, 2),
    }
    return order
