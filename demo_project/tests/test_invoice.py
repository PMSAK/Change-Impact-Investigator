"""
Tests for invoice.py

These tests verify the invoice output structure and numeric accuracy.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.invoice import generate_invoice


def _make_order(
    subtotal=100.00,
    discount=0.00,
    taxable_amount=100.00,
    tax=8.00,
    items_total=108.00,
    shipping=5.00,
    order_total=113.00,
    customer_type="regular",
    items=None,
):
    if items is None:
        items = [{"name": "Widget", "price": 100.00, "quantity": 1}]
    return {
        "items": items,
        "customer_type": customer_type,
        "subtotal": subtotal,
        "discount": discount,
        "taxable_amount": taxable_amount,
        "tax": tax,
        "items_total": items_total,
        "shipping": shipping,
        "order_total": order_total,
    }


class TestGenerateInvoice:
    def test_returns_text_and_totals_keys(self):
        invoice = generate_invoice(_make_order())
        assert "text" in invoice
        assert "totals" in invoice

    def test_totals_match_order(self):
        order = _make_order(
            subtotal=65.00,
            discount=3.25,
            taxable_amount=61.75,
            tax=4.94,
            items_total=66.69,
            shipping=5.00,
            order_total=71.69,
        )
        totals = generate_invoice(order)["totals"]
        assert totals["subtotal"] == 65.00
        assert totals["discount"] == 3.25
        assert totals["tax"] == 4.94
        assert totals["shipping"] == 5.00
        assert totals["order_total"] == 71.69

    def test_invoice_text_contains_order_total(self):
        order = _make_order(order_total=113.00)
        text = generate_invoice(order)["text"]
        assert "113.00" in text

    def test_invoice_text_contains_customer_type(self):
        order = _make_order(customer_type="vip")
        text = generate_invoice(order)["text"]
        assert "vip" in text
