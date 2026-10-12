# REFactor Race Python

Atividade da unidade curricular **Garantia e Qualidade do Software**: refatorar
um sistema legado de processamento de pedidos, melhorando a qualidade interna
**sem alterar o comportamento**, e provar a melhoria com testes e métricas.

## EQUIPE

| Integrante | Matrícula | E-mail | Papel |
|---|---|---|---|
| **Octávio Augusto Arruda dos Prazeres** | 326138211 | arrudaoctavio178@gmail.com | **Colaborador principal** — Desenvolvedor líder: conduziu a refatoração, a correção da regressão e a medição das métricas |
| **Rafael Martins Alves** | 325210271 | 325210271@ulife.com.br | **Colaborador principal** — Desenvolvedor e responsável por testes: extraiu as primeiras funções e criou testes (múltiplos itens, carrinho vazio) |
| Arthur Araujo Marzano | 32524206 | arthuramarzano10@gmail.com | Analista de qualidade: levantamento de code smells e acompanhamento das métricas |
| Luís Phillipe Pedra Souza | 325142539 | Luiphillip2020@gmail.com | Revisor técnico: revisão de legibilidade, organização e documentação |
| Mario Lana Veloso Junior | 325216033 | 325216033@ulife.com.br | Apoio aos testes e à documentação: revisão dos cenários de teste e do README |

Os papéis seguem a sugestão da atividade (analista de qualidade, desenvolvedor,
responsável por testes e revisor técnico) e foram alternados quando necessário.

## DESCRIÇÃO

`src/legacy_checkout.py` processa um pedido: calcula o subtotal, os descontos
(por tipo de cliente e por cupom), o frete, os impostos por estado e os pontos de
fidelidade, identifica produtos repetidos, registra o pedido num histórico e
imprime um resumo.

No início, tudo isso ficava numa única função `process_order` de ~120 linhas e
complexidade ciclomática 34. A equipe dividiu a função em partes pequenas e
testáveis, preservou exatamente o comportamento observável (retorno, saída
impressa e histórico) e documentou as métricas antes e depois.

### Estrutura do repositório

```
refactor-race-python/
├── src/
│   └── legacy_checkout.py         # código refatorado
├── tests/
│   ├── test_checkout.py           # testes originais + testes de caracterização
│   ├── test_checkout_units.py     # testes unitários das funções extraídas
│   ├── test_golden_master.py      # comparação automática com o código original
│   └── golden_master/
│       └── original_checkout.py   # cópia congelada do original (referência)
├── BASELINE - NÃO ALTERAR          # comandos usados para medir a baseline no Colab
├── METRICS.md                      # métricas antes x depois, com as saídas das ferramentas
├── README.md
├── pytest.ini                      # pythonpath = src, testpaths = tests
├── ruff.toml                       # exclui a cópia congelada da análise
├── requirements-dev.txt            # versões fixadas das ferramentas
└── .gitignore
```

A estrutura segue a mínima pedida. As adições (`test_golden_master.py`,
`golden_master/` e `ruff.toml`) estão justificadas em *Decisões técnicas*.

### Como executar

```bash
pip install -r requirements-dev.txt
pytest -v
pytest --cov=legacy_checkout --cov-report=term-missing
radon cc src/legacy_checkout.py -s -a
radon mi src/legacy_checkout.py -s
ruff check src/legacy_checkout.py --statistics
```

No Google Colab, basta usar `!` antes de cada comando.

## DIAGNÓSTICO INICIAL

Problemas encontrados no código original (commit `70d0a01`), antes de qualquer
alteração:

1. **`process_order` tinha responsabilidades demais.** Uma só função calculava o
   subtotal, o desconto, o peso, o frete, o imposto, os pontos e os duplicados,
   além de montar o resultado, gravar no histórico global e imprimir. O radon
   deu complexidade **E (34)**. Qualquer mudança numa regra exigia entender a
   função inteira.
2. **O subtotal era calculado duas vezes.** A variável `total1` era calculada e
   nunca usada, e o próprio comentário admitia o problema: *"alguém colocou outro
   cálculo porque não confiava no primeiro"*. Era código morto, que só gastava
   processamento.
3. **Condicionais aninhadas em excesso.** O desconto por tipo de cliente tinha
   quatro níveis de `if/else`, e a busca de duplicados tinha três `if` aninhados
   dentro de dois laços. O Ruff apontou 3× `SIM102` (collapsible-if).
4. **Números e strings mágicas.** Valores como `0.15`, `1000`, `800`, `0.25`,
   `500`, `20`, `0.4`, `35`, `0.6`, `1.8`, `0.07`… e textos como `"vip"` e
   `"PROMO10"` apareciam soltos. Não dava para saber o que cada número
   representava, e mudar uma regra exigia caçar valores pelo código.
5. **Busca de duplicados ineficiente.** Comparava todos os pares `(i, j)`,
   inclusive os dois sentidos, e ainda fazia `not in` numa lista. Isso é O(n²)
   comparações, e a própria função se descrevia como *"bem pouco elegante"*.
6. **Comparações redundantes.** `state == "MG" or state == "SP" or …` e a cadeia
   `if/elif` de alíquotas deveriam ser uma verificação de pertinência num
   conjunto e um mapeamento. `express == False` e `express == True` deveriam
   ser avaliações booleanas diretas.
7. **Teto de desconto feito à mão** com `if desconto > …: desconto = …`, quando
   `min()` expressa a intenção direto (Ruff `PLR1730`).
8. **Efeitos colaterais misturados ao cálculo.** `print` e
   `ORDERS_PROCESSED.append` ficavam dentro da função que calcula. Não era
   possível calcular um pedido sem imprimir e sem alterar o estado global, o
   que prejudicava a testabilidade.
9. **Estado global mutável.** `ORDERS_PROCESSED` é uma lista no nível do módulo
   que cresce a cada chamada, deixando os testes dependentes da ordem em que
   rodam.
10. **Nomes pouco descritivos e idiomas misturados.** `x`, `total1` e `taxa`,
    além da mistura de português (`desconto`, `frete`) com inglês (`subtotal`,
    `items`).
11. **Variáveis inicializadas e logo sobrescritas** (`desconto = 0`,
    `frete = 0`, `taxa = 0`, `pontos = 0`), o que gera ruído sem efeito.
12. **Pouca cobertura de testes.** Eram 4 testes com 83% de cobertura. Nenhum
    testava funcionário, VIP abaixo de R$ 1000, PROMO20, VIP50, o teto de 25%,
    frete fora do Sudeste nem frete expresso, então uma refatoração dessas
    regras não teria rede de segurança.

## CODE SMELLS ENCONTRADOS

| Code smell | Onde aparecia | Por que é um problema |
|---|---|---|
| **Long Method / God Function** | `process_order` inteira | Muitas responsabilidades e CC 34. Difícil de ler, testar e alterar com segurança. |
| **Duplicated Code / Dead Code** | Cálculo de `total1` e `subtotal` | Dois cálculos iguais, um deles sem uso. Confunde quem lê e desperdiça processamento. |
| **Deeply Nested Conditionals** | Desconto por tipo de cliente e busca de duplicados | Cada nível extra multiplica os caminhos e dificulta entender quando cada regra vale. |
| **Magic Numbers / Magic Strings** | Descontos, limites, frete, alíquotas, cupons, tipos de cliente | Escondem o significado das regras de negócio e espalham um mesmo valor por vários lugares. |
| **Inefficient Data Structure / Algorithm** | Duplicados: laço duplo + `not in` numa lista | O(n²). Um contador (`dict`) resolve com uma passada. |
| **Conditional instead of mapping** | Cadeia `if/elif` de alíquotas por estado | Acrescentar um estado exigia mais um ramo. Com mapeamento, basta acrescentar um dado. |
| **Side effects in calculation** | `print` e `append` dentro do cálculo | Impede testar o cálculo isolado e acopla regra de negócio a apresentação e armazenamento. |
| **Global Mutable State** | `ORDERS_PROCESSED` | Os testes passam a depender da ordem e surgem acoplamentos ocultos. |
| **Poor Naming** | `x`, `total1`, idiomas misturados | Os nomes não revelam a intenção. |
| **Comments explaining bad code** | "*alguém colocou outro cálculo…*", "*de forma bem pouco elegante*" | O comentário apontava o problema em vez de ele ser corrigido. |

## REFATORAÇÕES REALIZADAS

Cada item mostra **Problema encontrado → Alteração realizada → Justificativa**.
Os commits estão listados em *Histórico de commits*.

### 1. Extract Function: quebrar `process_order`
- **Problema:** uma função com CC 34 fazia tudo.
- **Alteração:** a lógica foi extraída para `calculate_subtotal`,
  `calculate_discount`, `calculate_total_weight`, `calculate_shipping`,
  `calculate_tax`, `calculate_points` e `find_duplicate_products`.
  `process_order` passou a só orquestrar.
- **Justificativa:** cada função tem uma única responsabilidade e um nome que
  diz o que calcula, e pode ser testada sozinha. `process_order` caiu de E (34)
  para A (1), e a maior complexidade do módulo agora é B (6).

### 2. Remove Dead Code: cálculo duplicado do subtotal
- **Problema:** `total1` era calculado e nunca usado.
- **Alteração:** ficou um único cálculo, em `calculate_subtotal`.
- **Justificativa:** elimina código morto e a dúvida sobre qual dos dois
  cálculos era o "certo".

### 3. Replace Magic Number with Constant
- **Problema:** números e strings sem significado espalhados pelo código.
- **Alteração:** 28 constantes nomeadas e agrupadas por assunto (tipos de
  cliente, descontos, cupons, frete, impostos, pontos), como
  `VIP_HIGH_VALUE_THRESHOLD = 1000` e `EXPRESS_SHIPPING_MULTIPLIER = 1.8`.
- **Justificativa:** o nome explica a regra, e mudar um valor passa a ser
  alterar um único ponto do código.

### 4. Replace Conditional with Mapping / Simplify Conditional
- **Problema:** cadeia `if/elif` para as alíquotas e `or` encadeado para os
  estados do Sudeste.
- **Alteração:** `TAX_RATES = {"MG": 0.07, …}` com
  `TAX_RATES.get(state, DEFAULT_TAX_RATE)` e
  `SOUTHEAST_STATES = frozenset({"MG", "SP", "RJ", "ES"})` com `state in …`.
- **Justificativa:** as regras ficam como dados. Acrescentar um estado não exige
  um novo ramo, e a complexidade cai.

### 5. Separar regras de desconto + Guard Clauses
- **Problema:** quatro níveis de `if/else` misturando desconto por cliente,
  cupons e teto.
- **Alteração:** `calculate_customer_type_discount` (regra por cliente),
  `calculate_coupon_discount` (regra por cupom) e `calculate_discount` (soma as
  duas e aplica `min(…, subtotal * MAX_DISCOUNT_RATE)`), com retornos
  antecipados.
- **Justificativa:** cada regra fica isolada e legível, o aninhamento some e os
  avisos `SIM102` e `PLR1730` do Ruff desaparecem sem supressão.

### 6. Otimização: busca de duplicados em O(n)
- **Problema:** laço duplo O(n²) com `not in` numa lista.
- **Alteração:** `Counter(item["name"] for item in items)` e depois
  `[name for name, count in name_counts.items() if count > 1]`.
- **Justificativa:** uma única passada. Como o `Counter` preserva a ordem de
  inserção, o resultado é o mesmo do original: cada nome repetido aparece uma
  vez, na ordem da primeira aparição. É ao mesmo tempo refatoração e
  otimização.

### 7. Separate Responsibilities: cálculo x registro x impressão
- **Problema:** o cálculo não podia rodar sem `print` e sem alterar
  `ORDERS_PROCESSED`.
- **Alteração:** `calculate_order_totals` (cálculo puro, que devolve a
  dataclass imutável `OrderTotals` com os valores brutos),
  `build_order_result` (monta o dicionário arredondado) e `print_order_summary`
  (imprime). `process_order` só coordena essas etapas.
- **Justificativa:** as regras podem ser testadas sem efeitos colaterais (ver
  `test_calculate_order_totals_has_no_side_effects`), e a apresentação fica
  isolada. O histórico e o `print` continuam em `process_order` porque fazem
  parte do comportamento observável que precisa ser preservado.

### 8. Rename Variable / Remove Unnecessary Variables
- **Problema:** `x`, `total1`, idiomas misturados e variáveis zeradas e logo
  sobrescritas.
- **Alteração:** nomes em inglês e padronizados (`item`, `subtotal`,
  `discount`, `shipping`, `tax`, `spent_per_point`), com as inicializações
  inúteis removidas.
- **Justificativa:** os nomes revelam a intenção, e o vocabulário fica
  consistente com as chaves do resultado (`"discount"`, `"shipping"`,
  `"tax"`…).

### 9. Correção de regressão (fix)
- **Problema:** a primeira extração de `find_duplicate_products`, no commit
  `ab64f8b`, mudou o comportamento. Com 3 itens "Mouse" iguais, o original
  devolvia `["Mouse"]` e a versão extraída passou a devolver
  `["Mouse", "Mouse", "Mouse"]`. Os testes da época só usavam 2 repetições e
  não pegaram o erro.
- **Alteração:** primeiro foi escrito um teste que falhava, depois veio a
  correção com `Counter` (commit `fix:`).
- **Justificativa:** restaura o comportamento original. Serviu de lição para a
  equipe: "os testes passam" não basta se os testes não cobrem o caso. Por isso
  criamos o golden master (abaixo).

## TESTES ADICIONADOS

A suíte passou de **4 para 50 testes**. Os 4 originais foram mantidos sem
alteração. Todos os valores esperados dos testes novos foram **conferidos no
código original** antes da refatoração, para garantir que eles descrevem o
comportamento existente e não regras inventadas.

**`tests/test_checkout.py`: caracterização via `process_order` (37 novos)**

| Área | Cenários |
|---|---|
| Tipo de cliente | funcionário (20%); VIP abaixo de 1000 (10%); VIP exatamente em 1000 (15%); regular abaixo de 800 (0%); regular exatamente em 800 (5%); tipo desconhecido (0%) |
| Cupons | PROMO20 a partir de 500; PROMO20 ignorado abaixo de 500; VIP50 para VIP; VIP50 ignorado para não VIP; cupom desconhecido ignorado |
| Teto de desconto | funcionário + PROMO10 limitado a 25%; VIP + VIP50 limitado a 25% |
| Frete | grátis exatamente em 500; Sudeste abaixo de 500; fora do Sudeste; expresso cobrado mesmo acima de 500; expresso fora do Sudeste; item sem peso |
| Impostos | alíquota de MG, SP, RJ, ES, BA e RS (parametrizado); imposto calculado sobre o valor já com desconto |
| Pedido | vários produtos diferentes (`test_multiple_items`); carrinho vazio (`test_empty_cart`) |
| Subtotal | itens com quantidade zero são ignorados |
| Pontos | regular ganha 1 ponto a cada 10; VIP ganha 1 ponto a cada 5 |
| Duplicados | produto repetido 3 vezes aparece uma vez; ordem da primeira aparição; pedido sem repetição |
| Efeitos preservados | pedido gravado em `ORDERS_PROCESSED`; resumo impresso; nome do cliente no resultado |

> **Correção de expectativa em `test_empty_cart`.** Na primeira versão, o teste
> esperava frete 0 para um carrinho vazio e falhava. Conferindo no código
> original, o subtotal 0 fica abaixo do mínimo para frete grátis (500), então o
> frete base do Sudeste (R$ 20) é cobrado e o total fica em R$ 20. Como uma regra
> de negócio não pode mudar sem requisito, quem foi ajustado foi o **teste**, e
> não o código (commit `test: corrige expectativa do teste de carrinho vazio`).
> Se a regra desejada for frete zero para pedido vazio, isso precisa vir como
> novo ticket.

**`tests/test_checkout_units.py`: unitários (8)**
Testam as funções extraídas direto (desconto por cliente, cupom, teto, frete,
imposto com alíquota padrão, truncamento de pontos, duplicados) e confirmam que
`calculate_order_totals` não imprime nada e não altera o histórico.

**`tests/test_golden_master.py`: golden master (1)**
Gera **5000 pedidos aleatórios** com semente fixa, portanto reproduzíveis,
variando tipos de cliente, cupons (inclusive inválidos e minúsculos), estados,
frete expresso, quantidades negativas, zero e positivas, itens sem peso e nomes
repetidos. O resultado, **a saída impressa e o histórico** do código refatorado
precisam ser **idênticos** aos da cópia congelada do original. Conferimos que
esse teste **falha** no commit `ab64f8b`, ou seja, ele detecta a regressão dos
duplicados.

## MÉTRICAS ANTES E DEPOIS

Os detalhes e as saídas completas das ferramentas estão em [METRICS.md](METRICS.md).

| Indicador                        | Antes          | Depois         |
|----------------------------------|----------------|----------------|
| Testes passando                  | 4 / 4          | 50 / 50        |
| Cobertura de testes              | 83%            | 100%           |
| Complexidade da função principal | E (34)         | A (1)          |
| Complexidade média               | E (34,0)       | A (2,47)       |
| Índice de manutenibilidade       | A (51,69)      | A (48,91)      |
| Problemas identificados pelo Ruff| 4              | 0              |
| Quantidade de testes             | 4              | 50             |

**A métrica que mais melhorou foi a complexidade ciclomática:** a função
principal caiu de 34 para 1, e a complexidade média, de 34 para 2,47.

O **índice de manutenibilidade caiu 2,78 pontos**, mas continua na faixa A. O MI
do radon penaliza o tamanho do arquivo, e a refatoração acrescentou constantes
nomeadas, docstrings e funções pequenas. São mudanças que melhoram a
legibilidade, mas aumentam o número de linhas. Preferimos registrar o valor real
a mexer na forma de medir. A análise completa está em `METRICS.md`.

## DECISÕES TÉCNICAS

1. **Preservar o comportamento, inclusive as esquisitices.** Por causa dos
   testes secretos (seção 12), nenhuma regra foi "melhorada" sem requisito.
   Continuam iguais: cupons com diferenciação de maiúsculas e minúsculas
   (Ticket 2 ainda não liberado), itens com `qty <= 0` ignorados em silêncio no
   subtotal (Ticket 1 ainda não liberado), quantidade negativa reduzindo o peso,
   tipo de cliente desconhecido sem desconto e o `print` do resumo com os
   valores sem arredondamento.
2. **Assinatura e módulo mantidos.** `process_order(customer, items, coupon="",
   state="MG", express=False)` continua em `legacy_checkout`, com o mesmo formato
   de retorno, para que testes externos continuem funcionando.
3. **`ORDERS_PROCESSED` e `print` mantidos.** Fazem parte do comportamento
   observável, mas foram isolados das regras (ver refatoração 7).
4. **Laço explícito em vez de `sum()`.** A verificação diferencial mostrou que, a
   partir do Python 3.12, `sum()` faz soma compensada de floats. Isso mudava a
   última casa decimal do subtotal impresso (`6921.24` contra
   `6921.240000000001` no original) e poderia, num caso limite, alterar um
   arredondamento. Por isso as somas continuam em laço, com um comentário
   explicando o motivo.
5. **Dataclass `OrderTotals` imutável.** Carrega os valores brutos entre o
   cálculo, a montagem do resultado e a impressão, sem campos auxiliares
   escondidos no dicionário de retorno. O total é derivado (`@property`), então
   não tem como ficar inconsistente.
6. **`express` tratado como booleano.** `== False` e `== True` foram trocados
   por `not express` e `if express`. Para os valores do contrato (`True` ou
   `False`) o resultado é idêntico. A diferença só aparece com valores que não
   são booleanos (por exemplo `None`), que estão fora do uso previsto.
7. **Golden master com cópia congelada do original.** Guardar uma cópia do
   código antigo em `tests/golden_master/` parece redundante, mas é a forma mais
   forte de responder à pergunta *"como vocês comprovam que o comportamento foi
   preservado?"*: milhares de casos comparados automaticamente, e não só os que
   a equipe lembrou de escrever.
8. **Versões fixadas e `ruff.toml`.** O conjunto de regras padrão do Ruff muda
   entre versões. Sem fixar a versão, outra pessoa poderia obter outra contagem
   de problemas. O `ruff.toml` só exclui a cópia congelada do original, que
   precisa continuar exatamente como era.
9. **Commits pequenos, com prefixo.** `test:`, `refactor:`, `fix:`, `docs:` e
   `chore:` separam o que é mudança de estrutura, correção, teste e
   documentação, e depois de cada commit a suíte inteira foi executada.

## USO DE INTELIGÊNCIA ARTIFICIAL

- **Ferramenta utilizada:** Claude Code (modelo Claude Opus 5.5, da Anthropic).
- **Finalidade:** a IA foi usada como apoio em duas frentes:
  1. **Criação de mais casos de teste:** sugerir cenários que a suíte original
     não cobria (limites de 500, 800 e 1000; cupons PROMO20 e VIP50; teto de
     25%; frete expresso e fora do Sudeste; impostos por estado; pontos) e o
     teste de golden master.
  2. **Conferência do código entregue:** revisar o código e o repositório
     contra o enunciado, apontar regressões, pendências de entrega e
     inconsistências na documentação.
- **Exemplos de sugestões recebidas:**
  - *Aceita (testes):* criar um teste com o mesmo produto repetido 3 vezes. O
    teste revelou que a extração de `find_duplicate_products` tinha mudado o
    comportamento (`["Mouse", "Mouse", "Mouse"]` em vez de `["Mouse"]`), e a
    correção foi feita com `collections.Counter`.
  - *Aceita (testes):* criar o golden master, que compara 5000 pedidos
    aleatórios com uma cópia congelada do código original.
  - *Aceita (conferência):* ajustar a expectativa de `test_empty_cart` (frete
    R$ 20 em vez de 0) depois de confirmar no código original qual era o
    comportamento real.
  - *Modificada (conferência):* a primeira proposta de separação entre cálculo
    e impressão guardava os valores brutos num campo auxiliar do dicionário de
    retorno. Trocamos por uma dataclass `OrderTotals`, que deixa o contrato
    explícito.
  - *Rejeitada (conferência):* usar `sum()` para calcular o subtotal e o peso.
    O golden master mostrou diferença na última casa decimal do valor impresso
    (efeito da soma compensada do Python 3.12), então mantivemos o laço
    explícito.
- **A sugestão foi aceita, modificada ou rejeitada?** As três situações
  aconteceram, como descrito acima.
- **Como a equipe validou a solução?** (1) A suíte roda após cada commit;
  (2) os valores esperados dos testes novos foram conferidos no código original;
  (3) o golden master compara 5000 pedidos com o original; (4) as métricas foram
  medidas de novo com as ferramentas pedidas; (5) a equipe revisou o código e
  consegue explicar cada alteração.

## MELHORIAS FUTURAS (débito técnico que permanece)

1. **Estado global:** `ORDERS_PROCESSED` continua sendo uma lista global. O ideal
   é um repositório de pedidos injetado como dependência, mas isso mudaria a
   interface pública.
2. **`print` dentro do processamento:** o ideal é usar `logging`, ou deixar quem
   chama a função decidir como exibir o resumo.
3. **Dinheiro em `float`:** valores monetários deveriam usar `decimal.Decimal`
   para evitar erros de arredondamento binário. A mudança exige alinhar o novo
   comportamento de arredondamento com o professor.
4. **Validação de entrada:** hoje `qty <= 0` é ignorada em silêncio e quantidade
   negativa reduz o peso (Ticket 1 resolveria isso com `ValueError`).
5. **Cupons sensíveis a maiúsculas e minúsculas** (Ticket 2).
6. **Dicionários sem tipo:** `customer` e `items` poderiam ser dataclasses com
   *type hints*, e o tipo de cliente poderia ser um `Enum`.
7. **Índice de manutenibilidade:** as constantes de regra de negócio poderiam ir
   para um módulo próprio de configuração, o que também facilitaria mudar regras
   sem mexer na lógica.

## RESUMO PARA A APRESENTAÇÃO

1. **Principal problema:** `process_order` fazia tudo numa função só, com
   complexidade 34, números mágicos e cálculo misturado com impressão e
   histórico global.
2. **Principais refatorações:** extrair funções, trocar números mágicos por
   constantes e condicionais por mapeamento, separar as regras de desconto,
   separar cálculo de efeitos colaterais e otimizar a busca de duplicados para
   O(n).
3. **Métrica que mais melhorou:** a complexidade da função principal, de E (34)
   para A (1). A cobertura foi de 83% para 100%, e os problemas do Ruff, de 4
   para 0.
4. **Como comprovamos que o comportamento foi preservado:** 50 testes com
   valores conferidos no original, mais o golden master, que compara 5000
   pedidos aleatórios (retorno, saída impressa e histórico) com uma cópia
   congelada do código original.
5. **Débito técnico que permanece:** estado global `ORDERS_PROCESSED`, `print`
   no processamento e dinheiro representado em `float`.

## HISTÓRICO DE COMMITS

Histórico em ordem cronológica, do mais antigo para o mais recente. Os commits
de refatoração, teste, correção e documentação estão separados e usam os
prefixos sugeridos na atividade (`refactor:`, `test:`, `fix:`, `docs:`,
`chore:`). Os sete primeiros commits (até `a88772b`) vêm do repositório base
fornecido pelo professor. O commit deste README vem logo depois do último da lista.

```
a193d8a Add order processing functionality in legacy_checkout.py
41c3d03 Create test
9cd6f4c Add order processing functionality in legacy_checkout.py
b819b32 Delete src/test
5191755 Delete legacy_checkout.py
70d0a01 Implement tests for order processing
a88772b Create BASELINE - NÃO ALTERAR
934042d Apenas subindo a atividade
06ebf17 informações iniciais
9e5641b refatorei o duplicados
ab64f8b Refatoração e novo teste de múltiplos itens
d8211c9 Novo teste para nenhum item no pedido e comentários
78321c3 chore: adiciona .gitignore e requirements-dev.txt e remove arquivos .pyc
9a9a6f5 docs: registra baseline de métricas do código original
7b7351c fix: lista cada produto duplicado apenas uma vez
40c1467 test: adiciona testes de caracterização das regras de negócio
a546837 refactor: substitui números e strings mágicas por constantes
f8dc60f refactor: separa regras de desconto e simplifica condicionais
9b31004 refactor: separa cálculo, registro e impressão do pedido
84dacf8 test: adiciona golden master comparando com o código original
cbf54b8 test: adiciona testes unitários das funções extraídas
1eeaba7 docs: registra métricas depois da refatoração
bf9c405 test: corrige expectativa do teste de carrinho vazio
b9b0573 docs: atualiza contagem de testes no relatório de métricas
```
