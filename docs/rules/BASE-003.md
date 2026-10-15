# BASE-003 `b20-seize-unguarded`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

`seizeWithMemo(from, to, amount, memo)` llegó con Cobalt y mueve el saldo de un holder sin allowance y **saltea las políticas de transferencia**. Lo protege `SEIZE_ROLE`. Si un contrato que tiene ese rol expone una función `public`/`external` que llama a `seizeWithMemo` sin control de acceso, cualquiera puede mover saldos ajenos. La doc también permite un memo `bytes32(0)`, pero entonces el registro onchain queda sin motivo.

**Qué marca:** funciones `public`/`external` que llegan a `seizeWithMemo` o a `SEIZE_ROLE` sin modificador `only*`, `hasRole` o `msg.sender ==`. También marca llamadas con memo `bytes32(0)`.

**Dirección del arreglo:** restringir quién puede ejecutar el seize (rol o multisig de compliance), exigir un memo no vacío y configurar `SEIZE_EXEMPT_POLICY` y `SEIZE_RECEIVER_POLICY` a propósito.

## English

`seizeWithMemo(from, to, amount, memo)` shipped with Cobalt. It moves a holder's balance without an allowance and **skips the transfer policies**. `SEIZE_ROLE` gates it. If a contract that holds that role exposes a `public`/`external` function that calls `seizeWithMemo` without access control, anyone can move other people's balances. The docs also allow a `bytes32(0)` memo, but then the onchain record carries no reason.

**What it flags:** `public`/`external` functions that reach `seizeWithMemo` or `SEIZE_ROLE` with no `only*` modifier, `hasRole`, or `msg.sender ==` check. It also flags calls with a `bytes32(0)` memo.

**Fix direction:** restrict who can trigger seize (a compliance role or multisig), require a non-empty memo, and set `SEIZE_EXEMPT_POLICY` and `SEIZE_RECEIVER_POLICY` deliberately.

## Fuentes / Sources

- [B20: Seize Functionality (Cobalt)](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-b20-seize)
- [Seize and Cancel Units](https://docs.base.org/build-on-base/issue-rwa/seize-and-cancel-units)
- [B20 Policies — SEIZE_EXEMPT_POLICY / SEIZE_RECEIVER_POLICY](https://docs.base.org/specifications/b20/concepts/policies)
