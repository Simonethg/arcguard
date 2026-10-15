// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-005 vulnerable — native value sent to the zero address
/// @notice Do not deploy. A non-zero native transfer to address(0) reverts
///         on Arc with "Zero address not allowed". A zero-value transfer
///         succeeds. This contract attempts the burn anyway.
/// @dev Rule: value-to-zero-address.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc005ValueToZeroVulnerable {
    function burnNative(uint256 amount) external {
        payable(address(0)).transfer(amount);
    }

    function burnZeroValue() external {
        payable(address(0)).transfer(0);
    }
}
