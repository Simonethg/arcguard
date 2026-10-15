// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {UsdcUnits} from "./UsdcUnits.sol";

/// @dev Minimal ERC-20 surface used by Arc's USDC predeploy (6-decimal view).
interface IUsdcErc20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function decimals() external view returns (uint8);
}

/// @title Usdc — Arc-safe USDC helpers
/// @notice Application-facing API for reading and moving USDC on Arc without
///         mixing the 18-decimal native view and the 6-decimal ERC-20 view.
///         Prefer this library over raw `msg.value` / `balanceOf` comparisons
///         when porting contracts from Ethereum.
///
///         Rules encoded here:
///         1. Application amounts are always ERC-20 units (6 decimals).
///         2. Native units (18 decimals) are only for gas / `msg.value` math.
///         3. Transfers to `address(0)` are rejected (Arc forbids burning native USDC;
///            we mirror that for the ERC-20 path so callers fail closed).
///         4. Never treat `balanceOf == 0` as proof the native balance is empty.
library Usdc {
    using UsdcUnits for uint256;

    /// @notice Canonical USDC ERC-20 interface on Arc (mainnet and testnet).
    address internal constant TOKEN = 0x3600000000000000000000000000000000000000;

    error UsdcZeroAddress();
    error UsdcInsufficientBalance(uint256 availableErc20, uint256 requiredErc20);
    error UsdcTransferFailed();
    error UsdcMixedUnits();

    /// @notice ERC-20 balance (6 decimals) — the ONLY balance apps should display.
    function balanceOf(address account) internal view returns (uint256) {
        return IUsdcErc20(TOKEN).balanceOf(account);
    }

    /// @notice Native balance (18 decimals) — gas / msg.value math only.
    function nativeBalanceOf(address account) internal view returns (uint256) {
        return account.balance;
    }

    /// @notice True if the ERC-20 view covers `requiredErc20` (6 decimals).
    /// @dev Does not imply the native dust is zero when this returns false for
    ///      a tiny amount — dust below 1e12 native wei is invisible to balanceOf.
    function hasAtLeast(address account, uint256 requiredErc20) internal view returns (bool) {
        return balanceOf(account) >= requiredErc20;
    }

    /// @notice Revert if `account` cannot cover `requiredErc20` (6 decimals).
    function requireBalance(address account, uint256 requiredErc20) internal view {
        uint256 available = balanceOf(account);
        if (available < requiredErc20) {
            revert UsdcInsufficientBalance(available, requiredErc20);
        }
    }

    /// @notice Compare a native `msg.value` (18d) against an ERC-20 requirement (6d).
    /// @dev Returns true only when both represent the same dollar amount.
    ///      A naive `msg.value >= requiredErc20` is wrong by 10^12.
    function nativeCoversErc20(uint256 nativeAmount, uint256 requiredErc20) internal pure returns (bool) {
        return UsdcUnits.nativeToErc20(nativeAmount) >= requiredErc20;
    }

    /// @notice Guard against the classic naive port: comparing raw msg.value to balanceOf.
    /// @dev Reverts with UsdcMixedUnits when the caller would treat the two views
    ///      as comparable without scaling. Pass the values you were about to compare.
    function assertSameUnitFamily(uint256 a, uint256 b, bool aIsNative, bool bIsNative) internal pure {
        if (aIsNative != bIsNative) revert UsdcMixedUnits();
        // Silence unused-variable warnings when families match — values are for
        // caller context / future invariant checks.
        a;
        b;
    }

    /// @notice ERC-20 transfer in 6-decimal units. Rejects the zero address.
    function transfer(address to, uint256 amountErc20) internal {
        if (to == address(0)) revert UsdcZeroAddress();
        bool ok = IUsdcErc20(TOKEN).transfer(to, amountErc20);
        if (!ok) revert UsdcTransferFailed();
    }

    /// @notice ERC-20 transferFrom in 6-decimal units. Rejects the zero address.
    function transferFrom(address from, address to, uint256 amountErc20) internal {
        if (to == address(0) || from == address(0)) revert UsdcZeroAddress();
        bool ok = IUsdcErc20(TOKEN).transferFrom(from, to, amountErc20);
        if (!ok) revert UsdcTransferFailed();
    }

    /// @notice Convert whole USDC (human) to ERC-20 units: 1 → 1e6.
    function fromWhole(uint256 wholeUsdc) internal pure returns (uint256) {
        return wholeUsdc * (10 ** UsdcUnits.ERC20_DECIMALS);
    }

    /// @notice Convert ERC-20 units to whole USDC (floors fractional cents).
    function toWhole(uint256 amountErc20) internal pure returns (uint256) {
        return amountErc20 / (10 ** UsdcUnits.ERC20_DECIMALS);
    }

    /// @notice Estimate max gas cost in ERC-20 USDC units (6 decimals).
    /// @param gasLimit Gas units for the transaction.
    /// @param maxFeePerGas Wei per gas (must be >= 20 gwei on Arc or the tx is dropped).
    /// @dev Floor is documented, not enforced here — see D4 gas helper in the SDK.
    function feeErc20(uint256 gasLimit, uint256 maxFeePerGas) internal pure returns (uint256) {
        return UsdcUnits.nativeToErc20(gasLimit * maxFeePerGas);
    }

    /// @notice Arc mempool floor for maxFeePerGas (20 gwei).
    uint256 internal constant MIN_MAX_FEE_PER_GAS = 20 gwei;
}
