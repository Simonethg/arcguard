# ARC-OFF-1 `max-fee-below-floor`

<!-- Replaced the es/en stub (problem and fix direction only, no example, no pt-BR, no section anchor). Source of copy: web/content/rules.ts -->

**Severidad / Severity / Severidade:** Alta / High / Alta

**Estado / Status:** Implementada. Corre con `arcaudit scan` desde `offchain/` (no es un detector de Slither). / Implemented. It runs with `arcaudit scan` from `offchain/` (it is not a Slither detector). / Implementada. Roda com `arcaudit scan` a partir de `offchain/` (não é um detector do Slither).

Fuentes de la regla / Rule sources:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

## Español

### Problema / Problem / Problema

Arc descarta en silencio una transacción cuyo maxFeePerGas está por debajo de 20 Gwei. No hay recibo de error y no entra en un bloque. El fallo vive en scripts de TypeScript o JavaScript y en la config de Foundry, no en el bytecode. Reutilizar el gas price de una red Ethereum local suele quedar debajo del piso.

### Ejemplo vulnerable / Vulnerable example / Exemplo vulnerável

Fragmento ilustrativo. 1 Gwei está debajo del piso de 20 Gwei.

```typescript
// WRONG on Arc: 1 Gwei is below the 20 Gwei floor.
// The mempool drops the transaction. There is no error receipt.
const maxFeePerGas = 1_000_000_000n;
```

### Arreglo / Fix / Correção

UsdcUnits no aplica: esto es el tope de fee, no una mezcla de decimales del saldo. Fijá maxFeePerGas en al menos 20 Gwei para Arc testnet (chain 5042002).

```typescript
// Arc testnet, chain 5042002. At least 20 Gwei.
// https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior
const maxFeePerGas = 20_000_000_000n;
```

UsdcUnits no aplica a esta regla.

### Documentación / Documentation / Documentação

- [EVM differences — Fee market and block behavior](https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior)
- [Porting contracts to Arc — Steps](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc#steps)

## English

### Problema / Problem / Problema

Arc silently drops a transaction whose maxFeePerGas is below 20 Gwei. There is no error receipt and it never appears in a block. The failure lives in TypeScript or JavaScript scripts and in Foundry config, not in bytecode. Reusing the gas price from a local Ethereum network usually lands below the floor.

### Ejemplo vulnerable / Vulnerable example / Exemplo vulnerável

Illustrative snippet. 1 Gwei is below the 20 Gwei floor.

```typescript
// WRONG on Arc: 1 Gwei is below the 20 Gwei floor.
// The mempool drops the transaction. There is no error receipt.
const maxFeePerGas = 1_000_000_000n;
```

### Arreglo / Fix / Correção

UsdcUnits does not apply: this is the fee cap, not a balance-decimal mix. Set maxFeePerGas to at least 20 Gwei for Arc testnet (chain 5042002).

```typescript
// Arc testnet, chain 5042002. At least 20 Gwei.
// https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior
const maxFeePerGas = 20_000_000_000n;
```

UsdcUnits does not apply to this rule.

### Documentación / Documentation / Documentação

- [EVM differences — Fee market and block behavior](https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior)
- [Porting contracts to Arc — Steps](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc#steps)

## Português (Brasil)

### Problema / Problem / Problema

A Arc descarta em silêncio uma transação cujo maxFeePerGas está abaixo de 20 Gwei. Não há recibo de erro e ela não entra em um bloco. A falha vive em scripts TypeScript ou JavaScript e na config do Foundry, não no bytecode. Reutilizar o gas price de uma rede Ethereum local costuma ficar abaixo do piso.

### Ejemplo vulnerable / Vulnerable example / Exemplo vulnerável

Trecho ilustrativo. 1 Gwei está abaixo do piso de 20 Gwei.

```typescript
// WRONG on Arc: 1 Gwei is below the 20 Gwei floor.
// The mempool drops the transaction. There is no error receipt.
const maxFeePerGas = 1_000_000_000n;
```

### Arreglo / Fix / Correção

UsdcUnits não se aplica: isto é o teto da fee, não uma mistura de casas do saldo. Defina maxFeePerGas em pelo menos 20 Gwei para a Arc testnet (chain 5042002).

```typescript
// Arc testnet, chain 5042002. At least 20 Gwei.
// https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior
const maxFeePerGas = 20_000_000_000n;
```

UsdcUnits não se aplica a esta regra.

### Documentación / Documentation / Documentação

- [EVM differences — Fee market and block behavior](https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior)
- [Porting contracts to Arc — Steps](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc#steps)
