"""
Tests for pricing.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pricing import calculate_subtotal, calculate_tax, calculate_total


class TestSubtotal:
    def test_single_item(self):
        items = [{"name": "Widget", "price": 10.00, "quantity": 3}]
        assert calculate_subtotal(items) == 30.00

    def test_multiple_items(self):
        items = [
            {"name": "Widget", "price": 10.00, "quantity": 2},
            {"name": "Gadget", "price": 24.99, "quantity": 1},
        ]
        assert calculate_subtotal(items) == 44.99

    def test_empty_cart(self):
        assert calculate_subtotal([]) == 0.0

    def test_fractional_prices(self):
        items = [{"name": "Bolt", "price": 1.49, "quantity": 4}]
        assert calculate_subtotal(items) == 5.96


class TestTax:
    def test_tax_on_round_amount(self):
        assert calculate_tax(100.00) == 8.00

    def test_tax_rounded_to_cents(self):
        assert calculate_tax(49.99) == 4.00

    def test_zero_amount(self):
        assert calculate_tax(0.00) == 0.00


class TestCalculateTotal:
    def test_full_pipeline(self):
        items = [{"name": "Widget", "price": 20.00, "quantity": 5}]
        result = calculate_total(items)
        assert result["subtotal"] == 100.00
        assert result["tax"] == 8.00
        assert result["total"] == 108.00

    def test_result_keys_present(self):
        items = [{"name": "Thing", "price": 10.00, "quantity": 1}]
        result = calculate_total(items)
        assert set(result.keys()) == {"subtotal", "tax", "total"}
