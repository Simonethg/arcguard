/**
 * Canonical copy for ArcGuard rules ARC-001..008 and ARC-OFF-1.
 *
 * Official sources for every rule:
 * - https://docs.arc.io/arc/references/evm-differences
 * - https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
 * - https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
 *
 * UsdcUnits is the recommended scale fix from scaffold-arc:
 * https://github.com/Simonethg/scaffold-arc/blob/main/packages/foundry/src/UsdcUnits.sol
 * NaiveEthereumPort is the reference vulnerable case:
 * https://github.com/Simonethg/scaffold-arc/blob/main/packages/foundry/src/examples/NaiveEthereumPort.sol
 *
 * Arc testnet only (chain 5042002). These pages do not certify a contract.
 */

export const LOCALES = ["es", "en", "pt-BR"] as const;

export type Locale = (typeof LOCALES)[number];

export const RULE_IDS = [
  "ARC-001",
  "ARC-002",
  "ARC-003",
  "ARC-004",
  "ARC-005",
  "ARC-006",
  "ARC-007",
  "ARC-008",
  "ARC-OFF-1",
] as const;

export type RuleId = (typeof RULE_IDS)[number];

export type Severity = "high" | "medium";

export type DocLink = {
  url: string;
  label: Record<Locale, string>;
};

export type CodeSample = {
  language: "solidity" | "typescript";
  code: string;
};

export type RuleCopy = {
  name: string;
  problem: string;
  vulnerableCaption: string;
  fixCaption: string;
  findingSummary: string;
  findingDetail: string;
};

export type Rule = {
  id: RuleId;
  slug: string;
  severity: Severity;
  /** True when scaffold-arc UsdcUnits is the recommended fix. */
  usdcUnitsApplies: boolean;
  docs: DocLink[];
  vulnerable: CodeSample;
  fix: CodeSample;
  copy: Record<Locale, RuleCopy>;
};

export const USDC_UNITS_URL =
  "https://github.com/Simonethg/scaffold-arc/blob/main/packages/foundry/src/UsdcUnits.sol";

export const NAIVE_PORT_URL =
  "https://github.com/Simonethg/scaffold-arc/blob/main/packages/foundry/src/examples/NaiveEthereumPort.sol";

export const NAIVE_PORT_PATH = "packages/foundry/src/examples/NaiveEthereumPort.sol";

export const SOURCE_URLS = [
  "https://docs.arc.io/arc/references/evm-differences",
  "https://docs.arc.io/arc/tutorials/porting-contracts-to-arc",
  "https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps",
] as const;

const EVM = "https://docs.arc.io/arc/references/evm-differences";
const PORT = "https://docs.arc.io/arc/tutorials/porting-contracts-to-arc";

function lines(parts: string[]): string {
  return parts.join("\n");
}

function link(
  url: string,
  es: string,
  en: string,
  pt: string,
): DocLink {
  return { url, label: { es, en, "pt-BR": pt } };
}

export const RULES: Rule[] = [
  {
    id: "ARC-001",
    slug: "msg-value-vs-balanceof-mix",
    severity: "high",
    usdcUnitsApplies: true,
    docs: [
      link(
        `${EVM}#value-transfer-rules`,
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
      ),
      link(
        `${PORT}#:~:text=Audit%20balance%20and%20decimal%20assumptions`,
        "Porting contracts to Arc — Audit balance and decimal assumptions",
        "Porting contracts to Arc — Audit balance and decimal assumptions",
        "Porting contracts to Arc — Audit balance and decimal assumptions",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// Reference: NaiveEthereumPort.naiveValueCoversErc20 (scaffold-arc).",
        "// WRONG on Arc: msg.value is 18 decimals and the ERC-20 amount is 6.",
        "function naiveValueCoversErc20(uint256 msgValue, uint256 requiredErc20)",
        "    internal",
        "    pure",
        "    returns (bool)",
        "{",
        "    return msgValue >= requiredErc20;",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "import {UsdcUnits} from \"scaffold-arc/UsdcUnits.sol\";",
        "",
        "function valueCoversErc20(uint256 msgValue, uint256 requiredErc20)",
        "    internal",
        "    pure",
        "    returns (bool)",
        "{",
        "    return msgValue >= UsdcUnits.erc20ToNative(requiredErc20);",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "Mezcla de valor nativo y ERC-20",
        problem:
          "En Arc el gas nativo es USDC con 18 decimales. El mismo saldo, visto por el ERC-20, tiene 6. Comparar, sumar o restar msg.value o address.balance contra balanceOf o el monto de un transfer, sin escalar, mezcla dos unidades. La diferencia es exactamente 10 a la 12. Un pago que parece alcanzar puede ser un millón de veces más chico, o al revés.",
        vulnerableCaption:
          "Ejemplo vulnerable, publicado en NaiveEthereumPort de scaffold-arc (línea 14). No lo uses en producción.",
        fixCaption:
          "El arreglo recomendado es UsdcUnits.erc20ToNative de scaffold-arc: convierte el monto de 6 decimales a la unidad nativa de 18 antes de compararlo con msg.value.",
        findingSummary:
          "Se compara valor nativo (18 decimales) con un monto ERC-20 (6 decimales) sin convertir.",
        findingDetail:
          "En Arc las dos cifras no están en la misma unidad. Hay que escalar con UsdcUnits antes de comparar o transferir.",
      },
      en: {
        name: "Native value mixed with ERC-20",
        problem:
          "On Arc the native gas token is USDC with 18 decimals. The same balance, read through the ERC-20 interface, has 6 decimals. Comparing, adding, or subtracting msg.value or address.balance against balanceOf or a transfer amount, without scaling, mixes the two units. The raw integers differ by exactly 10 to the 12. A payment that looks sufficient can be a million times too small, or the other way around.",
        vulnerableCaption:
          "Vulnerable example, published in scaffold-arc NaiveEthereumPort (line 14). Do not use it in production.",
        fixCaption:
          "The recommended fix is scaffold-arc UsdcUnits.erc20ToNative: convert the 6-decimal amount into 18-decimal native units before comparing it with msg.value.",
        findingSummary:
          "Native value (18 decimals) is compared with an ERC-20 amount (6 decimals) without converting.",
        findingDetail:
          "On Arc those two numbers are not the same unit. Scale with UsdcUnits before comparing or transferring.",
      },
      "pt-BR": {
        name: "Valor nativo misturado com ERC-20",
        problem:
          "Na Arc o gás nativo é USDC com 18 casas decimais. O mesmo saldo, lido pela interface ERC-20, tem 6. Comparar, somar ou subtrair msg.value ou address.balance com balanceOf ou com o valor de um transfer, sem converter, mistura as duas unidades. A diferença é exatamente 10 elevado a 12. Um pagamento que parece suficiente pode ser um milhão de vezes menor, ou o contrário.",
        vulnerableCaption:
          "Exemplo vulnerável, publicado em NaiveEthereumPort do scaffold-arc (linha 14). Não use em produção.",
        fixCaption:
          "A correção recomendada é UsdcUnits.erc20ToNative do scaffold-arc: converte o valor de 6 casas para a unidade nativa de 18 antes de comparar com msg.value.",
        findingSummary:
          "Valor nativo (18 casas) é comparado com um valor ERC-20 (6 casas) sem conversão.",
        findingDetail:
          "Na Arc os dois números não estão na mesma unidade. Converta com UsdcUnits antes de comparar ou transferir.",
      },
    },
  },
  {
    id: "ARC-002",
    slug: "usdc-decimals-hardcoded",
    severity: "high",
    usdcUnitsApplies: true,
    docs: [
      link(
        `${EVM}#usdc-as-the-native-gas-token`,
        "EVM differences — USDC as the native gas token",
        "EVM differences — USDC as the native gas token",
        "EVM differences — USDC as the native gas token",
      ),
      link(
        `${PORT}#:~:text=Audit%20balance%20and%20decimal%20assumptions`,
        "Porting contracts to Arc — Audit balance and decimal assumptions",
        "Porting contracts to Arc — Audit balance and decimal assumptions",
        "Porting contracts to Arc — Audit balance and decimal assumptions",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// WRONG on Arc: 1e6 is one USDC on the ERC-20 view, not in msg.value.",
        "function needsOneUsdc() external payable {",
        "    require(msg.value >= 1e6, \"short\");",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "import {UsdcUnits} from \"scaffold-arc/UsdcUnits.sol\";",
        "",
        "function needsOneUsdc() external payable {",
        "    uint256 oneUsdcNative = UsdcUnits.erc20ToNative(1e6);",
        "    require(msg.value >= oneUsdcNative, \"short\");",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "Decimales fijos",
        problem:
          "Un literal pensado para Ethereum deja de describir el activo correcto en Arc. 1e6 es un USDC en la vista ERC-20, pero el valor nativo usa 18 decimales, así que 1e6 nativo es una fracción diminuta. Al revés, tratar un monto ERC-20 como si tuviera 18 decimales infla la cifra. decimals() aplicado al activo equivocado cae en el mismo error.",
        vulnerableCaption:
          "Fragmento ilustrativo. Supone 6 decimales sobre msg.value, que en Arc tiene 18.",
        fixCaption:
          "UsdcUnits.erc20ToNative(1e6) es un USDC entero en unidades nativas. No reutilices la constante del otro activo.",
        findingSummary:
          "Hay un supuesto fijo de 6 decimales sobre valor nativo, o de 18 sobre el ERC-20.",
        findingDetail:
          "En Arc el nativo tiene 18 decimales y el ERC-20 tiene 6. La constante tiene que ser la del activo que realmente se usa. UsdcUnits concentra ese factor.",
      },
      en: {
        name: "Hard-coded decimals",
        problem:
          "A literal written for Ethereum no longer describes the right asset on Arc. 1e6 is one USDC on the ERC-20 view, but native value uses 18 decimals, so 1e6 of native value is a tiny fraction. The reverse mistake, treating an ERC-20 amount as if it had 18 decimals, inflates the figure. decimals() applied to the wrong asset is the same bug.",
        vulnerableCaption:
          "Illustrative snippet. It assumes 6 decimals for msg.value, which has 18 decimals on Arc.",
        fixCaption:
          "UsdcUnits.erc20ToNative(1e6) is one whole USDC in native units. Do not reuse the other asset's constant.",
        findingSummary:
          "A fixed 6-decimal assumption is applied to native value, or an 18-decimal assumption to the ERC-20.",
        findingDetail:
          "On Arc native value has 18 decimals and the ERC-20 has 6. The constant has to match the asset actually in use. UsdcUnits holds that factor.",
      },
      "pt-BR": {
        name: "Casas decimais fixas",
        problem:
          "Um literal pensado para Ethereum deixa de descrever o ativo certo na Arc. 1e6 é um USDC na visão ERC-20, mas o valor nativo usa 18 casas, então 1e6 nativo é uma fração minúscula. O inverso, tratar um valor ERC-20 como se tivesse 18 casas, infla o número. decimals() aplicado ao ativo errado é o mesmo erro.",
        vulnerableCaption:
          "Trecho ilustrativo. Supõe 6 casas em msg.value, que na Arc tem 18.",
        fixCaption:
          "UsdcUnits.erc20ToNative(1e6) é um USDC inteiro em unidades nativas. Não reutilize a constante do outro ativo.",
        findingSummary:
          "Há uma suposição fixa de 6 casas no valor nativo, ou de 18 no ERC-20.",
        findingDetail:
          "Na Arc o nativo tem 18 casas e o ERC-20 tem 6. A constante tem de ser a do ativo que realmente está em uso. UsdcUnits concentra esse fator.",
      },
    },
  },
  {
    id: "ARC-003",
    slug: "native-erc20-dual-asset-pool",
    severity: "high",
    usdcUnitsApplies: true,
    docs: [
      link(
        `${EVM}#value-transfer-rules`,
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
      ),
      link(
        `${PORT}#:~:text=Don%27t%20pair%20%22native%22%20against%20the%20ERC-20`,
        "Porting contracts to Arc — do not pair native against the ERC-20",
        "Porting contracts to Arc — do not pair native against the ERC-20",
        "Porting contracts to Arc — do not pair native against the ERC-20",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// Reference: NaiveEthereumPort.naiveTotalBalance (scaffold-arc).",
        "// WRONG on Arc: the two views are one balance, not two assets.",
        "function naiveTotalBalance(uint256 nativeBalance, uint256 erc20Balance)",
        "    internal",
        "    pure",
        "    returns (uint256)",
        "{",
        "    return nativeBalance + erc20Balance;",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "import {UsdcUnits} from \"scaffold-arc/UsdcUnits.sol\";",
        "",
        "// One asset. Pick one view. Do not add them.",
        "function totalNative(uint256 nativeBalance) internal pure returns (uint256) {",
        "    return nativeBalance;",
        "}",
        "",
        "function totalErc20View(uint256 nativeBalance) internal pure returns (uint256) {",
        "    return UsdcUnits.nativeToErc20(nativeBalance);",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "USDC nativo y ERC-20 como dos activos",
        problem:
          "El USDC nativo y el USDC ERC-20 son el mismo saldo en dos representaciones, no un par. Un pool, un LTV o un oráculo que los suma doble-cuenta el dinero. Un pool que los enfrenta como si fueran dos patas no tiene sentido: es el activo contra sí mismo.",
        vulnerableCaption:
          "Ejemplo vulnerable, publicado en NaiveEthereumPort de scaffold-arc (línea 20). Suma las dos vistas.",
        fixCaption:
          "Elegí una sola vista. Si hace falta mostrar la cifra ERC-20, UsdcUnits.nativeToErc20 convierte el saldo nativo. No las sumes.",
        findingSummary:
          "El saldo nativo y el balanceOf del ERC-20 se tratan como dos activos.",
        findingDetail:
          "En Arc son el mismo USDC. Sumarlos o ponerlos en las dos patas de un pool doble-cuenta o deja un lado sin precio. UsdcUnits solo convierte la unidad; no crea un segundo activo.",
      },
      en: {
        name: "Native and ERC-20 USDC treated as two assets",
        problem:
          "Native USDC and ERC-20 USDC are the same balance in two representations, not a pair. A pool, an LTV, or an oracle that adds them double-counts the funds. A pool that pairs them as two legs is meaningless: it is the asset against itself.",
        vulnerableCaption:
          "Vulnerable example, published in scaffold-arc NaiveEthereumPort (line 20). It adds the two views.",
        fixCaption:
          "Pick one view. If you need the ERC-20 figure, UsdcUnits.nativeToErc20 converts the native balance. Do not add the views.",
        findingSummary: "Native balance and ERC-20 balanceOf are treated as two assets.",
        findingDetail:
          "On Arc they are the same USDC. Adding them, or placing them on both legs of a pool, double-counts value or prices only one side. UsdcUnits only converts the unit; it does not create a second asset.",
      },
      "pt-BR": {
        name: "USDC nativo e ERC-20 como dois ativos",
        problem:
          "O USDC nativo e o USDC ERC-20 são o mesmo saldo em duas representações, não um par. Um pool, um LTV ou um oráculo que soma os dois conta o dinheiro duas vezes. Um pool que os coloca como duas pernas não faz sentido: é o ativo contra ele mesmo.",
        vulnerableCaption:
          "Exemplo vulnerável, publicado em NaiveEthereumPort do scaffold-arc (linha 20). Soma as duas visões.",
        fixCaption:
          "Escolha uma só visão. Se precisar mostrar o número ERC-20, UsdcUnits.nativeToErc20 converte o saldo nativo. Não some as duas.",
        findingSummary: "O saldo nativo e o balanceOf do ERC-20 são tratados como dois ativos.",
        findingDetail:
          "Na Arc eles são o mesmo USDC. Somá-los ou colocá-los nas duas pernas de um pool conta em dobro ou deixa um lado sem preço. UsdcUnits só converte a unidade; não cria um segundo ativo.",
      },
    },
  },
  {
    id: "ARC-004",
    slug: "weth-pattern",
    severity: "medium",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${PORT}#:~:text=Audit%20DEX%2C%20AMM%2C%20and%20router%20contracts`,
        "Porting contracts to Arc — Audit DEX, AMM, and router contracts",
        "Porting contracts to Arc — Audit DEX, AMM, and router contracts",
        "Porting contracts to Arc — Audit DEX, AMM, and router contracts",
      ),
      link(
        `${EVM}#usdc-as-the-native-gas-token`,
        "EVM differences — USDC as the native gas token",
        "EVM differences — USDC as the native gas token",
        "EVM differences — USDC as the native gas token",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "interface IWETH {",
        "    function deposit() external payable;",
        "    function withdraw(uint256 amount) external;",
        "}",
        "",
        "// WRONG on Arc: there is no WETH-style wrapper for native USDC.",
        "function wrap(address weth) external payable {",
        "    IWETH(weth).deposit{value: msg.value}();",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "interface IERC20 {",
        "    function transferFrom(address from, address to, uint256 amount) external returns (bool);",
        "}",
        "",
        "// Drop deposit/withdraw. Use the ERC-20 USDC interface directly.",
        "// Canonical ERC-20 USDC: 0x3600000000000000000000000000000000000000",
        "function pullErc20(IERC20 usdc, address from, uint256 erc20Amount) external {",
        "    require(usdc.transferFrom(from, address(this), erc20Amount), \"pull\");",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "Patrón WETH",
        problem:
          "WETH.deposit, WETH.withdraw y las constantes de WETH asumen un nativo que se envuelve en otro ERC-20. En Arc el nativo ya es USDC y no hace falta un wrapper. Portar ese patrón no envuelve ETH: parte la liquidez y confunde al usuario. Si una ruta sigue aceptando msg.value y montos ERC-20, ahí sí hay que escalar, pero el primer paso es borrar el wrap.",
        vulnerableCaption:
          "Fragmento ilustrativo. deposit payable es el patrón WETH que la guía de portado pide eliminar.",
        fixCaption:
          "UsdcUnits no reemplaza este arreglo. Sacá deposit y withdraw. El ERC-20 USDC canónico es la interfaz del mismo saldo. Si más adelante mezclás msg.value con montos de 6 decimales, recién ahí usá UsdcUnits.",
        findingSummary: "Aparece el patrón WETH: deposit, withdraw, wrap o una constante WETH.",
        findingDetail:
          "En Arc no hay un WETH para el USDC nativo. Hay que borrar el wrap y usar la interfaz ERC-20, o el valor nativo, según lo que el contrato necesite.",
      },
      en: {
        name: "WETH pattern",
        problem:
          "WETH.deposit, WETH.withdraw, and WETH constants assume a native asset that is wrapped into a different ERC-20. On Arc the native asset is already USDC and no wrapper is needed. Porting that pattern does not wrap ETH: it fragments liquidity and confuses users. If a route still accepts both msg.value and ERC-20 amounts, those amounts still need scaling, but the first step is to delete the wrap.",
        vulnerableCaption:
          "Illustrative snippet. A payable deposit is the WETH pattern the porting guide says to remove.",
        fixCaption:
          "UsdcUnits does not replace this fix. Remove deposit and withdraw. Canonical ERC-20 USDC is the interface over the same balance. If you later mix msg.value with 6-decimal amounts, use UsdcUnits at that boundary.",
        findingSummary: "The WETH pattern shows up: deposit, withdraw, wrap, or a WETH constant.",
        findingDetail:
          "Arc has no WETH for native USDC. Remove the wrap and use the ERC-20 interface, or native value, according to what the contract actually needs.",
      },
      "pt-BR": {
        name: "Padrão WETH",
        problem:
          "WETH.deposit, WETH.withdraw e as constantes de WETH pressupõem um nativo que se embrulha em outro ERC-20. Na Arc o nativo já é USDC e não precisa de wrapper. Portar esse padrão não embrulha ETH: fragmenta a liquidez e confunde o usuário. Se uma rota ainda aceitar msg.value e valores ERC-20, aí sim é preciso converter, mas o primeiro passo é apagar o wrap.",
        vulnerableCaption:
          "Trecho ilustrativo. deposit payable é o padrão WETH que o guia de portabilidade manda remover.",
        fixCaption:
          "UsdcUnits não substitui esta correção. Remova deposit e withdraw. O ERC-20 USDC canônico é a interface do mesmo saldo. Se depois misturar msg.value com valores de 6 casas, use UsdcUnits nessa fronteira.",
        findingSummary: "Aparece o padrão WETH: deposit, withdraw, wrap ou uma constante WETH.",
        findingDetail:
          "Na Arc não há WETH para o USDC nativo. Remova o wrap e use a interface ERC-20, ou o valor nativo, conforme o que o contrato precisa.",
      },
    },
  },
  {
    id: "ARC-005",
    slug: "value-to-zero-address",
    severity: "high",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${EVM}#value-transfer-rules`,
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
      ),
      link(
        `${PORT}#:~:text=Audit%20value%20transfers`,
        "Porting contracts to Arc — Audit value transfers",
        "Porting contracts to Arc — Audit value transfers",
        "Porting contracts to Arc — Audit value transfers",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// WRONG on Arc: a value-bearing transfer to address(0) reverts.",
        "// Official revert text: \"Zero address not allowed\".",
        "function burnNative(uint256 amount) external {",
        "    payable(address(0)).transfer(amount);",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "// Do not send native value to address(0).",
        "// A zero-value call to address(0) can succeed. A non-zero one reverts.",
        "// Mint and burn go through the native-coin precompile, not a value transfer.",
        "function rejectNativeBurn() external pure {",
        "    revert(\"native burn is not a transfer to address(0)\");",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "Valor a la dirección cero",
        problem:
          "En Ethereum, enviar el nativo a address(0) se usa como burn. En Arc una transferencia con valor a 0x0 no quema ese USDC: revierte con \"Zero address not allowed\". Una transferencia de valor cero a 0x0 sí puede tener éxito. El mint y el burn pasan por el precompile de la moneda nativa, no por un envío de valor.",
        vulnerableCaption:
          "Fragmento ilustrativo. transfer a address(0) con valor revierte en Arc.",
        fixCaption:
          "UsdcUnits no aplica. No uses address(0) como destino de valor. Si el protocolo necesita destruir unidades, seguí el camino de burn que documenta Arc, y probalo en Arc testnet.",
        findingSummary: "Hay un envío de valor nativo hacia address(0).",
        findingDetail:
          "En Arc ese envío revierte. No es un burn. Un call sin valor a la dirección cero no dispara esta regla.",
      },
      en: {
        name: "Value sent to the zero address",
        problem:
          "On Ethereum, sending the native asset to address(0) is a common burn. On Arc a value-bearing transfer to 0x0 does not burn that USDC: it reverts with \"Zero address not allowed\". A zero-value transfer to 0x0 can still succeed. Mint and burn go through the native-coin precompile, not through a value transfer.",
        vulnerableCaption:
          "Illustrative snippet. transfer to address(0) with value reverts on Arc.",
        fixCaption:
          "UsdcUnits does not apply. Do not use address(0) as a value recipient. If the protocol needs to destroy units, follow the burn path Arc documents, and test it on Arc testnet.",
        findingSummary: "Native value is sent to address(0).",
        findingDetail:
          "On Arc that transfer reverts. It is not a burn. A zero-value call to the zero address does not trigger this rule.",
      },
      "pt-BR": {
        name: "Valor enviado ao endereço zero",
        problem:
          "No Ethereum, enviar o nativo para address(0) é um burn comum. Na Arc uma transferência com valor para 0x0 não queima esse USDC: ela reverte com \"Zero address not allowed\". Uma transferência de valor zero para 0x0 pode ter sucesso. Mint e burn passam pelo precompile da moeda nativa, não por um envio de valor.",
        vulnerableCaption:
          "Trecho ilustrativo. transfer para address(0) com valor reverte na Arc.",
        fixCaption:
          "UsdcUnits não se aplica. Não use address(0) como destino de valor. Se o protocolo precisa destruir unidades, siga o caminho de burn que a Arc documenta e teste na Arc testnet.",
        findingSummary: "Há um envio de valor nativo para address(0).",
        findingDetail:
          "Na Arc esse envio reverte. Não é um burn. Uma chamada sem valor para o endereço zero não dispara esta regra.",
      },
    },
  },
  {
    id: "ARC-006",
    slug: "unchecked-native-send",
    severity: "medium",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${EVM}#value-transfer-rules`,
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
        "EVM differences — Value transfer rules",
      ),
      link(
        `${PORT}#:~:text=Audit%20value%20transfers`,
        "Porting contracts to Arc — Audit value transfers",
        "Porting contracts to Arc — Audit value transfers",
        "Porting contracts to Arc — Audit value transfers",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// WRONG on Arc: success is assumed. The return value is discarded.",
        "function uncheckedSend(address payable to, uint256 amount) external {",
        "    to.call{value: amount}(\"\");",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "function checkedSend(address payable to, uint256 amount) external {",
        "    (bool ok, ) = to.call{value: amount}(\"\");",
        "    require(ok, \"native send failed\");",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "Envío nativo sin comprobar",
        problem:
          "En Arc un envío nativo puede revertir aunque el contrato tenga saldo: dirección cero, blocklist, o un burn prohibido. call{value:}, transfer y send no pueden darse por exitosos. Ignorar el booleano de send, o no mirar el retorno de call, deja al contrato en un estado que el autor creía imposible. Un revert por blocklist igual consume gas.",
        vulnerableCaption:
          "Fragmento ilustrativo. El retorno de call se descarta.",
        fixCaption:
          "UsdcUnits no aplica. Comprobá el resultado y definí el camino de fallo. El saldo no prueba que la transferencia vaya a pasar.",
        findingSummary:
          "Un call, transfer o send con valor nativo no comprueba si tuvo éxito.",
        findingDetail:
          "En Arc el envío puede fallar con saldo suficiente. Hay que leer el resultado y manejar el fallo.",
      },
      en: {
        name: "Unchecked native send",
        problem:
          "On Arc a native send can revert even when the contract has balance: the zero address, the blocklist, or a forbidden burn. call{value:}, transfer, and send cannot be assumed to succeed. Ignoring send's boolean, or skipping call's return value, leaves the contract in a state the author thought was impossible. A blocklist revert still consumes gas.",
        vulnerableCaption: "Illustrative snippet. The call return value is discarded.",
        fixCaption:
          "UsdcUnits does not apply. Check the result and define the failure path. The balance does not prove the transfer will pass.",
        findingSummary: "A native call, transfer, or send does not check success.",
        findingDetail:
          "On Arc the send can fail even when the balance is enough. Read the result and handle the failure.",
      },
      "pt-BR": {
        name: "Envio nativo sem conferir o resultado",
        problem:
          "Na Arc um envio nativo pode reverter mesmo quando o contrato tem saldo: endereço zero, blocklist ou um burn proibido. call{value:}, transfer e send não podem ser tratados como sucesso garantido. Ignorar o booleano de send, ou não ler o retorno de call, deixa o contrato num estado que o autor achava impossível. Um revert por blocklist ainda consome gás.",
        vulnerableCaption: "Trecho ilustrativo. O retorno de call é descartado.",
        fixCaption:
          "UsdcUnits não se aplica. Confira o resultado e defina o caminho de falha. O saldo não prova que a transferência vai passar.",
        findingSummary: "Um call, transfer ou send com valor nativo não confere o sucesso.",
        findingDetail:
          "Na Arc o envio pode falhar com saldo suficiente. Leia o resultado e trate a falha.",
      },
    },
  },
  {
    id: "ARC-007",
    slug: "selfdestruct-moves-usdc",
    severity: "high",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${EVM}#selfdestruct`,
        "EVM differences — SELFDESTRUCT",
        "EVM differences — SELFDESTRUCT",
        "EVM differences — SELFDESTRUCT",
      ),
      link(
        `${PORT}#:~:text=Audit%20SELFDESTRUCT%20usage`,
        "Porting contracts to Arc — Audit SELFDESTRUCT usage",
        "Porting contracts to Arc — Audit SELFDESTRUCT usage",
        "Porting contracts to Arc — Audit SELFDESTRUCT usage",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// WRONG on Arc: SELFDESTRUCT moves the contract USDC to beneficiary.",
        "// It does not burn that balance. Self as beneficiary, or address(0),",
        "// reverts when the balance is non-zero.",
        "function retire(address payable beneficiary) external {",
        "    selfdestruct(beneficiary);",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "// Move USDC with an explicit transfer. Do not use selfdestruct to",
        "// take it out of circulation. Check the call.",
        "function moveTo(address payable beneficiary, uint256 amount) external {",
        "    require(beneficiary != address(0), \"zero\");",
        "    require(beneficiary != address(this), \"self\");",
        "    (bool ok, ) = beneficiary.call{value: amount}(\"\");",
        "    require(ok, \"native send failed\");",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "selfdestruct mueve USDC",
        problem:
          "En Arc el USDC de un contrato es su saldo nativo. selfdestruct no lo quema: se lo transfiere al beneficiario y, si tiene éxito, emite un Transfer. Si el beneficiario es el propio contrato o address(0) y hay saldo, revierte. Un envío con valor a una cuenta que ya se autodestruyó también revierte: Arc lo trata como un burn prohibido. En otras cadenas el USDC ERC-20 vive en el token y selfdestruct no lo toca.",
        vulnerableCaption:
          "Fragmento ilustrativo. selfdestruct mueve el USDC nativo del contrato.",
        fixCaption:
          "UsdcUnits no aplica. No uses selfdestruct para retirar USDC de circulación. Transferí al destinatario correcto y comprobá el call. Probá el efecto en Arc testnet.",
        findingSummary: "selfdestruct mueve el USDC del contrato al beneficiario.",
        findingDetail:
          "En Arc eso no quema el saldo. Beneficiario cero, el propio contrato, una cuenta ya destruida o una dirección en la blocklist pueden revertir si hay saldo.",
      },
      en: {
        name: "selfdestruct moves USDC",
        problem:
          "On Arc a contract's USDC is its native balance. selfdestruct does not burn it: it transfers it to the beneficiary and, on success, emits a Transfer. If the beneficiary is the contract itself or address(0) and the balance is non-zero, it reverts. A value-bearing send to an account that already self-destructed also reverts: Arc treats it as a forbidden burn. On other chains ERC-20 USDC lives in the token contract and selfdestruct does not touch it.",
        vulnerableCaption:
          "Illustrative snippet. selfdestruct moves the contract's native USDC.",
        fixCaption:
          "UsdcUnits does not apply. Do not use selfdestruct to take USDC out of circulation. Transfer to the intended recipient and check the call. Test the effect on Arc testnet.",
        findingSummary: "selfdestruct moves the contract's USDC to the beneficiary.",
        findingDetail:
          "On Arc that does not burn the balance. A zero beneficiary, the contract itself, an already destroyed account, or a blocklisted address can revert when the balance is non-zero.",
      },
      "pt-BR": {
        name: "selfdestruct move USDC",
        problem:
          "Na Arc o USDC de um contrato é o saldo nativo dele. selfdestruct não queima esse saldo: transfere ao beneficiário e, se tiver sucesso, emite um Transfer. Se o beneficiário é o próprio contrato ou address(0) e há saldo, reverte. Um envio com valor para uma conta que já se autodestruiu também reverte: a Arc trata isso como um burn proibido. Em outras redes o USDC ERC-20 vive no token e o selfdestruct não o altera.",
        vulnerableCaption:
          "Trecho ilustrativo. selfdestruct move o USDC nativo do contrato.",
        fixCaption:
          "UsdcUnits não se aplica. Não use selfdestruct para tirar USDC de circulação. Transfira ao destinatário certo e confira a chamada. Teste o efeito na Arc testnet.",
        findingSummary: "selfdestruct move o USDC do contrato para o beneficiário.",
        findingDetail:
          "Na Arc isso não queima o saldo. Beneficiário zero, o próprio contrato, uma conta já destruída ou um endereço na blocklist podem reverter se houver saldo.",
      },
    },
  },
  {
    id: "ARC-008",
    slug: "prevrandao-randomness",
    severity: "high",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${EVM}#execution-and-opcode-differences`,
        "EVM differences — Execution and opcode differences",
        "EVM differences — Execution and opcode differences",
        "EVM differences — Execution and opcode differences",
      ),
      link(
        `${PORT}#:~:text=Audit%20randomness%20sources`,
        "Porting contracts to Arc — Audit randomness sources",
        "Porting contracts to Arc — Audit randomness sources",
        "Porting contracts to Arc — Audit randomness sources",
      ),
    ],
    vulnerable: {
      language: "solidity",
      code: lines([
        "// WRONG on Arc: PREVRANDAO is always 0. difficulty is the same field.",
        "function winner(uint256 participants) external view returns (uint256) {",
        "    return uint256(block.prevrandao) % participants;",
        "}",
      ]),
    },
    fix: {
      language: "solidity",
      code: lines([
        "// Take entropy from a VRF or an oracle. Do not read block.prevrandao",
        "// or block.difficulty on Arc: both are 0.",
        "function winner(uint256 entropyFromOracle, uint256 participants)",
        "    external",
        "    pure",
        "    returns (uint256)",
        "{",
        "    require(participants != 0, \"participants\");",
        "    return entropyFromOracle % participants;",
        "}",
      ]),
    },
    copy: {
      es: {
        name: "PREVRANDAO como aleatoriedad",
        problem:
          "block.prevrandao y block.difficulty no son aleatoriedad en Arc: el valor es siempre 0. Un sorteo, un commit-reveal o un salto que depende de ese campo queda fijo. La documentación dice que no hay aleatoriedad onchain y que hay que usar un oráculo o una VRF.",
        vulnerableCaption:
          "Fragmento ilustrativo. block.prevrandao como semilla de un sorteo.",
        fixCaption:
          "UsdcUnits no aplica. Sacá esa lectura del camino de decisión. Si el protocolo necesita entropía, usá una fuente documentada para Arc, no el campo que aquí es constante.",
        findingSummary:
          "block.prevrandao o block.difficulty se usan como aleatoriedad.",
        findingDetail:
          "En Arc PREVRANDAO siempre devuelve 0. El resultado queda fijo. Hay que reemplazarlo por un oráculo o una VRF.",
      },
      en: {
        name: "PREVRANDAO used as randomness",
        problem:
          "block.prevrandao and block.difficulty are not a randomness source on Arc: the value is always 0. A draw, a commit-reveal, or a branch that depends on that field is fixed. The docs say there is no onchain randomness and that an oracle or a VRF is required.",
        vulnerableCaption:
          "Illustrative snippet. block.prevrandao used as a draw seed.",
        fixCaption:
          "UsdcUnits does not apply. Remove that read from the decision path. If the protocol needs entropy, use a source documented for Arc, not the field that is constant here.",
        findingSummary: "block.prevrandao or block.difficulty is used as randomness.",
        findingDetail:
          "On Arc PREVRANDAO always returns 0. The result is fixed. Replace it with an oracle or a VRF.",
      },
      "pt-BR": {
        name: "PREVRANDAO como aleatoriedade",
        problem:
          "block.prevrandao e block.difficulty não são aleatoriedade na Arc: o valor é sempre 0. Um sorteio, um commit-reveal ou um desvio que depende desse campo fica fixo. A documentação diz que não há aleatoriedade onchain e que é preciso usar um oráculo ou uma VRF.",
        vulnerableCaption:
          "Trecho ilustrativo. block.prevrandao como semente de um sorteio.",
        fixCaption:
          "UsdcUnits não se aplica. Tire essa leitura do caminho de decisão. Se o protocolo precisa de entropia, use uma fonte documentada para a Arc, não o campo que aqui é constante.",
        findingSummary: "block.prevrandao ou block.difficulty são usados como aleatoriedade.",
        findingDetail:
          "Na Arc PREVRANDAO sempre devolve 0. O resultado fica fixo. Substitua por um oráculo ou uma VRF.",
      },
    },
  },
  {
    id: "ARC-OFF-1",
    slug: "max-fee-below-floor",
    severity: "high",
    usdcUnitsApplies: false,
    docs: [
      link(
        `${EVM}#fee-market-and-block-behavior`,
        "EVM differences — Fee market and block behavior",
        "EVM differences — Fee market and block behavior",
        "EVM differences — Fee market and block behavior",
      ),
      link(
        `${PORT}#steps`,
        "Porting contracts to Arc — Steps",
        "Porting contracts to Arc — Steps",
        "Porting contracts to Arc — Steps",
      ),
    ],
    vulnerable: {
      language: "typescript",
      code: lines([
        "// WRONG on Arc: 1 Gwei is below the 20 Gwei floor.",
        "// The mempool drops the transaction. There is no error receipt.",
        "const maxFeePerGas = 1_000_000_000n;",
      ]),
    },
    fix: {
      language: "typescript",
      code: lines([
        "// Arc testnet, chain 5042002. At least 20 Gwei.",
        "// https://docs.arc.io/arc/references/evm-differences#fee-market-and-block-behavior",
        "const maxFeePerGas = 20_000_000_000n;",
      ]),
    },
    copy: {
      es: {
        name: "maxFeePerGas bajo el piso",
        problem:
          "Arc descarta en silencio una transacción cuyo maxFeePerGas está por debajo de 20 Gwei. No hay recibo de error y no entra en un bloque. El fallo vive en scripts de TypeScript o JavaScript y en la config de Foundry, no en el bytecode. Reutilizar el gas price de una red Ethereum local suele quedar debajo del piso.",
        vulnerableCaption:
          "Fragmento ilustrativo. 1 Gwei está debajo del piso de 20 Gwei.",
        fixCaption:
          "UsdcUnits no aplica: esto es el tope de fee, no una mezcla de decimales del saldo. Fijá maxFeePerGas en al menos 20 Gwei para Arc testnet (chain 5042002).",
        findingSummary: "maxFeePerGas está por debajo del piso de 20 Gwei.",
        findingDetail:
          "La mempool de Arc tira esa transacción sin recibo. El tope tiene que ser de al menos 20 Gwei antes de enviarla a Arc testnet.",
      },
      en: {
        name: "maxFeePerGas below the floor",
        problem:
          "Arc silently drops a transaction whose maxFeePerGas is below 20 Gwei. There is no error receipt and it never appears in a block. The failure lives in TypeScript or JavaScript scripts and in Foundry config, not in bytecode. Reusing the gas price from a local Ethereum network usually lands below the floor.",
        vulnerableCaption: "Illustrative snippet. 1 Gwei is below the 20 Gwei floor.",
        fixCaption:
          "UsdcUnits does not apply: this is the fee cap, not a balance-decimal mix. Set maxFeePerGas to at least 20 Gwei for Arc testnet (chain 5042002).",
        findingSummary: "maxFeePerGas is below the 20 Gwei floor.",
        findingDetail:
          "The Arc mempool drops that transaction with no receipt. The cap has to be at least 20 Gwei before you submit it to Arc testnet.",
      },
      "pt-BR": {
        name: "maxFeePerGas abaixo do piso",
        problem:
          "A Arc descarta em silêncio uma transação cujo maxFeePerGas está abaixo de 20 Gwei. Não há recibo de erro e ela não entra em um bloco. A falha vive em scripts TypeScript ou JavaScript e na config do Foundry, não no bytecode. Reutilizar o gas price de uma rede Ethereum local costuma ficar abaixo do piso.",
        vulnerableCaption: "Trecho ilustrativo. 1 Gwei está abaixo do piso de 20 Gwei.",
        fixCaption:
          "UsdcUnits não se aplica: isto é o teto da fee, não uma mistura de casas do saldo. Defina maxFeePerGas em pelo menos 20 Gwei para a Arc testnet (chain 5042002).",
        findingSummary: "maxFeePerGas está abaixo do piso de 20 Gwei.",
        findingDetail:
          "A mempool da Arc descarta essa transação sem recibo. O teto precisa ser de pelo menos 20 Gwei antes de enviá-la à Arc testnet.",
      },
    },
  },
];

const BY_ID = new Map<string, Rule>(RULES.map((rule) => [rule.id, rule]));

export function isRuleId(value: string): value is RuleId {
  return BY_ID.has(value);
}

export function ruleById(id: string): Rule | undefined {
  return BY_ID.get(id);
}
