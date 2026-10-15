# BASE-OFF-2 `builder-code-suffix-missing`

**Severidad / Severity:** Baja / Low

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

No es un bug de seguridad. Los Builder Codes (ERC-8021) se agregan como sufijo al calldata para atribuir la actividad a una app o agente. Sin el sufijo, la actividad no se atribuye y la app queda fuera de las analytics y de los programas basados en Builder Codes. La doc de grants de Base pide integrarlos como primer paso.

**Qué marca:** archivos TS/JS que configuran `base` o `baseSepolia` (o chainId 8453/84532) y hacen escrituras (`writeContract`, `sendTransaction`, `sendCalls`) sin `dataSuffix` ni `toDataSuffix`.

**Dirección del arreglo:** generar el sufijo con `Attribution.toDataSuffix` de `ox/erc8021` y pasarlo en cada escritura. La doc avisa que wagmi no aplica el `dataSuffix` de `createConfig` a los conectores.

## English

Not a safety bug. Builder Codes (ERC-8021) are appended to calldata to attribute activity to an app or agent. Without the suffix, activity is not attributed and the app misses analytics and Builder Code-based programs. Base's grant docs list integrating them as the first step.

**What it flags:** TS/JS files that configure `base` or `baseSepolia` (or chainId 8453/84532) and send writes (`writeContract`, `sendTransaction`, `sendCalls`) without `dataSuffix` or `toDataSuffix`.

**Fix direction:** build the suffix with `Attribution.toDataSuffix` from `ox/erc8021` and pass it on every write. The docs warn that wagmi does not apply the `createConfig` `dataSuffix` to connectors.

## Fuentes / Sources

- [Base Builder Codes](https://docs.base.org/specifications/builder-codes/overview)
- [Builder Codes for App Developers](https://docs.base.org/specifications/builder-codes/for-app-developers)
- [Builders — grants eligibility](https://docs.base.org/get-started/builders)
