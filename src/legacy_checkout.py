"""Processamento de pedidos: subtotal, descontos, frete, impostos, pontos de
fidelidade e detecção de produtos repetidos."""

from collections import Counter
from dataclasses import dataclass

ORDERS_PROCESSED = []

# Tipos de cliente
VIP = "vip"
EMPLOYEE = "employee"
REGULAR = "regular"

# Desconto por tipo de cliente
VIP_DISCOUNT_RATE = 0.10
VIP_HIGH_VALUE_DISCOUNT_RATE = 0.15
VIP_HIGH_VALUE_THRESHOLD = 1000
EMPLOYEE_DISCOUNT_RATE = 0.20
REGULAR_DISCOUNT_RATE = 0.05
REGULAR_DISCOUNT_THRESHOLD = 800
MAX_DISCOUNT_RATE = 0.25

# Cupons
COUPON_PROMO10 = "PROMO10"
COUPON_PROMO20 = "PROMO20"
COUPON_VIP50 = "VIP50"
PROMO10_RATE = 0.10
PROMO20_RATE = 0.20
PROMO20_MIN_SUBTOTAL = 500
VIP50_AMOUNT = 50

# Frete
FREE_SHIPPING_THRESHOLD = 500
SOUTHEAST_STATES = frozenset({"MG", "SP", "RJ", "ES"})
SOUTHEAST_BASE_SHIPPING = 20
SOUTHEAST_SHIPPING_PER_KG = 0.4
OTHER_REGIONS_BASE_SHIPPING = 35
OTHER_REGIONS_SHIPPING_PER_KG = 0.6
EXPRESS_SHIPPING_MULTIPLIER = 1.8

# Impostos
TAX_RATES = {
    "MG": 0.07,
    "SP": 0.09,
    "RJ": 0.08,
    "ES": 0.07,
}
DEFAULT_TAX_RATE = 0.12

# Pontos de fidelidade: valor gasto necessário para ganhar 1 ponto
VIP_SPENT_PER_POINT = 5
DEFAULT_SPENT_PER_POINT = 10



@dataclass(frozen=True)
class OrderTotals:
    """Valores do pedido antes do arredondamento."""

    subtotal: float
    discount: float
    shipping: float
    tax: float

    @property
    def total(self):
        return self.subtotal - self.discount + self.shipping + self.tax


def process_order(customer, items, coupon="", state="MG", express=False):
    """Calcula o pedido, registra no histórico e imprime o resumo."""
    totals = calculate_order_totals(customer["type"], items, coupon, state, express)
    result = build_order_result(customer, items, totals)

    ORDERS_PROCESSED.append(result)
    print_order_summary(customer["name"], totals, result["total"])

    return result


def calculate_order_totals(customer_type, items, coupon, state, express):
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(customer_type, subtotal, coupon)
    weight = calculate_total_weight(items)

    return OrderTotals(
        subtotal=subtotal,
        discount=discount,
        shipping=calculate_shipping(subtotal, weight, state, express),
        tax=calculate_tax(subtotal - discount, state),
    )


def build_order_result(customer, items, totals):
    return {
        "customer": customer["name"],
        "subtotal": round(totals.subtotal, 2),
        "discount": round(totals.discount, 2),
        "shipping": round(totals.shipping, 2),
        "tax": round(totals.tax, 2),
        "total": round(totals.total, 2),
        "points": calculate_points(customer["type"], totals.total),
        "duplicate_products": find_duplicate_products(items),
    }


def print_order_summary(customer_name, totals, rounded_total):
    print(f"Pedido processado para {customer_name}")
    print("Subtotal:", totals.subtotal)
    print("Desconto:", totals.discount)
    print("Frete:", totals.shipping)
    print("Imposto:", totals.tax)
    print("TOTAL:", rounded_total)


# As somas usam laço explícito de propósito: desde o Python 3.12, sum() faz soma
# compensada de floats e pode diferir do original na última casa decimal.
def calculate_subtotal(items):
    """Soma preço x quantidade; itens com quantidade <= 0 são ignorados."""
    subtotal = 0
    for item in items:
        if item["qty"] > 0:
            subtotal += item["price"] * item["qty"]

    return subtotal


def calculate_discount(customer_type, subtotal, coupon):
    """Desconto do tipo de cliente + cupom, limitado a MAX_DISCOUNT_RATE."""
    discount = calculate_customer_type_discount(customer_type, subtotal)
    discount += calculate_coupon_discount(coupon, customer_type, subtotal)

    return min(discount, subtotal * MAX_DISCOUNT_RATE)


def calculate_customer_type_discount(customer_type, subtotal):
    if customer_type == VIP:
        if subtotal >= VIP_HIGH_VALUE_THRESHOLD:
            return subtotal * VIP_HIGH_VALUE_DISCOUNT_RATE
        return subtotal * VIP_DISCOUNT_RATE

    if customer_type == EMPLOYEE:
        return subtotal * EMPLOYEE_DISCOUNT_RATE

    if customer_type == REGULAR and subtotal >= REGULAR_DISCOUNT_THRESHOLD:
        return subtotal * REGULAR_DISCOUNT_RATE

    return 0


def calculate_coupon_discount(coupon, customer_type, subtotal):
    if coupon == COUPON_PROMO10:
        return subtotal * PROMO10_RATE

    if coupon == COUPON_PROMO20 and subtotal >= PROMO20_MIN_SUBTOTAL:
        return subtotal * PROMO20_RATE

    if coupon == COUPON_VIP50 and customer_type == VIP:
        return VIP50_AMOUNT

    return 0


def calculate_total_weight(items):
    weight = 0
    for item in items:
        weight += item.get("weight", 0) * item["qty"]

    return weight


def calculate_shipping(subtotal, weight, state, express):
    if subtotal >= FREE_SHIPPING_THRESHOLD and not express:
        return 0

    if state in SOUTHEAST_STATES:
        shipping = SOUTHEAST_BASE_SHIPPING + weight * SOUTHEAST_SHIPPING_PER_KG
    else:
        shipping = OTHER_REGIONS_BASE_SHIPPING + weight * OTHER_REGIONS_SHIPPING_PER_KG

    if express:
        shipping *= EXPRESS_SHIPPING_MULTIPLIER

    return shipping


def calculate_tax(discounted_value, state):
    return discounted_value * TAX_RATES.get(state, DEFAULT_TAX_RATE)


def calculate_points(customer_type, total):
    if customer_type == VIP:
        spent_per_point = VIP_SPENT_PER_POINT
    else:
        spent_per_point = DEFAULT_SPENT_PER_POINT

    return int(total / spent_per_point)


def find_duplicate_products(items):
    """Nomes que aparecem mais de uma vez, na ordem da primeira aparição.

    Usa Counter (uma passada, O(n)) no lugar da comparação de todos os pares
    (O(n²)) do código original.
    """
    name_counts = Counter(item["name"] for item in items)

    return [name for name, count in name_counts.items() if count > 1]
