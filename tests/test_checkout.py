# test_legacy_checkout.py

from legacy_checkout import process_order


def test_regular_customer():
    customer = {
        "name": "Ana",
        "type": "regular"
    }

    items = [
        {
            "name": "Notebook",
            "price": 1000.00,
            "qty": 1,
            "weight": 2
        }
    ]

    result = process_order(
        customer,
        items,
        state="MG"
    )

    assert result["subtotal"] == 1000.00
    assert result["discount"] == 50.00
    assert result["shipping"] == 0
    assert result["tax"] == 66.50
    assert result["total"] == 1016.50


def test_vip_customer():
    customer = {
        "name": "Carlos",
        "type": "vip"
    }

    items = [
        {
            "name": "Monitor",
            "price": 600,
            "qty": 2,
            "weight": 3
        }
    ]

    result = process_order(
        customer,
        items,
        state="SP"
    )

    assert result["subtotal"] == 1200
    assert result["discount"] == 180


def test_coupon():
    customer = {
        "name": "Maria",
        "type": "regular"
    }

    items = [
        {
            "name": "Teclado",
            "price": 200,
            "qty": 2,
            "weight": 1
        }
    ]

    result = process_order(
        customer,
        items,
        coupon="PROMO10",
        state="MG"
    )

    assert result["discount"] == 40


def test_duplicate_products():
    customer = {
        "name": "João",
        "type": "regular"
    }

    items = [
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Teclado", "price": 200, "qty": 1, "weight": 1}
    ]

    result = process_order(customer, items)

    assert result["duplicate_products"] == ["Mouse"]
