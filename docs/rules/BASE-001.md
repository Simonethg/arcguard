# BASE-001 `b20-union-weakens-blocklist`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

Desde Cobalt, `PolicyRegistry` combina de 2 a 4 políticas simples con `UNION` (OR) o `INTERSECT` (AND). Un `UNION` autoriza si **cualquier** hijo autoriza. Si un hijo es un blocklist de sanciones y otro es un allowlist de KYC, una cuenta con KYC que está sancionada igual pasa: el blocklist deja de proteger. La doc de Base arma "KYC y no sancionado" con `INTERSECT`.

**Qué marca:** `createCompositePolicy` con `UNION` (o el valor `2`) cuando la llamada o las líneas previas mencionan un blocklist, sanciones o una denylist.

**Dirección del arreglo:** usar `INTERSECT` cuando un hijo es una restricción (blocklist). Reservar `UNION` para sumar listas de admisión equivalentes.

## English

Since Cobalt, `PolicyRegistry` combines 2 to 4 simple policies under `UNION` (OR) or `INTERSECT` (AND). `UNION` authorizes when **any** child authorizes. If one child is a sanctions blocklist and another a KYC allowlist, a sanctioned account that is on the KYC list still passes, so the blocklist no longer protects anything. Base docs build "KYC and not sanctioned" with `INTERSECT`.

**What it flags:** `createCompositePolicy` with `UNION` (or the value `2`) when the call or the lines just before it mention a blocklist, sanctions, or a denylist.

**Fix direction:** use `INTERSECT` when a child is a restriction (blocklist). Keep `UNION` for combining equivalent admission lists.

## Fuentes / Sources

- [PolicyRegistry: Composite Policies (UNION / INTERSECT)](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-policyregistry-composite-policy)
- [B20 Policies — §4.2 Composite: KYC and sanctions](https://docs.base.org/specifications/b20/concepts/policies)
- [Cobalt overview](https://docs.base.org/upgrades/cobalt/overview)
