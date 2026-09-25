"""
Tests for checkout.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.checkout import create_order


SAMPLE_ITEMS = [
    {"name": "Widget", "price": 25.00, "quantity": 2},
    {"name": "Gadget", "price": 15.00, "quantity": 1},
]


class TestCreateOrder:
    def test_order_contains_expected_keys(self):
        order = create_order(SAMPLE_ITEMS, weight=2.0, destination="domestic")
        expected_keys = {
            "items", "subtotal", "tax", "items_total", "shipping", "order_total",
        }
        assert set(order.keys()) == expected_keys

    def test_domestic_order(self):
        order = create_order(SAMPLE_ITEMS, weight=2.0, destination="domestic")
        assert order["subtotal"] == 65.00
        assert order["tax"] == 5.20       # 8% of 65
        assert order["items_total"] == 70.20
        assert order["shipping"] == 5.00
        assert order["order_total"] == 75.20

    def test_international_shipping_applied(self):
        order = create_order(SAMPLE_ITEMS, weight=3.0, destination="international")
        assert order["shipping"] == 21.00
        assert order["order_total"] == round(order["items_total"] + 21.00, 2)

    def test_order_total_equals_items_total_plus_shipping(self):
        order = create_order(SAMPLE_ITEMS, weight=4.0, destination="domestic")
        assert order["order_total"] == round(order["items_total"] + order["shipping"], 2)

    def test_invalid_destination_raises(self):
        with pytest.raises(ValueError):
            create_order(SAMPLE_ITEMS, weight=1.0, destination="moon")
