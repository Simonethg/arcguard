# CELO-003 `adapter-used-for-transfer`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (no conectada a Slither ni a `arcaudit scan`). / text heuristic in `detectors/celo/` (not wired into Slither or `arcaudit scan`).

**Corpus:** `corpus/celo/CELO-003/` (vulnerable + fixed)

## Español

El error inverso: usar la dirección del adapter en `transfer`, `transferFrom` o `approve`. El adapter solo sirve para el campo `feeCurrency`.

**Qué marca:** `transfer`/`transferFrom`/`approve` cerca (±250 caracteres) de una dirección de adapter o de una constante que la contiene.

**Dirección del arreglo:** transferir y aprobar siempre con la dirección del token.

## English

The reverse mistake: using the adapter address in `transfer`, `transferFrom` or `approve`. The adapter is only for the `feeCurrency` field.

**What it flags:** `transfer`/`transferFrom`/`approve` near (±250 chars) an adapter address or a constant holding it.

**Fix direction:** always transfer and approve with the token address.

## Fuentes / Sources

- [Using fee abstraction — adapters vs tokens](https://docs.celo.org/build/fee-abstraction/using-fee-abstraction)
- [Fee currency contracts](https://docs.celo.org/build/tools/contracts/fee-currencies)
