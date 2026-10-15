# CELO-012 `random-contract`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (no conectada a Slither ni a `arcaudit scan`). / text heuristic in `detectors/celo/` (not wired into Slither or `arcaudit scan`).

**Corpus:** `corpus/celo/CELO-012/` (vulnerable + fixed)

## Español

El contrato `Random` de Celo quedó desactivado en L2. Hay que usar `PREVRANDAO` (que tampoco es aleatoriedad segura para valor en juego; preferir un VRF).

**Qué marca:** `IRandom`, búsqueda de `"Random"` en el Registry, `revealAndCommit`, `getBlockRandomness`.

**Dirección del arreglo:** `block.prevrandao` o un VRF.

## English

Celo's `Random` contract was deactivated on L2. Use `PREVRANDAO` (not secure randomness for value at stake either; prefer a VRF).

**What it flags:** `IRandom`, Registry lookups of `"Random"`, `revealAndCommit`, `getBlockRandomness`.

**Fix direction:** `block.prevrandao` or a VRF.

## Fuentes / Sources

- [Celo L1 → L2 changes — deactivated Random contract](https://docs.celo.org/learn/celo-l1)
