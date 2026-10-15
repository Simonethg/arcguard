# ArcGuard GitHub Action

Composite action. En la raíz del repositorio se usa `uses: Simonethg/arcguard@v0`. Este directorio es el mismo manifiesto para `uses: Simonethg/arcguard/action@v0`.

Composite action. At the repository root the usage is `uses: Simonethg/arcguard@v0`. This directory is the same manifest for `uses: Simonethg/arcguard/action@v0`.

ArcGuard no certifica seguridad y no reemplaza una auditoría. Solo Arc testnet.

ArcGuard does not certify security and does not replace an audit. Arc testnet only.

## Qué hace / What it does

1. Instala `arcguard` desde el checkout de la Action, o desde PyPI si se pasa `version`.
2. Ejecuta `arcaudit scan`.
3. Si el CLI documenta `--format sarif`, sube ese SARIF a Code Scanning.
4. Si el CLI todavía no emite SARIF (el scaffold sale con código 2), corre igual `arcaudit scan` y escribe el SARIF con reglas de texto. Esas reglas no son el plugin de Slither.
5. Comenta el pull request en español e inglés, actualizando el comentario anterior de la misma ruta.
6. Falla el job cuando hay hallazgos del nivel `fail-on` o más alto.

1. Installs `arcguard` from the Action checkout, or from PyPI when `version` is set.
2. Runs `arcaudit scan`.
3. If the CLI documents `--format sarif`, that SARIF is uploaded to Code Scanning.
4. If the CLI does not emit SARIF yet (the scaffold exits 2), it still runs `arcaudit scan` and writes SARIF from text rules. Those rules are not the Slither plugin.
5. Comments on the pull request in Spanish and English, replacing the previous comment for the same path.
6. Fails the job when a finding is at or above `fail-on`.

Contrato que el CLI puede implementar después / CLI contract a later release can implement:

```text
arcaudit scan <path> --format sarif --output <file.sarif>
arcaudit scan <path> --format sarif --output <file.sarif> --markdown-output <file.md>
```

Códigos del CLI / CLI status codes: `0` sin hallazgos que fallen, `1` con hallazgos, `2` error. La Action aplica `fail-on` sobre el SARIF.

## Permisos / Permissions

| Permiso / Permission | Cuándo / When |
| --- | --- |
| `contents: read` | Siempre / Always |
| `actions: read` | Repositorio privado, para descargar actions / Private repository, to download actions |
| `security-events: write` | `upload-sarif: true` |
| `pull-requests: write` | `comment: true` |

El token del comentario es `github.token`. No commitear credenciales. Un secreto de CI, si hace falta, se declara en GitHub Secrets.

The comment token is `github.token`. Do not commit credentials. A CI secret, if one is required, is declared in GitHub Secrets.

## Inputs

| Input | Default | Rol / Role |
| --- | --- | --- |
| `path` | `.` | Archivo o directorio / File or directory |
| `fail-on` | `high` | `none`, `info`, `low`, `medium`, `high` |
| `comment` | `true` | Resumen en el PR / PR summary |
| `upload-sarif` | `true` | Code Scanning |
| `ignore` | vacío / empty | Rutas relativas, una por línea / Relative paths, one per line |
| `sarif-file` | `arcguard.sarif` | Salida / Output |
| `sarif-category` | `arcguard` | Categoría distinta si hay varios uploads / Distinct category when several jobs upload |
| `python-version` | `3.12` | Intérprete del install / Interpreter for the install |
| `version` | vacío / empty | Versión de PyPI. Vacío instala este checkout / PyPI version. Empty installs this checkout |
| `token` | `github.token` | Solo el comentario / Comment only |

## Fixtures

[`fixtures/vulnerable`](fixtures/vulnerable) tiene que fallar. [`fixtures/fixed`](fixtures/fixed) tiene que pasar. No desplegar.

[`fixtures/vulnerable`](fixtures/vulnerable) must fail. [`fixtures/fixed`](fixtures/fixed) must pass. Do not deploy.

## Fuentes / Sources

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
