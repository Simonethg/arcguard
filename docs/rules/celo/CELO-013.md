# CELO-013 `deprecated-tx-types`

**Severidad / Severity:** Media / Medium

**Estado / Status:** heurística de texto en `detectors/celo/` (no conectada a Slither ni a `arcaudit scan`). / text heuristic in `detectors/celo/` (not wired into Slither or `arcaudit scan`).

**Corpus:** `corpus/celo/CELO-013/` (vulnerable + fixed)

## Español

Las tx tipo 0 con `feeCurrency` y el tipo 124 (CIP-42) quedaron deprecadas. Para fee abstraction Celo usa CIP-64 (tipo 123).

**Qué marca:** `type: 0x7c|124|cip42`, o `type: legacy|0` cerca de `feeCurrency`.

**Dirección del arreglo:** usar `type: "cip64"` (viem) / tipo 123.

## English

Type 0 txs with `feeCurrency` and type 124 (CIP-42) are deprecated. Celo uses CIP-64 (type 123) for fee abstraction.

**What it flags:** `type: 0x7c|124|cip42`, or `type: legacy|0` near `feeCurrency`.

**Fix direction:** use `type: "cip64"` (viem) / type 123.

## Fuentes / Sources

- [Celo L1 → L2 changes — transaction types](https://docs.celo.org/learn/celo-l1)
- [Migrate from Ethereum — transaction types](https://docs.celo.org/build/tools/overview/migrate/from-ethereum)
