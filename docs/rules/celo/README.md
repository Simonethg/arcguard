# Reglas Celo / Celo rules

Heurísticas de texto en `detectors/celo/` (`arcguard.celo.scan_path`). Todavía **no** están conectadas a Slither ni a `arcaudit scan`. Todas citan docs.celo.org. / Text heuristics in `detectors/celo/` (`arcguard.celo.scan_path`), **not** yet wired into Slither or `arcaudit scan`. All cite docs.celo.org.

Un hallazgo es una pista para revisar, no prueba de un bug. ArcGuard no certifica seguridad ni reemplaza una auditoría. / A finding is a review hint, not proof of a bug. ArcGuard does not certify security or replace an audit.

| ID | Página / Page | Severidad / Severity |
| --- | --- | --- |
| CELO-001 | [usdc-wrong-decimals](CELO-001.md) | Crítica / Critical |
| CELO-002 | [feecurrency-token-not-adapter](CELO-002.md) | Alta / High |
| CELO-003 | [adapter-used-for-transfer](CELO-003.md) | Alta / High |
| CELO-006 | [feecurrency-assumed-honored](CELO-006.md) | Alta / High |
| CELO-008 | [celo-native-erc20-duality](CELO-008.md) | Alta / High |
| CELO-009 | [msgvalue-plus-erc20-double-count](CELO-009.md) | Alta / High |
| CELO-010 | [block-time-assumption](CELO-010.md) | Media / Medium |
| CELO-011 | [removed-precompiles](CELO-011.md) | Alta / High |
| CELO-012 | [random-contract](CELO-012.md) | Alta / High |
| CELO-013 | [deprecated-tx-types](CELO-013.md) | Media / Medium |

Pendientes de la propuesta (no implementadas aún) / Not implemented yet: CELO-004, 005, 007, 014, 015, 016.
