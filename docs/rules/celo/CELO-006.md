# CELO-006 `feecurrency-assumed-honored`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-006/` (vulnerable + fixed)

## Español

MetaMask y otras wallets inyectadas descartan `feeCurrency` y cobran en CELO; MiniPay puede reemplazar la moneda elegida por la app. Una UI que promete "pagás la comisión en USDC" puede dejar al usuario sin CELO para gas o mostrar un costo falso.

**Qué marca:** archivos que usan `feeCurrency` con una wallet inyectada (`window.ethereum`, MetaMask, `injected()`) sin detectar `isMiniPay` ni verificar la moneda realmente usada.

**Dirección del arreglo:** detectar la wallet, mandar `feeCurrency` solo donde se respeta y verificar la tx resultante.

## English

MetaMask and other injected wallets drop `feeCurrency` and charge CELO; MiniPay may replace the app's choice. A UI that promises "you pay the fee in USDC" can leave users without CELO for gas or show a false cost.

**What it flags:** files that use `feeCurrency` with an injected wallet (`window.ethereum`, MetaMask, `injected()`) without checking `isMiniPay` or verifying the fee currency actually used.

**Fix direction:** detect the wallet, send `feeCurrency` only where honored, and verify the resulting tx.

## Fuentes / Sources

- [Fee abstraction overview — wallet support](https://docs.celo.org/build/fee-abstraction/overview)
- [MiniPay / Mini Apps overview](https://docs.celo.org/build/mini-apps/overview)
