# METRICS — Antes x Depois

## Como reproduzir

```bash
pip install -r requirements-dev.txt
pytest -v
pytest --cov=legacy_checkout --cov-report=term-missing
radon cc src/legacy_checkout.py -s -a
radon mi src/legacy_checkout.py -s
ruff check src/legacy_checkout.py --statistics
```

> O código fica em `src/`. O `pytest.ini` inclui `src` no `pythonpath`, por isso
> `--cov=legacy_checkout` funciona sem precisar do caminho. No `radon` e no `ruff`
> é preciso passar o caminho completo do arquivo. As versões das ferramentas estão
> fixadas no `requirements-dev.txt`, porque o conjunto de regras padrão do Ruff
> muda entre versões.

- **Antes**: código original do commit `70d0a01`, rodando a suíte original (4 testes).
- **Depois**: código atual da branch, rodando a suíte completa.

## Comparação

| Indicador                          | Antes                                | Depois                              | Resultado |
|------------------------------------|--------------------------------------|-------------------------------------|-----------|
| Testes passando                    | 4 / 4                                | 49 / 49                             | ✅ melhorou |
| Cobertura de testes                | 83% (12 de 72 linhas sem cobertura)  | 100% (0 de 112 linhas sem cobertura)| ✅ melhorou |
| Complexidade da função principal   | `process_order` — **E (34)**         | `process_order` — **A (1)**         | ✅ melhorou |
| Maior complexidade no módulo       | E (34)                               | B (6)                               | ✅ melhorou |
| Complexidade média                 | E (34,0) — 1 bloco                   | A (2,47) — 15 blocos                | ✅ melhorou |
| Índice de manutenibilidade         | A (51,69)                            | A (48,91)                           | ⚠️ caiu 2,78 pontos (continua na faixa A) — ver análise |
| Problemas identificados pelo Ruff  | 4 (3× SIM102, 1× PLR1730)            | 0                                   | ✅ melhorou |
| Quantidade de testes               | 4                                    | 49 (4 originais + 45 novos)         | ✅ melhorou |

### Distribuição dos 49 testes

| Arquivo | Testes | Finalidade |
|---|---|---|
| `tests/test_checkout.py` | 40 | 4 originais + 36 de caracterização via `process_order` (o parametrizado de impostos conta como 6) |
| `tests/test_checkout_units.py` | 8 | Testes unitários das funções extraídas |
| `tests/test_golden_master.py` | 1 | Compara com o código original em 5000 pedidos aleatórios |

## Análise

**Complexidade.** No original, toda a lógica ficava numa função com 34 caminhos
independentes (nota E). Hoje `process_order` só orquestra (CC 1), e as funções
mais complexas são as de regra de desconto, com CC 6 (nota B), porque cada `if`
corresponde a uma regra de negócio real.

**Cobertura.** Subiu de 83% para 100%. As linhas que não eram cobertas antes
(desconto de funcionário, VIP abaixo de 1000, PROMO20, VIP50, teto de 25%, frete
fora do Sudeste, frete expresso) agora têm testes com os valores esperados
conferidos no código original. Cobertura por si só não prova qualidade. Por isso
também existe o teste de golden master: ele confere que o comportamento é
**idêntico** ao original, e não apenas que as linhas foram executadas.

**Índice de manutenibilidade (queda de 51,69 para 48,91).** O MI do radon combina
o volume de Halstead, a complexidade ciclomática e o **número de linhas** (em
escala logarítmica). A complexidade caiu muito, mas o arquivo cresceu de 72 para
112 instruções: foram adicionadas 28 constantes nomeadas no lugar dos números
mágicos, docstrings, a dataclass `OrderTotals` e as funções extraídas. Cada
constante nomeada soma volume de Halstead e linhas, o que puxa o MI para baixo.
Ou seja, as mudanças que mais melhoram a legibilidade são justamente as que o
indicador penaliza. Poderíamos subir o MI mexendo só na medição (por exemplo,
passando as constantes para outro arquivo, fora do comando pedido), mas optamos
por registrar o valor real. O índice continua na faixa A (acima de 20) e aparece
como ponto de atenção em *Melhorias futuras* no README.

**Ruff.** Os 4 problemas do original (3 `if` aninhados que poderiam ser combinados
e um teto de desconto feito com `if` em vez de `min()`) foram eliminados pela
própria refatoração, sem suprimir nenhuma regra.

## Saídas — Antes (baseline)

```text
$ pytest -v
tests/test_checkout.py::test_regular_customer PASSED
tests/test_checkout.py::test_vip_customer PASSED
tests/test_checkout.py::test_coupon PASSED
tests/test_checkout.py::test_duplicate_products PASSED
4 passed

$ pytest --cov=legacy_checkout --cov-report=term-missing
src/legacy_checkout.py      72     12    83%   27, 30, 41, 44, 48, 66, 69, 78-83

$ radon cc src/legacy_checkout.py -s -a
    F 6:0 process_order - E (34)
Average complexity: E (34.0)

$ radon mi src/legacy_checkout.py -s
src/legacy_checkout.py - A (51.69)

$ ruff check src/legacy_checkout.py --statistics
3	SIM102 	[ ] collapsible-if
1	PLR1730	[*] if-stmt-min-max
Found 4 errors.
```

## Saídas — Depois

```text
$ pytest -v
49 passed

$ pytest --cov=legacy_checkout --cov-report=term-missing
Name                     Stmts   Miss  Cover   Missing
src/legacy_checkout.py     112      0   100%

$ radon cc src/legacy_checkout.py -s -a
    F 136:0 calculate_customer_type_discount - B (6)
    F 151:0 calculate_coupon_discount - B (6)
    F 172:0 calculate_shipping - A (5)
    F 200:0 find_duplicate_products - A (4)
    F 118:0 calculate_subtotal - A (3)
    F 164:0 calculate_total_weight - A (2)
    F 191:0 calculate_points - A (2)
    C 57:0 OrderTotals - A (2)
    F 70:0 process_order - A (1)
    F 81:0 calculate_order_totals - A (1)
    F 94:0 build_order_result - A (1)
    F 107:0 print_order_summary - A (1)
    F 128:0 calculate_discount - A (1)
    F 187:0 calculate_tax - A (1)
    M 66:4 OrderTotals.total - A (1)
15 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.466666666666667)

$ radon mi src/legacy_checkout.py -s
src/legacy_checkout.py - A (48.91)

$ ruff check src/legacy_checkout.py --statistics
(nenhum problema — "All checks passed!")
```

## Otimização: busca de produtos duplicados

| | Antes | Depois |
|---|---|---|
| Algoritmo | dois laços sobre todos os pares `(i, j)` + `not in` numa lista | uma passada com `collections.Counter` |
| Comparações de nomes para *n* itens | *n*·(*n*−1) comparações de pares, mais a busca linear na lista de duplicados | *n* inserções num dicionário (hash) |
| Complexidade | O(n²) | O(n) |
| Resultado | nomes repetidos, sem repetição, na ordem da 1ª aparição | idêntico (verificado pelo golden master) |
