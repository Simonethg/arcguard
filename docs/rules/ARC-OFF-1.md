# ARC-OFF-1 `max-fee-below-floor`

**Severidad / Severity:** Alta / High

**Estado / Status:** documentada; el chequeo off-chain no está implementado. / documented; the off-chain check is not implemented.

## Español

Arc descarta en silencio una transacción cuyo `maxFeePerGas` está por debajo del piso de 20 Gwei. El fallo vive en scripts TypeScript o JavaScript y en la config de Foundry, no en el bytecode.

**Qué debe marcar:** asignaciones de `maxFeePerGas` (y equivalentes en `foundry.toml` o en clientes de viem/ethers) con un valor menor a 20 Gwei.

**Dirección del arreglo:** fijar el tope de fee en al menos 20 Gwei en la config de Arc testnet. No reutilizar el gas price de una red Ethereum local.

## English

Arc silently drops a transaction whose `maxFeePerGas` is below the 20 Gwei floor. The failure lives in TypeScript or JavaScript scripts and in Foundry config, not in bytecode.

**What to flag:** `maxFeePerGas` assignments (and the Foundry or viem/ethers equivalents) set below 20 Gwei.

**Fix direction:** set the fee cap to at least 20 Gwei in the Arc testnet config. Do not reuse the gas price from a local Ethereum network.

## Fuentes / Sources

- [EVM differences — fee market](https://docs.arc.io/arc/references/evm-differences)
- [Porting contracts to Arc](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc)
- [Arc compatibility guide for existing EVM apps](https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps)
