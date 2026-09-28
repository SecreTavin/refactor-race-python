# legacy_checkout.py

ORDERS_PROCESSED = []


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
    taxa = 0
    
    match state:
        case "MG":
            taxa = 0.07
        case "SP":
            taxa = 0.09
        case "RJ":
            taxa = 0.08
        case "ES":
            taxa = 0.07
        case _:
            taxa = 0.12

    imposto = valor_com_desconto * taxa
    
    return imposto

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
    if customer["type"] == "vip":
        if subtotal >= 1000:
            desconto = subtotal * 0.15
        else:
            desconto = subtotal * 0.10
    else:
        if customer["type"] == "employee":
            desconto = subtotal * 0.20
        else:
            if customer["type"] == "regular":
                if subtotal >= 800:
                    desconto = subtotal * 0.05

    # cupons
    if coupon == "PROMO10":
        desconto = desconto + subtotal * 0.10

    if coupon == "PROMO20" and subtotal >= 500:
        desconto = desconto + subtotal * 0.20

    if coupon == "VIP50" and customer["type"] == "vip":
        desconto = desconto + 50

    # desconto máximo permitido
    if desconto > subtotal * 0.25:
        desconto = subtotal * 0.25

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
    if subtotal >= 500 and express == False:
        frete = 0
    else:
        if state == "MG" or state == "SP" or state == "RJ" or state == "ES":
            frete = 20 + peso * 0.4
        else:
            frete = 35 + peso * 0.6

        if express == True:
            frete = frete * 1.8

    return frete


def points_calculation(customer, valor_com_desconto, frete, imposto):
    pontos = 0
    
    if customer["type"] == "vip":
        pontos = int((valor_com_desconto + frete + imposto) / 5)
    else:
        pontos = int((valor_com_desconto + frete + imposto) / 10)
        
    return pontos

def find_duplicate_products(items):
    duplicados = []
    
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i]["name"] == items[j]["name"]:
                duplicados.append(items[i]["name"])

    return duplicados
