"""
Invoice module: renders a human-readable invoice from a completed order.
"""


def generate_invoice(order):
    """
    Produce a formatted invoice string and a structured summary dict from the
    order dict returned by checkout.create_order.

    Returns a dict with keys:
        text   – the printable invoice string
        totals – a dict with subtotal, discount, tax, shipping, order_total
    """
    lines = []
    lines.append("=" * 44)
    lines.append("           ORDER INVOICE")
    lines.append("=" * 44)

    lines.append(f"Customer type : {order['customer_type']}")
    lines.append("")
    lines.append("Items:")
    for item in order["items"]:
        line_total = item["price"] * item["quantity"]
        lines.append(
            f"  {item['name']:<20} {item['quantity']:>2} x ${item['price']:>7.2f}"
            f"  = ${line_total:>8.2f}"
        )

    lines.append("-" * 44)
    lines.append(f"  Subtotal          : ${order['subtotal']:>8.2f}")
    lines.append(f"  Discount          : ${order['discount']:>8.2f}")
    lines.append(f"  Taxable amount    : ${order['taxable_amount']:>8.2f}")
    lines.append(f"  Tax (8%)          : ${order['tax']:>8.2f}")
    lines.append(f"  Items total       : ${order['items_total']:>8.2f}")
    lines.append(f"  Shipping          : ${order['shipping']:>8.2f}")
    lines.append("=" * 44)
    lines.append(f"  ORDER TOTAL       : ${order['order_total']:>8.2f}")
    lines.append("=" * 44)

    totals = {
        "subtotal": order["subtotal"],
        "discount": order["discount"],
        "tax": order["tax"],
        "shipping": order["shipping"],
        "order_total": order["order_total"],
    }

    return {
        "text": "\n".join(lines),
        "totals": totals,
    }
