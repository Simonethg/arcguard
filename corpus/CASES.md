# Casos ARC-001 … ARC-008

Cada regla tiene un contrato en `src/vulnerable/` y la versión corregida en `src/fixed/`. El port de `NaiveEthereumPort` (scaffold-arc) es el caso de referencia de mezcla 18/6 y de doble conteo; `SafeCheckout` y `UsdcUnits` son el fix.

| ID | Regla | Vulnerable | Corregido | Falla que el test muestra |
|---|---|---|---|---|
| ARC-001 | `msg-value-vs-balanceof-mix` | `Arc001MsgValueMix.sol`, `NaiveCheckout.sol` | `Arc001MsgValueMix.sol`, `SafeCheckout.sol` | `1e6` wei nativo (no 1 USDC) pasa el `require` vulnerable. El fix escala con `UsdcUnits` y rechaza ese pago. |
| ARC-002 | `usdc-decimals-hardcoded` | `Arc002HardcodedDecimals.sol` | `Arc002HardcodedDecimals.sol` | El vulnerable exige `msg.value >= 1e6` y transfiere `10**18` por ERC-20. El fix exige `10^18` nativo y transfiere `10^6`. |
| ARC-003 | `native-erc20-dual-asset-pool` | `Arc003DualAssetPool.sol` | `Arc003DualAssetPool.sol` | El TVL vulnerable suma `address.balance` y `balanceOf`. El fix usa un solo reserve. |
| ARC-004 | `weth-pattern` | `Arc004WethPattern.sol` | `Arc004WethPattern.sol` | `deposit()` / `withdraw()` contra la constante WETH de Ethereum. El fix acredita USDC nativo sin wrapper. |
| ARC-005 | `value-to-zero-address` | `Arc005ValueToZero.sol` | `Arc005ValueToZero.sol` | `transfer` con valor a `address(0)` revierte `Zero address not allowed`. Valor 0 no revierte. El fix corta antes de enviar. |
| ARC-006 | `unchecked-native-send` | `Arc006UncheckedSend.sol` | `Arc006UncheckedSend.sol` | `call{value:}` y `send` a `address(0)` fallan y el vulnerable igual deja `recordedSuccess`. El fix revierte. |
| ARC-007 | `selfdestruct-moves-usdc` | `Arc007Selfdestruct.sol` | `Arc007Selfdestruct.sol` | `SELFDESTRUCT` a sí mismo o a `address(0)` con saldo revierte. Un pago posterior, en la misma tx, a la cuenta destruida falla. El fix retira con un call chequeado y sin `SELFDESTRUCT`. |
| ARC-008 | `prevrandao-randomness` | `Arc008Prevrandao.sol` | `Arc008Prevrandao.sol` | El contrato vulnerable lee `block.prevrandao` / `block.difficulty`. En un fork de Arc testnet esos valores son 0. `arc-anvil` de Arc Foundry v0.8.0-2 todavía no los fuerza a 0, así que esa aserción corre solo con chain id `5042002`. El fix recibe entropía externa. |

Fuentes citadas en cada archivo:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
