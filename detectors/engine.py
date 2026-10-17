"""SlithIR analysis shared by the ARC-001..ARC-008 detectors.

Scale handling is deliberate: dividing or multiplying by 1e12, or calling
``nativeToErc20`` / ``erc20ToNative`` (the UsdcUnits fix), marks a value as
converted. Those patterns must not be reported. ``Usdc.sol`` and
``UsdcUnits.sol`` in scaffold-arc are the false-positive gate.

Sources:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from slither.core.cfg.node import NodeType
from slither.core.declarations import Contract, Function
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    HighLevelCall,
    InternalCall,
    LibraryCall,
    LowLevelCall,
    Member,
    Return,
    Send,
    SolidityCall,
    Transfer,
    TypeConversion,
    Unpack,
)
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable

from arcguard.rules import (
    FACTOR_1E6,
    FACTOR_1E18,
    RULES,
    SCALE_1E12,
    USDC_ERC20_ADDRESS,
    Rule,
)

RAW_NATIVE = "RAW_NATIVE"
RAW_ERC20 = "RAW_ERC20"
# A name that only says "usdc". On Arc that is ambiguous: native USDC
# (18 decimals) and the ERC-20 interface (6 decimals) are the same asset, so a
# reserve called realUsdc can hold native wei. It still counts as ERC-20 for the
# mixing rules, but not as proof of 6 decimals when the contract handles native
# value (see _erc20_scale_evidence).
NAME_USDC = "NAME_USDC"
CONVERTED = "CONVERTED"
AMOUNT_UNITS = {RAW_NATIVE, RAW_ERC20, NAME_USDC}
SCALE_FACTORS = {
    FACTOR_1E6: "1e6",
    SCALE_1E12: "1e12",
    FACTOR_1E18: "1e18",
}
CONVERTER_NAMES = {"nativetoerc20", "erc20tonative"}
MIX_OPS = {
    BinaryType.ADDITION,
    BinaryType.SUBTRACTION,
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
}
ARITH_OPS = {
    BinaryType.ADDITION: lambda left, right: left + right,
    BinaryType.SUBTRACTION: lambda left, right: left - right,
    BinaryType.MULTIPLICATION: lambda left, right: left * right,
    BinaryType.DIVISION: lambda left, right: left // right if right else None,
    BinaryType.POWER: lambda left, right: left**right if 0 <= right <= 40 else None,
}
VALUE_NAMES = {"transfer", "send"}
ERC20_MOVE_NAMES = {"transfer", "transferfrom", "approve"}
DESTRUCT_CALLS = {"selfdestruct(address)", "suicide(address)"}
UNIMPLEMENTED_DESTRUCT_NAMES = {"destroy", "selfdestruct", "suicide"}
WETH_NAME = re.compile(r"(^|[^a-z0-9])(iweth|weth9|weth|wusdc|wnative|wrappedether)([^a-z0-9]|$)")
PASSES = 6

_CACHE: dict[int, dict[str, list[Finding]]] = {}


@dataclass(frozen=True)
class Finding:
    """One detector hit. ``anchor`` is a Slither node, function, contract, or variable.

    ``severity`` overrides the rule default. ARC-001 uses Medium when the only
    native evidence is a parameter or variable named like ``msgValue`` mixed
    with a real USDC ``balanceOf`` result. A call that passes real ``msg.value``
    stays High.
    """

    rule_id: str
    message: str
    anchor: object
    severity: str


def findings_for(compilation_unit: object, rule_id: str) -> list[Finding]:
    """Return findings for ``rule_id``, computing the whole unit once."""

    key = id(compilation_unit)
    cached = _CACHE.get(key)
    if cached is None:
        cached = analyze(compilation_unit)
        _CACHE[key] = cached
    return cached.get(rule_id, [])


def analyze(compilation_unit: object) -> dict[str, list[Finding]]:
    """Run every ARC rule and group findings by id."""

    contracts = list(compilation_unit.contracts)
    const_env, const_ids = _constant_maps(contracts)
    facts = _Facts(const_env, const_ids)
    facts.native_contracts = _contracts_handling_native(contracts)
    grouped: dict[str, list[Finding]] = {rule_id: [] for rule_id in RULES}
    destructing = _functions_that_selfdestruct(contracts)

    for _ in range(PASSES):
        # Tags accumulate. Findings are rebuilt so an early pass cannot
        # freeze a hit that later scale information disproves.
        facts.findings = []
        facts.seen = set()
        facts.native_state = {}
        facts.erc20_state = {}
        facts.returns_seen = {}
        for contract in contracts:
            _scan_weth(contract, facts)
            for function in _functions(contract):
                _scan_function(function, facts, destructing)
        _flush_dual_reserves(facts)
        facts.function_returns = facts.returns_seen

    for finding in facts.findings:
        grouped[finding.rule_id].append(finding)
    return grouped


class _Facts:
    """Monotonic tags plus the finding list from the latest pass."""

    def __init__(self, const_env: dict[tuple[str, str], int], const_ids: dict[int, int]) -> None:
        self.const_env = const_env
        self.const_ids = const_ids
        self.units: dict[int, set[str]] = defaultdict(set)
        self.zero_ids: set[int] = set()
        self.this_ids: set[int] = set()
        self.alias: dict[int, object] = {}
        self.decimals_ids: set[int] = set()
        self.function_returns: dict[Function, set[str]] = {}
        self.returns_seen: dict[Function, set[str]] = {}
        self.findings: list[Finding] = []
        self.seen: set[tuple[str, int, str]] = set()
        self.native_state: dict[int, tuple[str, object]] = {}
        self.erc20_state: dict[int, tuple[str, object]] = {}
        # Real msg.value / address.balance, real USDC balanceOf, and names.
        # Kept across passes so a helper analyzed before its caller still
        # flags the call site on the next pass.
        self.real_native: set[int] = set()
        self.real_erc20: set[int] = set()
        self.name_msgvalue: set[int] = set()
        self.param_of: dict[int, tuple[int, int]] = {}
        self.param_sources: dict[int, set[tuple[int, int]]] = defaultdict(set)
        self.mix_pairs: dict[int, set[tuple[int, int]]] = defaultdict(set)
        # ids of contracts with a payable function, msg.value or address.balance.
        self.native_contracts: set[int] = set()


def _functions(contract: Contract) -> list[Function]:
    return list(contract.functions_and_modifiers_declared)


def _contracts_handling_native(contracts: list[Contract]) -> set[int]:
    found: set[int] = set()
    for contract in contracts:
        for function in _functions(contract):
            if getattr(function, "payable", False) or _reads_native(function):
                found.add(id(contract))
                break
    return found


def _reads_native(function: Function) -> bool:
    for node in function.nodes:
        for ir in _irs(node):
            if isinstance(ir, SolidityCall) and ir.function.name == "balance(address)":
                return True
            if any(getattr(var, "name", None) == "msg.value" for var in _reads(ir)):
                return True
    return False


def _constant_maps(
    contracts: list[Contract],
) -> tuple[dict[tuple[str, str], int], dict[int, int]]:
    """Fold integer constants, including ``10 ** (18 - 6)`` into ``SCALE``."""

    env: dict[tuple[str, str], int] = {}
    local: dict[int, int] = {}

    def known(var: object) -> int | None:
        if (
            isinstance(var, Constant)
            and isinstance(var.value, int)
            and not isinstance(var.value, bool)
        ):
            return int(var.value)
        if isinstance(var, StateVariable):
            return env.get((var.contract.name, var.name))
        found = local.get(id(var))
        if found is not None:
            return found
        origin = getattr(var, "points_to_origin", None)
        if isinstance(origin, StateVariable):
            return env.get((origin.contract.name, origin.name))
        return None

    for _ in range(PASSES):
        changed = False
        for contract in contracts:
            for function in _functions(contract):
                for node in function.nodes:
                    for ir in _irs(node):
                        changed |= _fold_ir(ir, env, local, known)
        if not changed:
            break
    return env, local


def _fold_ir(ir: object, env: dict, local: dict[int, int], known) -> bool:
    def store(var: object, value: int | None) -> bool:
        if value is None or local.get(id(var)) == value:
            return False
        local[id(var)] = value
        if isinstance(var, StateVariable):
            env[(var.contract.name, var.name)] = value
        return True

    if isinstance(ir, Assignment) and ir.read:
        return store(ir.lvalue, known(ir.read[0]))
    if isinstance(ir, TypeConversion) and ir.read:
        return store(ir.lvalue, known(ir.read[0]))
    if isinstance(ir, Member):
        contract_name = getattr(ir.variable_left, "name", None)
        member_name = str(ir.variable_right)
        if contract_name is None:
            return False
        return store(ir.lvalue, env.get((str(contract_name), member_name)))
    if isinstance(ir, Binary) and ir.type in ARITH_OPS:
        left = known(ir.variable_left)
        right = known(ir.variable_right)
        if left is None or right is None:
            return False
        return store(ir.lvalue, ARITH_OPS[ir.type](left, right))
    return False


def _scan_weth(contract: Contract, facts: _Facts) -> None:
    for variable in contract.state_variables_declared:
        if _is_weth_name(variable.name):
            _add(
                facts,
                RULES["ARC-004"],
                variable,
                "WETH or WUSDC name. Arc has no wrapped native; use ERC-20 USDC directly.",
            )
    if _has_weth_surface(contract):
        _add(
            facts,
            RULES["ARC-004"],
            contract,
            "WETH-style payable deposit() plus withdraw(uint256). Arc does not use a wrapper.",
        )


def _scan_function(function: Function, facts: _Facts, destructing: set[Function]) -> None:
    _remember_parameters(function, facts)
    destroyed: set[int] = set()
    for node in function.nodes:
        if node.type == NodeType.ASSEMBLY:
            _scan_assembly(node, facts)
        for ir in _irs(node):
            _remember_alias(ir, facts)
            _remember_units(ir, node, facts)
            _remember_return(ir, function, facts)
            _check_mix(ir, node, facts)
            _check_mix_call(ir, node, facts)
            _check_decimal_scale(ir, node, facts)
            _check_erc20_amount(ir, node, facts)
            _check_prevrandao_reads(ir, node, facts)
            _check_weth_call(ir, node, facts)
            _check_selfdestruct(ir, node, facts)
            _check_value_transfer(ir, node, function, facts, destructing, destroyed)


def _remember_alias(ir: object, facts: _Facts) -> None:
    if isinstance(ir, (Assignment, TypeConversion)) and ir.read:
        facts.alias[id(ir.lvalue)] = ir.read[0]
    if not isinstance(ir, TypeConversion) or not ir.read:
        return
    source = ir.read[0]
    type_text = str(getattr(ir.lvalue, "type", ""))
    if "address" not in type_text:
        return
    if _known_int(source, facts) == 0 or id(source) in facts.zero_ids:
        facts.zero_ids.add(id(ir.lvalue))
    if getattr(source, "name", None) == "this" or id(source) in facts.this_ids:
        facts.this_ids.add(id(ir.lvalue))
    if _known_int(source, facts) == USDC_ERC20_ADDRESS:
        facts.const_ids[id(ir.lvalue)] = USDC_ERC20_ADDRESS


def _remember_units(ir: object, node: object, facts: _Facts) -> None:
    del node  # Scale findings use the same IR from _check_decimal_scale.
    if isinstance(ir, SolidityCall) and getattr(ir.function, "name", "") == "balance(address)":
        _set_units(facts, ir.lvalue, {RAW_NATIVE})
        facts.real_native.add(id(ir.lvalue))
        return
    if isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
        _remember_call_units(ir, facts)
        return
    if not isinstance(ir, Binary):
        if isinstance(ir, (Assignment, TypeConversion)) and ir.read:
            _copy_units(facts, ir.read[0], ir.lvalue)
        return
    _remember_binary_units(ir, facts)


def _remember_call_units(ir: object, facts: _Facts) -> None:
    name = _normalized(getattr(getattr(ir, "function", None), "name", "") or "")
    if name in CONVERTER_NAMES:
        _set_units(facts, ir.lvalue, {CONVERTED})
        return
    if name == "nativebalanceof":
        _set_units(facts, ir.lvalue, {RAW_NATIVE})
        return
    if name == "balanceof" and _is_usdc_call(ir, facts):
        _set_units(facts, ir.lvalue, {RAW_ERC20})
        facts.real_erc20.add(id(ir.lvalue))
        return
    if name == "decimals" and _is_usdc_call(ir, facts):
        facts.decimals_ids.add(id(ir.lvalue))
        return
    returned = facts.function_returns.get(ir.function, set())
    if CONVERTED in returned:
        _set_units(facts, ir.lvalue, {CONVERTED})
    elif returned & AMOUNT_UNITS:
        _set_units(facts, ir.lvalue, set(returned & AMOUNT_UNITS))


def _remember_binary_units(ir: Binary, facts: _Facts) -> None:
    left = ir.variable_left
    right = ir.variable_right
    if ir.type == BinaryType.SUBTRACTION and _is_decimal_gap(left, right, facts):
        facts.const_ids[id(ir.lvalue)] = 12
        return
    if ir.type == BinaryType.POWER and _known_int(left, facts) == 10:
        _remember_power(ir, facts)
        return
    factor, _other = _factor_and_other(left, right, facts)
    if factor in {SCALE_1E12, FACTOR_1E6, FACTOR_1E18} and ir.type in {
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }:
        # 1e12 is the documented conversion. 1e6 and 1e18 are the wrong scale;
        # the finding is recorded in _check_decimal_scale, and the result is
        # no longer a raw 18-decimal or 6-decimal amount.
        _set_units(facts, ir.lvalue, {CONVERTED})
        return
    if ir.type in {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }:
        _propagate_arith(ir, facts)


def _remember_power(ir: Binary, facts: _Facts) -> None:
    exponent = ir.variable_right
    value = _known_int(exponent, facts)
    if value in {6, 12, 18}:
        facts.const_ids[id(ir.lvalue)] = 10**value
        return
    if id(exponent) in facts.decimals_ids:
        # USDC.decimals() is 6. Using it as the native scale misses the 1e12 gap.
        facts.const_ids[id(ir.lvalue)] = FACTOR_1E6


def _remember_parameters(function: Function, facts: _Facts) -> None:
    for index, param in enumerate(function.parameters):
        facts.param_of[id(param)] = (id(function), index)
        facts.param_sources[id(param)].add((id(function), index))
        if "msgvalue" in _normalized(param.name):
            facts.name_msgvalue.add(id(param))


def _record_mix_pair(node: object, native_var: object, erc_var: object, facts: _Facts) -> None:
    function = getattr(node, "function", None)
    if not isinstance(function, Function):
        return
    for native_index in _param_indexes(native_var, function, facts):
        for erc_index in _param_indexes(erc_var, function, facts):
            if native_index != erc_index:
                facts.mix_pairs[id(function)].add((native_index, erc_index))


def _param_indexes(var: object, function: Function, facts: _Facts) -> set[int]:
    found: set[int] = set()
    func_id = id(function)
    located = facts.param_of.get(id(var))
    if located is not None and located[0] == func_id:
        found.add(located[1])
    for source_func, index in facts.param_sources.get(id(var), ()):
        if source_func == func_id:
            found.add(index)
    return found


def _call_arguments(ir: object, function: Function) -> list[object]:
    """Drop a leading library address if Slither inserted one."""

    args = list(getattr(ir, "arguments", []) or [])
    if len(args) == len(function.parameters) + 1:
        return args[1:]
    return args


def _carry(facts: _Facts, target: object, sources: list[object]) -> None:
    """Propagate real units and parameter indexes through a non-scaled value."""

    if target is None:
        return
    target_id = id(target)
    if "msgvalue" in _normalized(getattr(target, "name", "") or ""):
        facts.name_msgvalue.add(target_id)
    for source in sources:
        if source is None:
            continue
        if _carries_real_native(source, facts):
            facts.real_native.add(target_id)
        if _carries_real_erc20(source, facts):
            facts.real_erc20.add(target_id)
        if _carries_name_msgvalue(source, facts):
            facts.name_msgvalue.add(target_id)
        located = facts.param_of.get(id(source))
        if located is not None:
            facts.param_sources[target_id].add(located)
        inherited = facts.param_sources.get(id(source))
        if inherited:
            facts.param_sources[target_id] |= set(inherited)


def _carries_real_native(var: object, facts: _Facts) -> bool:
    if getattr(var, "name", None) == "msg.value":
        return True
    if id(var) in facts.real_native:
        return True
    origin = getattr(var, "points_to_origin", None)
    return origin is not None and origin is not var and id(origin) in facts.real_native


def _carries_real_erc20(var: object, facts: _Facts) -> bool:
    if id(var) in facts.real_erc20:
        return True
    origin = getattr(var, "points_to_origin", None)
    return origin is not None and origin is not var and id(origin) in facts.real_erc20


def _carries_name_msgvalue(var: object, facts: _Facts) -> bool:
    if "msgvalue" in _normalized(getattr(var, "name", "") or ""):
        return True
    if id(var) in facts.name_msgvalue:
        return True
    origin = getattr(var, "points_to_origin", None)
    return origin is not None and origin is not var and id(origin) in facts.name_msgvalue


def _remember_return(ir: object, function: Function, facts: _Facts) -> None:
    if not isinstance(ir, Return):
        return
    bucket = facts.returns_seen.setdefault(function, set())
    for value in _reads(ir):
        bucket |= _effective(value, facts)


def _check_mix(ir: object, node: object, facts: _Facts) -> None:
    if not isinstance(ir, Binary) or ir.type not in MIX_OPS:
        return
    if not _is_amount(ir.variable_left) or not _is_amount(ir.variable_right):
        return
    left = _effective(ir.variable_left, facts)
    right = _effective(ir.variable_right, facts)
    native_var: object | None = None
    erc_var: object | None = None
    if _is_raw(left, RAW_NATIVE) and _is_raw(right, RAW_ERC20):
        native_var, erc_var = ir.variable_left, ir.variable_right
    elif _is_raw(left, RAW_ERC20) and _is_raw(right, RAW_NATIVE):
        native_var, erc_var = ir.variable_right, ir.variable_left
    if native_var is not None and erc_var is not None:
        _record_mix_pair(node, native_var, erc_var, facts)
        if _carries_real_native(native_var, facts):
            _add(facts, RULES["ARC-001"], node, _mix_message())
        elif _carries_name_msgvalue(native_var, facts) and _carries_real_erc20(erc_var, facts):
            _add(facts, RULES["ARC-001"], node, _name_mix_message(), severity="Medium")
        else:
            _add(facts, RULES["ARC-001"], node, _mix_message())
        if ir.type == BinaryType.ADDITION:
            _add(facts, RULES["ARC-003"], node, _dual_message())
    if ir.type == BinaryType.EQUAL:
        _check_decimals_equals_18(ir, node, facts)


def _check_mix_call(ir: object, node: object, facts: _Facts) -> None:
    """Flag a caller that feeds real msg.value into a helper that mixes units.

    ``NaiveEthereumPort.naiveValueCoversErc20`` only sees a parameter named
    ``msgValue``. The High hit belongs on the contract that passes ``msg.value``.
    """

    if not isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
        return
    function = getattr(ir, "function", None)
    if not isinstance(function, Function):
        return
    pairs = facts.mix_pairs.get(id(function))
    if not pairs:
        return
    args = _call_arguments(ir, function)
    for native_index, erc_index in pairs:
        if native_index >= len(args) or erc_index >= len(args):
            continue
        native_arg = args[native_index]
        erc_arg = args[erc_index]
        if CONVERTED in _effective(native_arg, facts):
            continue
        if not _carries_real_native(native_arg, facts):
            continue
        if not _is_raw(_effective(erc_arg, facts), RAW_ERC20):
            continue
        _add(facts, RULES["ARC-001"], node, _call_mix_message())


def _check_decimal_scale(ir: object, node: object, facts: _Facts) -> None:
    """Flag 6 decimals applied to native value, or 18 decimals applied to ERC-20."""

    if not isinstance(ir, Binary) or ir.type not in {
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
        BinaryType.LESS,
        BinaryType.GREATER,
        BinaryType.LESS_EQUAL,
        BinaryType.GREATER_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }:
        return
    factor, other = _factor_and_other(ir.variable_left, ir.variable_right, facts)
    if other is None or factor is None:
        return
    other_units = _effective(other, facts)
    compared = ir.type not in {BinaryType.MULTIPLICATION, BinaryType.DIVISION}
    if factor == FACTOR_1E6 and _is_raw(other_units, RAW_NATIVE):
        detail = (
            "compares native USDC with a 6-decimal unit (1e6). Native value has 18 decimals."
            if compared
            else "applies a 6-decimal factor to native USDC. Native value has 18 decimals."
        )
        _add(facts, RULES["ARC-002"], node, detail)
    elif (
        factor == FACTOR_1E18
        and _is_raw(other_units, RAW_ERC20)
        and _erc20_scale_evidence(other_units, node, facts)
    ):
        detail = (
            "compares an ERC-20 USDC amount with 1e18. That interface has 6 decimals."
            if compared
            else "applies an 18-decimal factor to an ERC-20 amount. The interface has 6 decimals."
        )
        _add(facts, RULES["ARC-002"], node, detail)


def _check_erc20_amount(ir: object, node: object, facts: _Facts) -> None:
    if not isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
        return
    name = _normalized(getattr(ir.function, "name", "") or "")
    if name not in ERC20_MOVE_NAMES or not _is_usdc_call(ir, facts):
        return
    amounts = [arg for arg in ir.arguments if _is_amount(arg)]
    if not amounts:
        return
    amount = amounts[-1]
    if _is_raw(_effective(amount, facts), RAW_NATIVE):
        _add(
            facts,
            RULES["ARC-001"],
            node,
            "ERC-20 USDC transfer or approve amount is raw native value (18 decimals).",
        )
    if _known_int(amount, facts) == FACTOR_1E18:
        _add(
            facts,
            RULES["ARC-002"],
            node,
            "ERC-20 USDC transfer or approve amount is hardcoded as 10**18. "
            "The interface uses 6 decimals.",
        )


def _check_selfdestruct(ir: object, node: object, facts: _Facts) -> None:
    if not isinstance(ir, SolidityCall):
        return
    if getattr(ir.function, "name", "") not in DESTRUCT_CALLS:
        return
    beneficiary = ir.arguments[0] if ir.arguments else None
    if beneficiary is not None and _is_zero_address(beneficiary, facts):
        detail = "beneficiary is address(0); a non-zero balance reverts instead of burning."
    elif beneficiary is not None and _is_this_address(beneficiary, facts):
        detail = "beneficiary is the contract itself; a non-zero balance reverts."
    else:
        detail = "the contract's native USDC is transferred to the beneficiary."
    _add(facts, RULES["ARC-007"], node, "SELFDESTRUCT moves USDC on Arc; " + detail)


def _check_value_transfer(
    ir: object,
    node: object,
    function: Function,
    facts: _Facts,
    destructing: set[Function],
    destroyed: set[int],
) -> None:
    if isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
        callee = getattr(ir, "function", None)
        destination = getattr(ir, "destination", None)
        if (
            callee is not None
            and destination is not None
            and _callee_destructs(callee, destructing)
        ):
            destroyed.add(_root_id(destination, facts))
    if not isinstance(ir, (Transfer, Send, LowLevelCall)):
        return
    if not _value_moves(getattr(ir, "call_value", None), facts):
        return
    destination = ir.destination
    if _is_zero_address(destination, facts):
        _add(
            facts,
            RULES["ARC-005"],
            node,
            "native value is sent to address(0). Arc reverts with 'Zero address not allowed'.",
        )
    if _root_id(destination, facts) in destroyed:
        _add(
            facts,
            RULES["ARC-007"],
            node,
            "native value is sent to an account destroyed earlier in this transaction.",
        )
    if not _success_checked(function, ir):
        kind = type(ir).__name__.lower()
        _add(
            facts,
            RULES["ARC-006"],
            node,
            f"native {kind} assumes success. Blocklist or a burn can still revert it.",
        )


def _scan_assembly(node: object, facts: _Facts) -> None:
    text = node.source_mapping.content or ""
    if re.search(r"\bselfdestruct\b|\bsuicide\b", text):
        _add(
            facts,
            RULES["ARC-007"],
            node,
            "assembly SELFDESTRUCT moves the contract's native USDC to the beneficiary.",
        )
    if re.search(r"\bprevrandao\b|\bdifficulty\b", text):
        _add(
            facts,
            RULES["ARC-008"],
            node,
            "assembly reads PREVRANDAO or difficulty. On Arc that value is always 0.",
        )


def _flush_dual_reserves(facts: _Facts) -> None:
    contracts = set(facts.native_state) & set(facts.erc20_state)
    for contract_id in contracts:
        native_name, native_anchor = facts.native_state[contract_id]
        erc20_name, erc20_anchor = facts.erc20_state[contract_id]
        if native_name == erc20_name:
            continue
        _add(
            facts,
            RULES["ARC-003"],
            erc20_anchor,
            "stores native USDC and ERC-20 USDC as separate reserves of one asset.",
        )


def _check_decimals_equals_18(ir: Binary, node: object, facts: _Facts) -> None:
    left_is_decimals = id(ir.variable_left) in facts.decimals_ids
    right_is_decimals = id(ir.variable_right) in facts.decimals_ids
    if left_is_decimals and _known_int(ir.variable_right, facts) == 18:
        _add(facts, RULES["ARC-002"], node, _decimals_18_message())
    elif right_is_decimals and _known_int(ir.variable_left, facts) == 18:
        _add(facts, RULES["ARC-002"], node, _decimals_18_message())


def _propagate_arith(ir: Binary, facts: _Facts) -> None:
    left = _effective(ir.variable_left, facts)
    right = _effective(ir.variable_right, facts)
    if CONVERTED in left or CONVERTED in right:
        _set_units(facts, ir.lvalue, {CONVERTED})
        return
    merged = (left | right) & AMOUNT_UNITS
    if merged:
        _set_units(facts, ir.lvalue, merged)
    _carry(facts, ir.lvalue, [ir.variable_left, ir.variable_right])


def _copy_units(facts: _Facts, source: object, target: object) -> None:
    if not _is_amount(target):
        _note_state_units(facts, target, source)
        return
    effective = _effective(source, facts)
    if CONVERTED in effective:
        _set_units(facts, target, {CONVERTED})
    elif effective & AMOUNT_UNITS:
        _set_units(facts, target, set(effective & AMOUNT_UNITS))
        _carry(facts, target, [source])
    else:
        _carry(facts, target, [source])
    _note_state_units(facts, target, source)


def _note_state_units(facts: _Facts, target: object, source: object) -> None:
    if not isinstance(target, StateVariable) or not _is_amount(target):
        return
    effective = _effective(source, facts)
    anchor = getattr(target, "node", None) or target
    if _is_raw(effective, RAW_NATIVE) and CONVERTED not in effective:
        facts.native_state[id(target.contract)] = (target.name, anchor)
    if _is_raw(effective, RAW_ERC20) and CONVERTED not in effective:
        facts.erc20_state[id(target.contract)] = (target.name, anchor)


def _factor_and_other(
    left: object, right: object, facts: _Facts
) -> tuple[int | None, object | None]:
    left_value = _known_int(left, facts)
    right_value = _known_int(right, facts)
    if left_value in SCALE_FACTORS and right_value not in SCALE_FACTORS:
        return left_value, right
    if right_value in SCALE_FACTORS and left_value not in SCALE_FACTORS:
        return right_value, left
    return None, None


def _is_decimal_gap(left: object, right: object, facts: _Facts) -> bool:
    if _known_int(left, facts) != 18:
        return False
    if id(right) in facts.decimals_ids:
        return True
    return _known_int(right, facts) == 6


def _success_checked(function: Function, ir: object) -> bool:
    """True when a send/call boolean is read. ``transfer`` has no boolean."""

    if isinstance(ir, Transfer):
        return False
    lvalue = getattr(ir, "lvalue", None)
    if lvalue is None:
        return False
    tracked = {id(lvalue)}
    for node in function.nodes:
        for other in _irs(node):
            if isinstance(other, Unpack) and id(other.tuple) in tracked:
                tracked.add(id(other.lvalue))
                continue
            if any(id(item) in tracked for item in _reads(other)):
                return True
    return False


def _value_moves(call_value: object, facts: _Facts) -> bool:
    if call_value is None:
        return False
    value = _known_int(call_value, facts)
    return value != 0


def _is_zero_address(var: object, facts: _Facts) -> bool:
    if id(var) in facts.zero_ids:
        return True
    if _known_int(var, facts) == 0 and "address" in str(getattr(var, "type", "")):
        return True
    return False


def _is_this_address(var: object, facts: _Facts) -> bool:
    return id(var) in facts.this_ids or getattr(var, "name", None) == "this"


def _callee_destructs(function: object, destructing: set[Function]) -> bool:
    # A call to another contract's public state variable resolves to the
    # StateVariable behind the getter. A getter only reads storage, so it
    # cannot self-destruct.
    if not isinstance(function, Function):
        return False
    if function in destructing:
        return True
    if function.is_implemented and function.nodes:
        return False
    return function.name.lower() in UNIMPLEMENTED_DESTRUCT_NAMES


def _functions_that_selfdestruct(contracts: list[Contract]) -> set[Function]:
    found: set[Function] = set()
    for contract in contracts:
        for function in _functions(contract):
            for node in function.nodes:
                if node.type == NodeType.ASSEMBLY and re.search(
                    r"\bselfdestruct\b|\bsuicide\b",
                    node.source_mapping.content or "",
                ):
                    found.add(function)
                for ir in _irs(node):
                    if (
                        isinstance(ir, SolidityCall)
                        and getattr(ir.function, "name", "") in DESTRUCT_CALLS
                    ):
                        found.add(function)
    return found


def _has_weth_surface(contract: Contract) -> bool:
    deposit = False
    withdraw = False
    for function in contract.functions_declared:
        if function.name == "deposit" and function.payable and len(function.parameters) == 0:
            deposit = True
        if function.name == "withdraw" and len(function.parameters) == 1:
            withdraw = True
    return deposit and withdraw


def _is_weth_name(name: str) -> bool:
    return bool(WETH_NAME.search(name.lower()))


def _is_usdc_call(ir: object, facts: _Facts) -> bool:
    parts: list[str] = []
    function = getattr(ir, "function", None)
    contract = getattr(function, "contract", None)
    if contract is not None:
        parts.append(contract.name)
    destination = getattr(ir, "destination", None)
    if destination is not None:
        parts.append(str(getattr(destination, "name", "") or ""))
        parts.append(str(getattr(destination, "type", "") or ""))
        if _known_int(destination, facts) == USDC_ERC20_ADDRESS:
            parts.append("usdc")
    blob = " ".join(parts).lower()
    if "wusdc" in blob or "weth" in blob:
        return False
    return "usdc" in blob


def _is_amount(var: object) -> bool:
    if getattr(var, "name", None) == "msg.value":
        return True
    type_text = str(getattr(var, "type", "") or "")
    return "uint" in type_text or type_text.startswith("int")


def _effective(var: object, facts: _Facts) -> set[str]:
    found = set(facts.units.get(id(var), ()))
    if getattr(var, "name", None) == "msg.value":
        found.add(RAW_NATIVE)
    named = _classify_name(getattr(var, "name", "") or "", var, facts)
    if named:
        found.add(named)
    if CONVERTED in found:
        return {CONVERTED}
    return found & AMOUNT_UNITS


def _classify_name(name: str, var: object, facts: _Facts) -> str | None:
    if isinstance(var, StateVariable) and var.is_constant:
        value = _known_int(var, facts)
        if value is not None and 0 <= value <= 255:
            return None
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    if not normalized or normalized.endswith("decimals"):
        return None
    if "whole" in normalized and "usdc" in normalized:
        return None
    if "erc20" in normalized or "balanceof" in normalized:
        return RAW_ERC20
    if (
        "msgvalue" in normalized
        or "nativebalance" in normalized
        or "nativeamount" in normalized
        or normalized == "native"
    ):
        return RAW_NATIVE
    if "usdc" in normalized and "wusdc" not in normalized:
        return NAME_USDC
    return None


def _is_raw(units: set[str], kind: str) -> bool:
    if CONVERTED in units:
        return False
    if kind == RAW_ERC20:
        return RAW_ERC20 in units or NAME_USDC in units
    return kind in units


def _erc20_scale_evidence(units: set[str], node: object, facts: _Facts) -> bool:
    """True when an ERC-20 reading is strong enough to call 1e18 a 6-decimal bug.

    Real ERC-20 evidence (balanceOf, an erc20/balanceOf name) always counts. A
    bare "usdc" name counts only when the value carries no native evidence and
    the contract never touches native value (no payable function, msg.value or
    address.balance). Otherwise ``reserveUsdc * 1e18`` is usually native wei
    priced per whole 18-decimal token, which is correct on Arc.
    """

    if RAW_ERC20 in units:
        return True
    if NAME_USDC not in units or RAW_NATIVE in units:
        return False
    function = getattr(node, "function", None)
    contract = getattr(function, "contract", None)
    return id(contract) not in facts.native_contracts


def _set_units(facts: _Facts, var: object, units: set[str]) -> None:
    if not units:
        return
    if CONVERTED in units:
        facts.units[id(var)] = {CONVERTED}
        return
    facts.units[id(var)] |= set(units)


def _known_int(var: object, facts: _Facts) -> int | None:
    if isinstance(var, Constant) and isinstance(var.value, int) and not isinstance(var.value, bool):
        return int(var.value)
    if isinstance(var, StateVariable):
        return facts.const_env.get((var.contract.name, var.name))
    found = facts.const_ids.get(id(var))
    if found is not None:
        return found
    if isinstance(var, ReferenceVariable):
        origin = var.points_to_origin
        if origin is not None and origin is not var:
            return _known_int(origin, facts)
    return None


def _root_id(var: object, facts: _Facts) -> int:
    seen: set[int] = set()
    current = var
    while id(current) in facts.alias and id(current) not in seen:
        seen.add(id(current))
        current = facts.alias[id(current)]
    return id(current)


def _reads(ir: object) -> list[object]:
    raw = getattr(ir, "read", None) or []
    values: list[object] = []
    for item in raw:
        if item is None:
            continue
        if isinstance(item, (list, tuple)):
            values.extend(piece for piece in item if piece is not None)
        else:
            values.append(item)
    return values


def _irs(node: object) -> list[object]:
    return list(getattr(node, "irs", []) or [])


def _normalized(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _mix_message() -> str:
    return "mixes 18-decimal native USDC with a 6-decimal ERC-20 amount and does not scale by 1e12."


def _name_mix_message() -> str:
    return (
        "parameter or variable named like msgValue is mixed with a USDC balanceOf "
        "result and does not scale by 1e12."
    )


def _call_mix_message() -> str:
    return (
        "passes raw msg.value or address.balance into a helper that mixes it with "
        "an ERC-20 amount and does not scale by 1e12."
    )


def _dual_message() -> str:
    return "adds native USDC and ERC-20 USDC as if they were two assets."


def _decimals_18_message() -> str:
    return "assumes USDC decimals() is 18. The ERC-20 interface uses 6; native value uses 18."


def _add(
    facts: _Facts,
    rule: Rule,
    anchor: object,
    detail: str,
    severity: str | None = None,
) -> None:
    impact = severity or rule.severity
    message = (
        f"{rule.rule_id} ({impact}): {detail} "
        f"Recommendation: {rule.recommendation} Docs: {rule.primary_doc}"
    )
    key = (rule.rule_id, id(anchor), impact, detail)
    if key in facts.seen:
        return
    facts.seen.add(key)
    facts.findings.append(Finding(rule.rule_id, message, anchor, impact))


def _check_weth_call(ir: object, node: object, facts: _Facts) -> None:
    if not isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
        return
    function = getattr(ir, "function", None)
    if function is None or function.name not in {"deposit", "withdraw"}:
        return
    contract = getattr(function, "contract", None)
    destination = getattr(ir, "destination", None)
    names = [
        function.name,
        getattr(contract, "name", "") or "",
        str(getattr(destination, "name", "") or ""),
        str(getattr(destination, "type", "") or ""),
    ]
    surface = contract is not None and _has_weth_surface(contract)
    if surface or any(_is_weth_name(name) for name in names):
        _add(
            facts,
            RULES["ARC-004"],
            node,
            "calls WETH-style deposit or withdraw. Arc has no wrapped native token.",
        )


def _check_prevrandao_reads(ir: object, node: object, facts: _Facts) -> None:
    for value in _reads(ir):
        if getattr(value, "name", None) in {"block.prevrandao", "block.difficulty"}:
            _add(
                facts,
                RULES["ARC-008"],
                node,
                "reads block.prevrandao or block.difficulty. On Arc PREVRANDAO is always 0.",
            )
            return
