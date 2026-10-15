# Reglas ArcGuard / ArcGuard rules / Regras ArcGuard

Estas páginas reemplazan los stubs es/en del scaffold. Cada regla tiene el problema, un ejemplo vulnerable, el arreglo (UsdcUnits de scaffold-arc cuando aplica) y el enlace a la sección de docs.arc.io, en español, inglés y portugués de Brasil.

These pages replace the scaffold es/en stubs. Each rule has the problem, a vulnerable example, the fix (scaffold-arc UsdcUnits when it applies), and the docs.arc.io section link, in Spanish, English, and Brazilian Portuguese.

Estas páginas substituem os stubs es/en do scaffold. Cada regra tem o problema, um exemplo vulnerável, a correção (UsdcUnits do scaffold-arc quando se aplica) e o link da seção em docs.arc.io, em espanhol, inglês e português do Brasil.

ArcGuard no certifica seguridad y no reemplaza una auditoría. Solo Arc testnet (chain 5042002). ARC-001..ARC-008 corren con `slither --detect arc-...`. `arcaudit scan` todavía no emite un reporte. ARC-OFF-1 sigue sin detector.

ArcGuard does not certify security and does not replace an audit. Arc testnet only (chain 5042002). ARC-001..ARC-008 run with `slither --detect arc-...`. `arcaudit scan` does not emit a report yet. ARC-OFF-1 still has no detector.

O ArcGuard não certifica segurança e não substitui uma auditoria. Somente Arc testnet (chain 5042002). ARC-001..ARC-008 rodam com `slither --detect arc-...`. `arcaudit scan` ainda não emite um relatório. ARC-OFF-1 continua sem detector.

## Fuentes / Sources / Fontes

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

## Índice / Index / Índice

| ID | Página / Page / Página | Severidad / Severity / Severidade |
| --- | --- | --- |
| ARC-001 | [`msg-value-vs-balanceof-mix`](ARC-001.md) | Alta / High / Alta |
| ARC-002 | [`usdc-decimals-hardcoded`](ARC-002.md) | Alta / High / Alta |
| ARC-003 | [`native-erc20-dual-asset-pool`](ARC-003.md) | Alta / High / Alta |
| ARC-004 | [`weth-pattern`](ARC-004.md) | Media / Medium / Média |
| ARC-005 | [`value-to-zero-address`](ARC-005.md) | Alta / High / Alta |
| ARC-006 | [`unchecked-native-send`](ARC-006.md) | Media / Medium / Média |
| ARC-007 | [`selfdestruct-moves-usdc`](ARC-007.md) | Alta / High / Alta |
| ARC-008 | [`prevrandao-randomness`](ARC-008.md) | Alta / High / Alta |
| ARC-OFF-1 | [`max-fee-below-floor`](ARC-OFF-1.md) | Alta / High / Alta |
