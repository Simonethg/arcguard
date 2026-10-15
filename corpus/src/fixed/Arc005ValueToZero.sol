// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-005 fixed — refuse the zero address before any value move
/// @notice Application code fails closed for address(0), including a zero
///         amount. Burns, if a product needs them, go through the native-coin
///         precompile rather than a value transfer.
/// @dev Rule: value-to-zero-address.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc005ValueToZeroFixed {
    error ZeroAddressForbidden();
    error ForwardFailed();

    function forward(address payable to, uint256 amount) external {
        if (to == address(0)) revert ZeroAddressForbidden();
        (bool ok,) = to.call{value: amount}("");
        if (!ok) revert ForwardFailed();
    }
}
