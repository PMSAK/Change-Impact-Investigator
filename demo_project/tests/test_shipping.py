"""
Tests for shipping.py

Coverage:
- calculate_shipping: domestic and international zones, minimum charge
- calculate_shipping_with_discount: discount application and floor at zero

Intentional gap:
- No test exercises the exact boundary where weight * rate == MIN_SHIPPING
  for international shipping.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.shipping import calculate_shipping, calculate_shipping_with_discount


class TestCalculateShipping:
    def test_domestic_above_minimum(self):
        # 5 kg * $2.50 = $12.50
        assert calculate_shipping(5.0, "domestic") == 12.50

    def test_domestic_below_minimum_uses_minimum(self):
        # 1 kg * $2.50 = $2.50, but minimum is $5.00
        assert calculate_shipping(1.0, "domestic") == 5.00

    def test_international_above_minimum(self):
        # 3 kg * $7.00 = $21.00
        assert calculate_shipping(3.0, "international") == 21.00

    def test_unknown_destination_raises(self):
        with pytest.raises(ValueError, match="Unknown destination zone"):
            calculate_shipping(2.0, "mars")


class TestCalculateShippingWithDiscount:
    def test_discount_reduces_cost(self):
        # base = 5 kg * $2.50 = $12.50; discount $2.50 → $10.00
        assert calculate_shipping_with_discount(5.0, "domestic", 2.50) == 10.00

    def test_discount_cannot_make_cost_negative(self):
        # base = $5.00 (minimum); discount $10.00 → $0.00
        assert calculate_shipping_with_discount(1.0, "domestic", 10.00) == 0.00

    def test_zero_discount_returns_base(self):
        assert calculate_shipping_with_discount(5.0, "domestic", 0.00) == 12.50
