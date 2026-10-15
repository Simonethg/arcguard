# Evidencia de transacciones fallidas

Solo Arc testnet.

| Campo | Valor |
|---|---|
| Chain id | `5042002` |
| RPC | `https://rpc.testnet.arc.io` |
| Explorador | `https://explorer.testnet.arc.io` (antes `https://testnet.arcscan.app`, hoy redirige) |
| USDC ERC-20 | `0x3600000000000000000000000000000000000000` (6 decimales) |
| Piso de `maxFeePerGas` | 20 gwei. Por debajo, el mempool descarta la tx sin recibo. |

No hay clave en este repositorio. `scripts/run-testnet-evidence.sh` la lee de `ARC_TESTNET_PRIVATE_KEY` (entorno o secreto de CI) y se niega a correr contra cualquier chain id distinto de `5042002`. No imprime la variable. Si no está definida, no envía nada.

## Cómo reproducir

```bash
cp .env.example .env
# Poner la clave de testnet en .env o exportarla. No la commitees.
bash scripts/run-testnet-evidence.sh
```

El script manda 1 wei nativo, con `--gas-price 20gwei`, a:

1. `address(0)` — ARC-005. En Arc revierte con `Zero address not allowed` y el recibo queda con status 0.
2. `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` — dirección blocklisted publicada en la doc de direcciones de Arc. Una transferencia de valor hacia ella revierte en testnet. En `arc-anvil --network arc` local esa dirección no está blocklisted: el mismo envío allí se mina con status 1. No uses el anvil local como prueba de blocklist.

La salida queda en `evidence/last-run.txt` (gitignored). De ahí se copia solo el hash y el status.

## Cómo registrar el hash

1. Confirmá que el status es fallido (`0x0`) y que el chain id de la RPC era `5042002`.
2. Abrí `https://explorer.testnet.arc.io/tx/<hash>`.
3. Reemplazá el placeholder de la tabla. No pegues la clave, ni el JSON completo del recibo, ni un volcado que incluya inputs de firma.

Un fork de solo lectura (`bash scripts/run-testnet-fork.sh`) también muestra el revert de `address(0)`, `decimals() == 6` y `PREVRANDAO == 0`, pero no produce un hash en el explorador. El hash solo sale de la transacción enviada.

## Hashes

Corrida real en Arc testnet (chain id `5042002`) del 15/10/2026, con `scripts/run-testnet-evidence.sh` y `arc-forge create`. Gasto total aprox. 0,048 USDC de testnet.

| Regla | Qué falló | Status | Tx hash | Explorador |
|---|---|---|---|---|
| ARC-005 | Valor nativo (1 wei) a `address(0)`. Motivo: `Zero address not allowed`. | fallida (`0x0`) | [`0xf762dd4c…`](https://explorer.testnet.arc.io/tx/0xf762dd4c31f732d74357e9a53901a6e2577525e88980ef638263b934920d1130) | [explorer](https://explorer.testnet.arc.io/tx/0xf762dd4c31f732d74357e9a53901a6e2577525e88980ef638263b934920d1130) |
| ARC-006 | Valor nativo a la dirección blocklisted `0x7099…79C8`. | rechazada por la RPC (`-32000: Blocked address`) | sin hash: no entra al mempool | — |

ARC-006 no deja hash: la RPC de testnet rechaza el envío antes de aceptarlo, así que no hay recibo ni entrada en el explorador. El script ahora fuerza `--gas-limit` (la estimación de gas revierte antes de enviar) y registra el rechazo sin abortar.

### Deploys de los contratos del corpus

Deploys exitosos (status `0x1`) de `src/vulnerable/` y `src/fixed/` en Arc testnet. Prueban que compilan y se despliegan en Arc; las fallas de ejecución están en los tests y en la tabla de arriba.

| Regla | Contrato | Dirección | Tx hash |
|---|---|---|---|
| ARC-001 | Vulnerable | [`0x1cAfb1de43715961f0401EA6aE01161d0BE1e3aF`](https://explorer.testnet.arc.io/address/0x1cAfb1de43715961f0401EA6aE01161d0BE1e3aF) | [`0xd90620b7…`](https://explorer.testnet.arc.io/tx/0xd90620b7ec4c88c19e160bfce839aa3b2dab006ab1941c5d7af20b5cb74c7b7c) |
| ARC-002 | Vulnerable | [`0xAED265f70439be42A65189d9D838F57863dd4B8a`](https://explorer.testnet.arc.io/address/0xAED265f70439be42A65189d9D838F57863dd4B8a) | [`0x34b7b4eb…`](https://explorer.testnet.arc.io/tx/0x34b7b4ebeebf2e162c7949dd9ff3fa084f6f7c6d0d4b641d294c6f8003df607d) |
| ARC-003 | Vulnerable | [`0xB9A216Eb266f76F230e3504e26B795e5CC8a89c5`](https://explorer.testnet.arc.io/address/0xB9A216Eb266f76F230e3504e26B795e5CC8a89c5) | [`0x44e8972d…`](https://explorer.testnet.arc.io/tx/0x44e8972d5fa423e69c992a6cde23b95c63946079c0f68beeb21d968587ca293b) |
| ARC-004 | Vulnerable | [`0x9504E81b0DE5007d85a8945eB025C1f5c2Ed04BE`](https://explorer.testnet.arc.io/address/0x9504E81b0DE5007d85a8945eB025C1f5c2Ed04BE) | [`0xb280c0fa…`](https://explorer.testnet.arc.io/tx/0xb280c0faa1198c916e0856ab28d86db01612da645091e586152f771c358c30f6) |
| ARC-005 | Vulnerable | [`0x6CD482cbaed065BAE4111aC5879C6DB35f7231bE`](https://explorer.testnet.arc.io/address/0x6CD482cbaed065BAE4111aC5879C6DB35f7231bE) | [`0x0cd7cddd…`](https://explorer.testnet.arc.io/tx/0x0cd7cddd87f868242e05e376319173c2441dbd40e2e448c06b4ac154308b561a) |
| ARC-006 | Vulnerable | [`0x2Cd59D07E154BDDEa8b3e2aecd63f6baa000b5E2`](https://explorer.testnet.arc.io/address/0x2Cd59D07E154BDDEa8b3e2aecd63f6baa000b5E2) | [`0x35b10677…`](https://explorer.testnet.arc.io/tx/0x35b106770c68374c8288c507bf016a11a48ae2b018068149b49fba3ea675e772) |
| ARC-007 | Vulnerable | [`0x57f2a277cC0fD506704558656D9A537461F485f4`](https://explorer.testnet.arc.io/address/0x57f2a277cC0fD506704558656D9A537461F485f4) | [`0xa24298c1…`](https://explorer.testnet.arc.io/tx/0xa24298c14cbee1655fe7f11f9eedde73574f97cf9aee1868f5ae3dd97b8ea427) |
| ARC-008 | Vulnerable | [`0x8451628eF49a160073e844fe8EFe28dae70f4581`](https://explorer.testnet.arc.io/address/0x8451628eF49a160073e844fe8EFe28dae70f4581) | [`0xbda77f3e…`](https://explorer.testnet.arc.io/tx/0xbda77f3eacddcfa2a03a1944cbb3c0ab78280f2b54869b86856177d70e0c7da0) |
| ARC-001 | Fixed | [`0xEBF6A05F819eDF91Cdf4AbAc9Ade4781410D8d7c`](https://explorer.testnet.arc.io/address/0xEBF6A05F819eDF91Cdf4AbAc9Ade4781410D8d7c) | [`0x1f2bf766…`](https://explorer.testnet.arc.io/tx/0x1f2bf766ae5ff88aeb7f7b18b3e86dfed5aef1e16088d7ecd58da8922a447599) |
| ARC-002 | Fixed | [`0x52f1e8A112194B53D0fA7dEf66C8852EEAE90c1b`](https://explorer.testnet.arc.io/address/0x52f1e8A112194B53D0fA7dEf66C8852EEAE90c1b) | [`0xb49c2954…`](https://explorer.testnet.arc.io/tx/0xb49c2954f4f7e39f27c3adf2bda958fae9322f57fb70c3a276e170ee20d6aa3a) |
| ARC-003 | Fixed | [`0xfa35d8FFf786Ca7FF92FFC30dC900a828391dC47`](https://explorer.testnet.arc.io/address/0xfa35d8FFf786Ca7FF92FFC30dC900a828391dC47) | [`0xb23b8635…`](https://explorer.testnet.arc.io/tx/0xb23b8635e09c68ddd2ae691e0be12017db43f6282545865ed9424cbd5e37e3e5) |
| ARC-004 | Fixed | [`0x70B936a3c83D38eDaB948AD0dA01f27Ee96Cb7FF`](https://explorer.testnet.arc.io/address/0x70B936a3c83D38eDaB948AD0dA01f27Ee96Cb7FF) | [`0x452c84c3…`](https://explorer.testnet.arc.io/tx/0x452c84c3844ffca604398b2989357bcd7afeb44f571b54d8fe9423849f9f7fc5) |
| ARC-005 | Fixed | [`0x31be329E3930Dd3Ec5539273900D925629641074`](https://explorer.testnet.arc.io/address/0x31be329E3930Dd3Ec5539273900D925629641074) | [`0x24cb0abe…`](https://explorer.testnet.arc.io/tx/0x24cb0abec2ab2b8be8e6825642208c55604d5355db2fdb9bd5e8eb8ae72745ba) |
| ARC-006 | Fixed | [`0x675d2dB25CCe7B992673C45197B86a72EAe55886`](https://explorer.testnet.arc.io/address/0x675d2dB25CCe7B992673C45197B86a72EAe55886) | [`0x77a48aa1…`](https://explorer.testnet.arc.io/tx/0x77a48aa1e2e4aefc3a4c803ee05ba1b9a8da76febac7b9de933e650ef46db2bd) |
| ARC-007 | Fixed | [`0xb224c01307b28d46981b45F2454131217D5ceCB5`](https://explorer.testnet.arc.io/address/0xb224c01307b28d46981b45F2454131217D5ceCB5) | [`0x05a48b26…`](https://explorer.testnet.arc.io/tx/0x05a48b26f19bf573ab8d0a34335f286d7a530d739971ae6c9026ef48cb8ac2ba) |
| ARC-008 | Fixed | [`0x1Ba8AA51348BFE7BC61dA07382eC396346A3677E`](https://explorer.testnet.arc.io/address/0x1Ba8AA51348BFE7BC61dA07382eC396346A3677E) | [`0x1feb5c84…`](https://explorer.testnet.arc.io/tx/0x1feb5c841a27958c3f886368cf0fa87f6b6ff3b7fb7ee578a146e032d08421ff) |

## Qué sí se observó sin clave

Estas comprobaciones no son hashes de testnet:

- Lectura pública de testnet: chain id `5042002`, `decimals()` de USDC igual a 6, base fee del último bloque en el piso de 20 gwei.
- `arc-forge test --network arc`: el envío con valor a `address(0)` revierte con `Zero address not allowed`; el envío de valor 0 a `address(0)` no revierte; `SELFDESTRUCT` hacia sí mismo con saldo revierte; `SELFDESTRUCT` hacia `address(0)` con saldo revierte con `Zero address not allowed`; un envío con valor, en la misma transacción, a una cuenta recién destruida devuelve falso con `Cannot increase the balance of selfdestructed account`.
- Fork de solo lectura de Arc testnet (chain id `5042002`): `block.prevrandao` y `block.difficulty` son 0, el base fee está en 20 gwei, y USDC responde `decimals() == 6`.
- `arc-anvil --network arc` reporta `"network": "arc"`, chain id `31337` (no es testnet) y base fee de 20 gwei. El predeploy de USDC responde `decimals() == 6`. En Arc Foundry v0.8.0-2, incluso con `--hardfork arc:zero8`, `PREVRANDAO` en ese nodo local no es 0. La prueba de la regla ARC-008 es el fork de testnet, no el anvil local.
