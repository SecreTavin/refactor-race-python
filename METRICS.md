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
> é preciso passar o caminho completo do arquivo.

**Baseline ("Antes")**: código original do commit `70d0a01`, rodando a suíte de
testes original (4 testes), antes de qualquer intervenção da equipe.

## Comparação

| Indicador                          | Antes            | Depois |
|------------------------------------|------------------|--------|
| Testes passando                    | 4 / 4            |        |
| Cobertura de testes                | 83% (12 de 72 linhas sem cobertura) |  |
| Complexidade da função principal   | `process_order` — E (34) |  |
| Complexidade média                 | E (34,0) — 1 bloco |      |
| Índice de manutenibilidade         | A (51,69)        |        |
| Problemas identificados pelo Ruff  | 4 (3× SIM102, 1× PLR1730) |  |
| Quantidade de testes               | 4                |        |

## Saídas da baseline

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
