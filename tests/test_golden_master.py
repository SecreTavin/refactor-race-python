# Golden master: compara o código refatorado com uma cópia congelada do
# código original em milhares de pedidos gerados aleatoriamente (semente
# fixa, portanto reproduzível). Verifica o resultado retornado, a saída
# impressa e o histórico ORDERS_PROCESSED.

import contextlib
import importlib.util
import io
import random
from pathlib import Path

import legacy_checkout

ORIGINAL_PATH = Path(__file__).parent / "golden_master" / "original_checkout.py"

PRODUCT_NAMES = ["Mouse", "Teclado", "Monitor", "Cabo", "Notebook"]
CUSTOMER_TYPES = ["vip", "employee", "regular", "guest"]
COUPONS = ["", "PROMO10", "PROMO20", "VIP50", "promo10", "INVALIDO"]
STATES = ["MG", "SP", "RJ", "ES", "BA", "RS", "PR"]
NUMBER_OF_ORDERS = 5000


def load_original_module():
    spec = importlib.util.spec_from_file_location("original_checkout", ORIGINAL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def random_item(rng):
    item = {
        "name": rng.choice(PRODUCT_NAMES),
        "price": rng.choice(
            [rng.randint(1, 1500), round(rng.uniform(0.01, 1500), 2), 500, 800, 1000]
        ),
        "qty": rng.randint(-1, 4),
    }
    if rng.random() < 0.8:
        item["weight"] = rng.choice([0, 0.1, 0.2, 1, 2.5, rng.randint(0, 50)])
    return item


def random_order(rng):
    customer = {"name": rng.choice(["Ana", "Bia"]), "type": rng.choice(CUSTOMER_TYPES)}
    items = [random_item(rng) for _ in range(rng.randint(0, 6))]
    options = {
        "coupon": rng.choice(COUPONS),
        "state": rng.choice(STATES),
        "express": rng.choice([True, False]),
    }
    return customer, items, options


def run_capturing_output(module, customer, items, options):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = module.process_order(customer, items, **options)
    return result, output.getvalue()


def test_refactored_code_matches_original_for_random_orders(monkeypatch):
    original = load_original_module()
    monkeypatch.setattr(legacy_checkout, "ORDERS_PROCESSED", [])
    rng = random.Random(2026)

    for _ in range(NUMBER_OF_ORDERS):
        customer, items, options = random_order(rng)

        expected = run_capturing_output(original, customer, items, options)
        actual = run_capturing_output(legacy_checkout, customer, items, options)

        assert actual == expected, (customer, items, options)

    assert legacy_checkout.ORDERS_PROCESSED == original.ORDERS_PROCESSED
