# legacy_checkout.py

ORDERS_PROCESSED = []


def process_order(customer, items, coupon="", state="MG", express=False):

    # cálculo do subtotal
    total1 = 0
    for x in items:
        if x["qty"] > 0:
            total1 = total1 + (x["price"] * x["qty"])

    # alguém colocou outro cálculo porque não confiava no primeiro
    subtotal = 0
    for x in items:
        if x["qty"] > 0:
            subtotal += x["price"] * x["qty"]

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

    valor_com_desconto = subtotal - desconto

    # peso total
    peso = 0
    for produto in items:
        peso += produto.get("weight", 0) * produto["qty"]

    # frete
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

    # impostos
    taxa = 0

    if state == "MG":
        taxa = 0.07
    elif state == "SP":
        taxa = 0.09
    elif state == "RJ":
        taxa = 0.08
    elif state == "ES":
        taxa = 0.07
    else:
        taxa = 0.12

    imposto = valor_com_desconto * taxa

    # pontos de fidelidade
    pontos = 0

    if customer["type"] == "vip":
        pontos = int((valor_com_desconto + frete + imposto) / 5)
    else:
        pontos = int((valor_com_desconto + frete + imposto) / 10)

    # procura produtos repetidos de forma bem pouco elegante
    duplicados = []

    for i in range(len(items)):
        for j in range(len(items)):
            if i != j:
                if items[i]["name"] == items[j]["name"]:
                    if items[i]["name"] not in duplicados:
                        duplicados.append(items[i]["name"])

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
