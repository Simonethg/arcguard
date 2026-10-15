# Reglas ArcGuard / ArcGuard rules

Estas páginas describen las reglas v0.1. Los detectores todavía no corren: el plugin de Slither devuelve listas vacías y `arcaudit scan` no emite un reporte.

These pages describe the v0.1 rules. Detectors do not run yet: the Slither plugin returns empty lists and `arcaudit scan` does not emit a report.

ArcGuard no certifica seguridad y no reemplaza una auditoría. Solo Arc testnet.

ArcGuard does not certify security and does not replace an audit. Arc testnet only.

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
