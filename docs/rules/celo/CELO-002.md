# CELO-002 `feecurrency-token-not-adapter`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-002/` (vulnerable + fixed)

## Español

Los tokens que no tienen 18 decimales (USDC, USD₮, USA₮) se habilitan para pagar gas a través de un **adapter** con otra dirección. Poner la dirección del token en `feeCurrency` hace que la tx sea rechazada.

**Qué marca:** `feeCurrency` cuyo valor es la dirección del token USDC/USDT/USA₮ (mainnet o Celo Sepolia) o una constante que la contiene.

**Dirección del arreglo:** usar la dirección del adapter (columna feeCurrency del FeeCurrencyDirectory).

## English

Non-18-decimal tokens (USDC, USD₮, USA₮) are allowlisted for gas through an **adapter** at a different address. Using the token address in `feeCurrency` makes the tx be rejected.

**What it flags:** `feeCurrency` set to the USDC/USDT/USA₮ token address (mainnet or Celo Sepolia) or a constant holding it.

**Fix direction:** use the adapter address (feeCurrency column of the FeeCurrencyDirectory).

## Fuentes / Sources

- [Fee currency contracts — feeCurrency vs token address](https://docs.celo.org/build/tools/contracts/fee-currencies)
- [Using fee abstraction — adapters](https://docs.celo.org/build/fee-abstraction/using-fee-abstraction)
