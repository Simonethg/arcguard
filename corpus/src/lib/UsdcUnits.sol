// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title UsdcUnits — decimal safety for USDC on Arc
/// @notice Port of the recommended fix from
///         https://github.com/Simonethg/scaffold-arc
///         (packages/foundry/src/UsdcUnits.sol), MIT.
///         On Arc, USDC is the native token. It exposes two views over the
///         same balance:
///           - native (gas, `msg.value`, `address.balance`): 18 decimals
///           - ERC-20 at 0x3600...0000 (`balanceOf`, `transfer`): 6 decimals
///         There is no wrapped USDC. Mixing the two units is off by 10^12.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
library UsdcUnits {
    /// @dev Decimals used by native gas accounting and `msg.value`.
    uint8 internal constant NATIVE_DECIMALS = 18;

    /// @dev Decimals used by the ERC-20 interface at 0x3600...0000.
    uint8 internal constant ERC20_DECIMALS = 6;

    /// @dev Conversion factor between the two views: native = erc20 * SCALE.
    uint256 internal constant SCALE = 10 ** (NATIVE_DECIMALS - ERC20_DECIMALS);

    /// @notice Convert an ERC-20 USDC amount (6 decimals) to native units (18 decimals).
    function erc20ToNative(uint256 erc20Amount) internal pure returns (uint256) {
        return erc20Amount * SCALE;
    }

    /// @notice Convert a native USDC amount (18 decimals) to ERC-20 units (6 decimals).
    /// @dev Truncates sub-unit dust. A native balance below SCALE reads as zero
    ///      through the ERC-20 view. The dust is still onchain.
    function nativeToErc20(uint256 nativeAmount) internal pure returns (uint256) {
        return nativeAmount / SCALE;
    }
}
