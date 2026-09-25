# Demo Project — E-Commerce Order Processor

A small Python application that models an e-commerce order processing pipeline.
It exists as **ground truth** for the Change Impact Investigator hackathon demo.

## Module overview

| Module | Responsibility |
|---|---|
| `app/pricing.py` | Subtotal, discount, tax, and total calculation |
| `app/shipping.py` | Shipping cost by weight and destination zone |
| `app/checkout.py` | Assembles the full order (calls pricing + shipping) |
| `app/invoice.py` | Renders a formatted invoice from a completed order |

## Dependency graph

```
checkout.create_order
    └─ pricing.calculate_total
    │       └─ pricing.calculate_subtotal
    │       └─ pricing.calculate_discount
    │       └─ pricing.calculate_tax
    └─ shipping.calculate_shipping

invoice.generate_invoice
    └─ (consumes order dict from checkout.create_order)
```

## Running tests

```bash
# from the repo root
pip install -r requirements.txt
cd demo_project
pytest tests/ -v
```

## Known coverage gaps (intentional)

- `pricing.calculate_discount` / `calculate_total` with `customer_type="vip"` are
  not tested — the VIP 10% discount path is exercised in production but has no
  dedicated test.
- The international-shipping minimum boundary edge case has no test.

These gaps are intentional ground truth for demonstrating coverage analysis.
