# BASE-002 `b20-policy-id-unchecked`

**Severidad / Severity:** Media / Medium

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

Según la spec de Cobalt, un ID de `INTERSECT` bien formado pero nunca creado no tiene hijos y devuelve `true`: se comporta como `ALWAYS_ALLOW`. La doc pide llamar a `policyExists(policyId)` antes de guardar un ID. Un ID que llega desde la config o desde un parámetro sin verificar puede dejar un scope sin control.

**Qué marca:** `updatePolicy` o `updateComposite` en un archivo que nunca llama a `policyExists`.

**Dirección del arreglo:** verificar con `policyExists` antes de bindear o guardar el ID, y fallar cerrado si no existe.

## English

Per the Cobalt spec, a well-formed but never-created `INTERSECT` ID has no children and returns `true`, so it behaves like `ALWAYS_ALLOW`. The docs say to call `policyExists(policyId)` before storing an ID. An ID that comes from config or an unchecked parameter can leave a scope with no control.

**What it flags:** `updatePolicy` or `updateComposite` in a file that never calls `policyExists`.

**Fix direction:** check with `policyExists` before binding or storing the ID, and fail closed when it does not exist.

## Fuentes / Sources

- [PolicyRegistry: Composite Policies — evaluation of never-created IDs](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-policyregistry-composite-policy)
- [B20 Policies — built-in sentinels and `updatePolicy`](https://docs.base.org/specifications/b20/concepts/policies)
