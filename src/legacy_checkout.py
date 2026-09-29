# legacy_checkout.py

from collections import Counter

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


def process_order(customer, items, coupon="", state="MG", express=False):

    #calculo do subtotal
    subtotal = 0
    subtotal = subtotal_calculation(items)

    # Calcula o desconto com base no tipo de cliente, subtotal e cupom
    desconto = 0
    desconto = discount_calculation(customer, subtotal, coupon)
    valor_com_desconto = subtotal - desconto

    # Calcula o peso total dos items do pedido
    peso = 0
    peso = weight_calculation(items)

    # Calcula o frete com base no subtotal, peso, estado e se é expresso
    frete = 0
    frete = shipping_calculation(subtotal, peso, state, express)

    # Calcula o imposto com base no estado e no valor com desconto
    imposto = 0
    imposto = tax_calculation(state, valor_com_desconto)

    # Calcula os pontos do cliente com base no valor com desconto, frete e imposto
    pontos = points_calculation(customer, valor_com_desconto, frete, imposto)
    
    # Procura produtos repetidos de forma bem pouco elegante
    duplicados = find_duplicate_products(items)
    
    # Calcula o total final do pedido
    total_final = round(valor_com_desconto + frete + imposto, 2)

    resultado = {
        "customer": customer["name"],
        "subtotal": round(subtotal, 2),
        "discount": round(desconto, 2),
        "shipping": round(frete, 2),
        "tax": round(imposto, 2),
        "total": total_final,
        "points": pontos,
        "duplicate_products": duplicados
    }

    ORDERS_PROCESSED.append(resultado)

    print("Pedido processado para " + customer["name"])
    print("Subtotal:", subtotal)
    print("Desconto:", desconto)
    print("Frete:", frete)
    print("Imposto:", imposto)
    print("TOTAL:", total_final)

    return resultado

# Calcula o imposto com base no estado e no valor com desconto
def tax_calculation(state, valor_com_desconto):
    taxa = TAX_RATES.get(state, DEFAULT_TAX_RATE)

    return valor_com_desconto * taxa

# Calcula o subtotal dos items do pedido
def subtotal_calculation(items):
    subtotal = 0
    
    for x in items:
        if x["qty"] > 0:
            subtotal += x["price"] * x["qty"]
            
    return subtotal

# Calcula o desconto com base no tipo de cliente, subtotal e cupom
def discount_calculation(customer, subtotal, coupon):
    desconto = 0

    # desconto por tipo de cliente
    if customer["type"] == VIP:
        if subtotal >= VIP_HIGH_VALUE_THRESHOLD:
            desconto = subtotal * VIP_HIGH_VALUE_DISCOUNT_RATE
        else:
            desconto = subtotal * VIP_DISCOUNT_RATE
    else:
        if customer["type"] == EMPLOYEE:
            desconto = subtotal * EMPLOYEE_DISCOUNT_RATE
        else:
            if customer["type"] == REGULAR:
                if subtotal >= REGULAR_DISCOUNT_THRESHOLD:
                    desconto = subtotal * REGULAR_DISCOUNT_RATE

    # cupons
    if coupon == COUPON_PROMO10:
        desconto = desconto + subtotal * PROMO10_RATE

    if coupon == COUPON_PROMO20 and subtotal >= PROMO20_MIN_SUBTOTAL:
        desconto = desconto + subtotal * PROMO20_RATE

    if coupon == COUPON_VIP50 and customer["type"] == VIP:
        desconto = desconto + VIP50_AMOUNT

    # desconto máximo permitido
    if desconto > subtotal * MAX_DISCOUNT_RATE:
        desconto = subtotal * MAX_DISCOUNT_RATE

    return desconto

# Calcula o peso total dos items do pedido
def weight_calculation(items):
    peso = 0
    
    for produto in items:
        peso += produto.get("weight", 0) * produto["qty"]
        
    return peso

# Calcula o frete com base no subtotal, peso, estado e se é expresso
def shipping_calculation(subtotal, peso, state, express):
    frete = 0
    if subtotal >= FREE_SHIPPING_THRESHOLD and express == False:
        frete = 0
    else:
        if state in SOUTHEAST_STATES:
            frete = SOUTHEAST_BASE_SHIPPING + peso * SOUTHEAST_SHIPPING_PER_KG
        else:
            frete = OTHER_REGIONS_BASE_SHIPPING + peso * OTHER_REGIONS_SHIPPING_PER_KG

        if express == True:
            frete = frete * EXPRESS_SHIPPING_MULTIPLIER

    return frete


def points_calculation(customer, valor_com_desconto, frete, imposto):
    pontos = 0
    
    if customer["type"] == VIP:
        pontos = int((valor_com_desconto + frete + imposto) / VIP_SPENT_PER_POINT)
    else:
        pontos = int((valor_com_desconto + frete + imposto) / DEFAULT_SPENT_PER_POINT)
        
    return pontos

def find_duplicate_products(items):
    name_counts = Counter(item["name"] for item in items)

    return [name for name, count in name_counts.items() if count > 1]
