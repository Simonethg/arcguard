# Reglas ArcGuard / ArcGuard rules

Estas páginas describen las reglas v0.1. El motor es multichain (`arcguard.arc`, `arcguard.base`, `arcguard.celo`). ARC-OFF-1 ya corre en `arcaudit scan`. El plugin de Slither sigue vacío hasta que entren los detectores de Solidity. Las pruebas en vivo se quedan en testnets públicas.

These pages describe the v0.1 rules. The engine is multichain (`arcguard.arc`, `arcguard.base`, `arcguard.celo`). ARC-OFF-1 already runs in `arcaudit scan`. The Slither plugin stays empty until the Solidity detectors land. Live checks stay on public testnets.

ArcGuard no certifica seguridad y no reemplaza una auditoría.

ArcGuard does not certify security and does not replace an audit.

## Fuentes / Sources

- [EVM differences](https://docs.arc.io/arc/references/evm-differences)
- [Porting contracts to Arc](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc)
- [Arc compatibility guide for existing EVM apps](https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps)

## Índice / Index

| ID | Página / Page | Severidad / Severity |
| --- | --- | --- |
| ARC-001 | [msg-value-vs-balanceof-mix](ARC-001.md) | Alta / High |
| ARC-002 | [usdc-decimals-hardcoded](ARC-002.md) | Alta / High |
| ARC-003 | [native-erc20-dual-asset-pool](ARC-003.md) | Alta / High |
| ARC-004 | [weth-pattern](ARC-004.md) | Media / Medium |
| ARC-005 | [value-to-zero-address](ARC-005.md) | Alta / High |
| ARC-006 | [unchecked-native-send](ARC-006.md) | Media / Medium |
| ARC-007 | [selfdestruct-moves-usdc](ARC-007.md) | Alta / High |
| ARC-008 | [prevrandao-randomness](ARC-008.md) | Alta / High |
| ARC-OFF-1 | [max-fee-below-floor](ARC-OFF-1.md) | Alta / High |
