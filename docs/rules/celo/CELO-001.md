# CELO-001 `usdc-wrong-decimals`

**Severidad / Severity:** Crítica / Critical

**Estado / Status:** heurística de texto en `detectors/celo/` (no conectada a Slither ni a `arcaudit scan`). / text heuristic in `detectors/celo/` (not wired into Slither or `arcaudit scan`).

**Corpus:** `corpus/celo/CELO-001/` (vulnerable + fixed)

## Español

USDC, USD₮ y USA₮ en Celo tienen **6 decimales** (USDm tiene 18). Escalar un monto con `parseUnits(x, 18)`, `parseEther`, `1e18` o `10**18` manda 10¹² veces el monto o rompe la contabilidad.

**Qué marca:** una línea que escala a 18 decimales (`parseUnits(..., 18)`, `parseEther`, `formatEther`, `1e18`, `10**18`) y menciona USDC/USDT/USA₮ o una dirección (o constante) de esos tokens.

**Dirección del arreglo:** usar `parseUnits(x, 6)` o leer `decimals()` del token.

## English

USDC, USD₮ and USA₮ on Celo have **6 decimals** (USDm has 18). Scaling with `parseUnits(x, 18)`, `parseEther`, `1e18` or `10**18` sends 10¹² times the amount or breaks accounting.

**What it flags:** a line that scales to 18 decimals and mentions USDC/USDT/USA₮ or one of their addresses (or a constant holding it).

**Fix direction:** use `parseUnits(x, 6)` or read `decimals()` from the token.

## Fuentes / Sources

- [MiniPay / Mini Apps overview — supported stablecoins and decimals](https://docs.celo.org/build/mini-apps/overview)
- [Fee currency contracts — token addresses](https://docs.celo.org/build/tools/contracts/fee-currencies)
