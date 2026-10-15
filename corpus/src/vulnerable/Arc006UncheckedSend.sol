// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-006 vulnerable — native send whose success is assumed
/// @notice Do not deploy. Ignores the boolean from `call{value:}` and
///         `send`. On Arc a native transfer can revert even when the sender
///         has balance (zero address, blocklist, burn).
/// @dev Rule: unchecked-native-send.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc006UncheckedSendVulnerable {
    bool public recordedSuccess;

    function forwardCall(address payable to, uint256 amount) external {
        to.call{value: amount}("");
        recordedSuccess = true;
    }

    function forwardSend(address payable to, uint256 amount) external {
        to.send(amount);
        recordedSuccess = true;
    }
}
