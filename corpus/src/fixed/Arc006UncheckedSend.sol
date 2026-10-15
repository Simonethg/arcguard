// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-006 fixed — native send reverts when the transfer fails
/// @notice Checks the boolean from both `call{value:}` and `send`. A failed
///         native transfer does not get recorded as delivered.
/// @dev Rule: unchecked-native-send.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc006UncheckedSendFixed {
    error ZeroAddress();
    error NativeSendFailed();

    bool public recordedSuccess;

    function forwardCall(address payable to, uint256 amount) external {
        if (to == address(0)) revert ZeroAddress();
        (bool ok,) = to.call{value: amount}("");
        if (!ok) revert NativeSendFailed();
        recordedSuccess = true;
    }

    function forwardSend(address payable to, uint256 amount) external {
        if (to == address(0)) revert ZeroAddress();
        bool ok = to.send(amount);
        if (!ok) revert NativeSendFailed();
        recordedSuccess = true;
    }
}
