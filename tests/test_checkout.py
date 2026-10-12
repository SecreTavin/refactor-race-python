# test_checkout.py

import pytest

import legacy_checkout
from legacy_checkout import process_order


# Test case for a regular customer
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
    
# Test case for multiple items in the order
def test_multiple_items():
    customer = {
        "name": "Pedro",
        "type": "regular"
    }

    items = [
        {
            "name": "Notebook",
            "price": 1000.00,
            "qty": 1,
            "weight": 2
        },
        {
            "name": "Mouse",
            "price": 50.00,
            "qty": 2,
            "weight": 0.1
        },
        {
            "name": "Teclado",
            "price": 200.00,
            "qty": 1,
            "weight": 1
        }
    ]

    result = process_order(
        customer,
        items,
        state="MG"
    )

    assert result["subtotal"] == 1300.00
    assert result["discount"] == 65.00
    assert result["shipping"] == 0
    assert result["tax"] == 86.45
    assert result["total"] == 1321.45

# Test case for a VIP customer
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

# Test case for applying a coupon
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

# Test case for duplicate products
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
    
# Test case for an empty cart
def test_empty_cart():
    customer = {
        "name": "Lucas",
        "type": "regular"
    }

    items = []

    result = process_order(customer, items)

    # Subtotal 0 fica abaixo do mínimo para frete grátis (500), então o
    # frete base do Sudeste (20) é cobrado mesmo sem itens: é o comportamento
    # do código original, e não deve ser alterado sem um requisito.
    assert result["subtotal"] == 0
    assert result["discount"] == 0
    assert result["shipping"] == 20
    assert result["tax"] == 0
    assert result["total"] == 20
    assert result["duplicate_products"] == []


def test_product_repeated_three_times_is_listed_once():
    customer = {"name": "João", "type": "regular"}

    items = [
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
    ]

    result = process_order(customer, items)

    assert result["duplicate_products"] == ["Mouse"]


def test_duplicate_products_keep_order_of_first_appearance():
    customer = {"name": "João", "type": "regular"}

    items = [
        {"name": "Teclado", "price": 200, "qty": 1, "weight": 1},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Teclado", "price": 200, "qty": 1, "weight": 1},
        {"name": "Monitor", "price": 900, "qty": 1, "weight": 3},
    ]

    result = process_order(customer, items)

    assert result["duplicate_products"] == ["Teclado", "Mouse"]


# ---------------------------------------------------------------------------
# Testes de caracterização adicionados pela equipe.
# Os valores esperados foram conferidos contra o código original (baseline),
# para garantir que descrevem o comportamento existente, sem inventar regras.
# ---------------------------------------------------------------------------

def make_customer(customer_type, name="Cliente"):
    return {"name": name, "type": customer_type}


def make_item(name="Produto", price=100.0, qty=1, weight=0):
    return {"name": name, "price": price, "qty": qty, "weight": weight}


# --- Descontos por tipo de cliente ---

def test_employee_receives_twenty_percent_discount():
    result = process_order(
        make_customer("employee"), [make_item(price=300, weight=2)], state="MG"
    )

    assert result["subtotal"] == 300
    assert result["discount"] == 60
    assert result["shipping"] == 20.8
    assert result["tax"] == 16.8
    assert result["total"] == 277.6


def test_vip_customer_below_1000_receives_ten_percent_discount():
    result = process_order(
        make_customer("vip"), [make_item(price=400, weight=1)], state="SP"
    )

    assert result["discount"] == 40
    assert result["shipping"] == 20.4
    assert result["tax"] == 32.4
    assert result["total"] == 412.8


def test_vip_customer_at_exactly_1000_receives_fifteen_percent_discount():
    result = process_order(make_customer("vip"), [make_item(price=1000)])

    assert result["discount"] == 150


def test_regular_customer_below_800_receives_no_discount():
    result = process_order(make_customer("regular"), [make_item(price=799.99)])

    assert result["discount"] == 0


def test_regular_customer_at_exactly_800_receives_five_percent_discount():
    result = process_order(make_customer("regular"), [make_item(price=800)])

    assert result["discount"] == 40


def test_unknown_customer_type_receives_no_discount():
    result = process_order(make_customer("guest"), [make_item(price=2000)])

    assert result["discount"] == 0


# --- Cupons ---

def test_promo20_coupon_applies_when_subtotal_is_at_least_500():
    result = process_order(
        make_customer("regular"), [make_item(price=500)], coupon="PROMO20"
    )

    assert result["discount"] == 100


def test_promo20_coupon_is_ignored_below_500():
    result = process_order(
        make_customer("regular"), [make_item(price=499)], coupon="PROMO20"
    )

    assert result["discount"] == 0


def test_vip50_coupon_adds_fixed_50_for_vip_customer():
    result = process_order(
        make_customer("vip"), [make_item(price=400)], coupon="VIP50"
    )

    assert result["discount"] == 90


def test_vip50_coupon_is_ignored_for_non_vip_customer():
    result = process_order(
        make_customer("regular"), [make_item(price=400)], coupon="VIP50"
    )

    assert result["discount"] == 0


def test_unknown_coupon_is_ignored():
    result = process_order(
        make_customer("regular"), [make_item(price=400)], coupon="BLACKFRIDAY"
    )

    assert result["discount"] == 0


def test_discount_is_limited_to_25_percent_of_subtotal():
    result = process_order(
        make_customer("employee"), [make_item(price=1000)], coupon="PROMO10"
    )

    assert result["discount"] == 250


def test_vip_discount_with_vip50_coupon_is_limited_to_25_percent():
    result = process_order(
        make_customer("vip"), [make_item(price=200)], coupon="VIP50"
    )

    assert result["discount"] == 50


# --- Frete ---

def test_shipping_is_free_at_exactly_500_without_express():
    result = process_order(
        make_customer("regular"), [make_item(price=500, weight=10)]
    )

    assert result["shipping"] == 0


def test_shipping_below_500_in_southeast_uses_southeast_rate():
    result = process_order(
        make_customer("regular"), [make_item(price=100, weight=5)], state="RJ"
    )

    assert result["shipping"] == 22


def test_shipping_outside_southeast_uses_other_regions_rate():
    result = process_order(
        make_customer("regular"), [make_item(price=100, weight=5)], state="BA"
    )

    assert result["shipping"] == 38


def test_express_shipping_is_charged_even_above_500():
    result = process_order(
        make_customer("regular"),
        [make_item(price=600, weight=5)],
        state="MG",
        express=True,
    )

    assert result["shipping"] == 39.6


def test_express_shipping_outside_southeast():
    result = process_order(
        make_customer("regular"),
        [make_item(price=100, weight=5)],
        state="BA",
        express=True,
    )

    assert result["shipping"] == 68.4


def test_item_without_weight_counts_as_zero_weight():
    item_without_weight = {"name": "Cabo", "price": 50, "qty": 3}

    result = process_order(make_customer("regular"), [item_without_weight])

    assert result["shipping"] == 20


# --- Impostos ---

@pytest.mark.parametrize(
    ("state", "expected_tax"),
    [("MG", 7), ("SP", 9), ("RJ", 8), ("ES", 7), ("BA", 12), ("RS", 12)],
)
def test_tax_rate_depends_on_state(state, expected_tax):
    result = process_order(
        make_customer("regular"), [make_item(price=100)], state=state
    )

    assert result["tax"] == expected_tax


def test_tax_is_calculated_over_discounted_value():
    result = process_order(
        make_customer("employee"), [make_item(price=100)], state="SP"
    )

    assert result["tax"] == 7.2


# --- Subtotal ---

def test_items_with_zero_quantity_are_not_added_to_subtotal():
    items = [make_item(price=100, qty=2), make_item(name="Brinde", price=50, qty=0)]

    result = process_order(make_customer("regular"), items)

    assert result["subtotal"] == 200


# --- Pontos de fidelidade ---

def test_regular_customer_earns_one_point_per_10_spent():
    result = process_order(
        make_customer("regular"), [make_item(price=100, weight=0)], state="MG"
    )

    # total = 100 + 20 (frete) + 7 (imposto) = 127
    assert result["total"] == 127
    assert result["points"] == 12


def test_vip_customer_earns_one_point_per_5_spent():
    result = process_order(
        make_customer("vip"), [make_item(price=100, weight=0)], state="MG"
    )

    # total = 90 + 20 (frete) + 6,30 (imposto) = 116,30
    assert result["total"] == 116.3
    assert result["points"] == 23


# --- Produtos duplicados ---

def test_order_without_repeated_products_has_no_duplicates():
    items = [make_item(name="Mouse"), make_item(name="Teclado")]

    result = process_order(make_customer("regular"), items)

    assert result["duplicate_products"] == []


# --- Efeitos colaterais preservados ---

def test_processed_order_is_stored_in_history():
    result = process_order(make_customer("regular", name="Bia"), [make_item()])

    assert legacy_checkout.ORDERS_PROCESSED[-1] is result


def test_order_summary_is_printed(capsys):
    process_order(make_customer("regular", name="Bia"), [make_item(price=100)])

    output = capsys.readouterr().out
    assert "Pedido processado para Bia" in output
    assert "TOTAL: 127.0" in output


def test_result_contains_customer_name():
    result = process_order(make_customer("regular", name="Bia"), [make_item()])

    assert result["customer"] == "Bia"
