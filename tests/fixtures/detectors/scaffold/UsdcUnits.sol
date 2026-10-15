// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title UsdcUnits — decimal safety for USDC on Arc
/// @notice On Arc, USDC is the native token. It exposes TWO views over the
///         SAME balance:
///           - native (gas accounting, `msg.value`, `address.balance`): 18 decimals
///           - ERC-20 interface at 0x3600...0000 (`balanceOf`, `transfer`):  6 decimals
///         There is no wrapped USDC. Mixing the two units is off by exactly
///         10^12 — the single most common bug when porting Ethereum code.
///         Prefer {Usdc} for balance reads, transfers, and fee math.
library UsdcUnits {
    /// @dev Decimals used by native gas accounting and `msg.value`.
    uint8 internal constant NATIVE_DECIMALS = 18;

    /// @dev Decimals used by the ERC-20 interface at 0x3600...0000.
    uint8 internal constant ERC20_DECIMALS = 6;

    /// @dev Conversion factor between the two views: native = erc20 * SCALE.
    uint256 internal constant SCALE = 10 ** (NATIVE_DECIMALS - ERC20_DECIMALS); // 1e12

    /// @notice Convert an ERC-20 USDC amount (6 decimals) to native units (18 decimals).
    function erc20ToNative(uint256 erc20Amount) internal pure returns (uint256) {
        return erc20Amount * SCALE;
    }

    /// @notice Convert a native USDC amount (18 decimals) to ERC-20 units (6 decimals).
    /// @dev Truncates sub-USDC-cent dust: a native balance below 10^12 wei
    ///      (0.000001 USDC) reads as zero through the ERC-20 view. The dust
    ///      still exists onchain — never treat `balanceOf() == 0` as proof
    ///      that the native balance is zero.
    function nativeToErc20(uint256 nativeAmount) internal pure returns (uint256) {
        return nativeAmount / SCALE;
    }
}
