# Testes unitários das funções extraídas na refatoração. Antes, essas regras
# só podiam ser testadas passando pela função process_order inteira.

import legacy_checkout
from legacy_checkout import (
    calculate_coupon_discount,
    calculate_customer_type_discount,
    calculate_discount,
    calculate_order_totals,
    calculate_points,
    calculate_shipping,
    calculate_tax,
    find_duplicate_products,
)


def test_customer_type_discount_for_each_type():
    assert calculate_customer_type_discount("vip", 999) == 999 * 0.10
    assert calculate_customer_type_discount("vip", 1000) == 150
    assert calculate_customer_type_discount("employee", 100) == 20
    assert calculate_customer_type_discount("regular", 800) == 40
    assert calculate_customer_type_discount("regular", 799) == 0
    assert calculate_customer_type_discount("guest", 5000) == 0


def test_coupon_discount_only_applies_to_known_coupons():
    assert calculate_coupon_discount("PROMO10", "regular", 100) == 10
    assert calculate_coupon_discount("PROMO20", "regular", 500) == 100
    assert calculate_coupon_discount("VIP50", "vip", 100) == 50
    assert calculate_coupon_discount("VIP50", "regular", 100) == 0
    assert calculate_coupon_discount("", "vip", 100) == 0


def test_total_discount_never_exceeds_25_percent():
    assert calculate_discount("employee", 1000, "PROMO20") == 250


def test_shipping_rules():
    assert calculate_shipping(500, 10, "MG", express=False) == 0
    assert calculate_shipping(100, 10, "MG", express=False) == 24
    assert calculate_shipping(100, 10, "AM", express=False) == 41
    assert calculate_shipping(100, 0, "MG", express=True) == 36


def test_tax_uses_default_rate_for_unmapped_state():
    assert calculate_tax(100, "SP") == 9
    assert calculate_tax(100, "PE") == 12


def test_points_are_truncated_not_rounded():
    assert calculate_points("regular", 19.99) == 1
    assert calculate_points("vip", 19.99) == 3


def test_find_duplicate_products_without_repetition():
    items = [{"name": "A"}, {"name": "B"}, {"name": "A"}, {"name": "A"}]

    assert find_duplicate_products(items) == ["A"]
    assert find_duplicate_products([]) == []


def test_calculate_order_totals_has_no_side_effects(capsys):
    history_before = list(legacy_checkout.ORDERS_PROCESSED)
    items = [{"name": "Notebook", "price": 1000.0, "qty": 1, "weight": 2}]

    totals = calculate_order_totals("regular", items, "", "MG", False)

    assert totals.subtotal == 1000
    assert totals.discount == 50
    assert totals.shipping == 0
    assert round(totals.tax, 2) == 66.5
    assert round(totals.total, 2) == 1016.5
    assert capsys.readouterr().out == ""
    assert legacy_checkout.ORDERS_PROCESSED == history_before
