"""
Tests for pricing.py

Coverage notes:
- calculate_subtotal: fully covered
- calculate_discount: covered for known customer types
- calculate_tax: fully covered
- calculate_total: covered for regular and member customers

Intentional gap:
- 'vip' customer type in calculate_discount / calculate_total is NOT tested.
  A future analyzer should flag this path as insufficiently covered.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pricing import (
    calculate_subtotal,
    calculate_discount,
    calculate_tax,
    calculate_total,
)


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


class TestDiscount:
    def test_regular_customer_gets_no_discount(self):
        assert calculate_discount(100.00, "regular") == 0.00

    def test_member_gets_five_percent(self):
        assert calculate_discount(200.00, "member") == 10.00

    def test_unknown_type_treated_as_regular(self):
        assert calculate_discount(100.00, "guest") == 0.00

    # NOTE: 'vip' discount (10%) is intentionally NOT tested here.


class TestTax:
    def test_tax_on_round_amount(self):
        assert calculate_tax(100.00) == 8.00

    def test_tax_rounded_to_cents(self):
        # 8% of $49.99 = $3.9992 → rounds to $4.00
        assert calculate_tax(49.99) == 4.00

    def test_zero_amount(self):
        assert calculate_tax(0.00) == 0.00


class TestCalculateTotal:
    def test_regular_customer_full_pipeline(self):
        items = [{"name": "Widget", "price": 20.00, "quantity": 5}]
        result = calculate_total(items, "regular")
        assert result["subtotal"] == 100.00
        assert result["discount"] == 0.00
        assert result["taxable_amount"] == 100.00
        assert result["tax"] == 8.00
        assert result["total"] == 108.00

    def test_member_discount_reflected_in_total(self):
        items = [{"name": "Gadget", "price": 50.00, "quantity": 2}]
        result = calculate_total(items, "member")
        assert result["subtotal"] == 100.00
        assert result["discount"] == 5.00
        assert result["taxable_amount"] == 95.00
        assert result["tax"] == 7.60
        assert result["total"] == 102.60

    def test_result_keys_present(self):
        items = [{"name": "Thing", "price": 10.00, "quantity": 1}]
        result = calculate_total(items, "regular")
        assert set(result.keys()) == {
            "subtotal", "discount", "taxable_amount", "tax", "total"
        }
