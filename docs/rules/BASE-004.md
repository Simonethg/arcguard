# BASE-004 `validity-predicate-unsafe`

**Severidad / Severity:** Media / Medium

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

Las Validity Transactions (Cobalt) se incluyen solo cuando se cumplen ciertos predicados (`balance`, `storage`, `block_number`, `flashblock_index`). La doc avisa que un predicado no simula la transacción y que una transacción anterior puede cambiar el estado observado. Además: no hay que suponer que un slot en cero vuelve seguro un CREATE2, un proxy o un contrato sin inicializar; no hay que usar la posición de la transacción como aleatoriedad; y no hay que poner secretos en los predicados.

**Qué marca:** predicados `storage` con `op "="` y `value` cero, y predicados `flashblock_index` cerca de lógica de aleatoriedad (random, lottery, winner, seed).

**Dirección del arreglo:** dejar el chequeo crítico dentro del contrato llamado, verificar el layout de storage antes de usar un predicado `storage` y no usar la posición como fuente de aleatoriedad.

## English

Validity Transactions (Cobalt) are included only when predicates (`balance`, `storage`, `block_number`, `flashblock_index`) match. The docs warn that a predicate does not simulate the transaction and that an earlier transaction can change the watched state. They also say not to assume a zero slot makes a CREATE2 address, proxy, or uninitialized contract safe, not to use transaction placement as randomness, and not to put secrets in predicates.

**What it flags:** `storage` predicates with `op "="` and a zero `value`, and `flashblock_index` predicates near randomness logic (random, lottery, winner, seed).

**Fix direction:** keep the critical check inside the called contract, verify the storage layout before using a `storage` predicate, and do not use placement as a randomness source.

## Fuentes / Sources

- [Predicates and Safety](https://docs.base.org/specifications/build-transaction/predicates-and-safety)
- [Validity Transactions (Cobalt)](https://docs.base.org/upgrades/cobalt/validity-transactions)
