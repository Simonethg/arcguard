// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

/// Medium ARC-001: the native side is only a parameter named msgValue.
/// It is mixed with a real USDC balanceOf result and never with msg.value.
contract NameOnlyMsgValue {
    IERC20 usdc;

    function credit(uint256 msgValue) external view returns (bool) {
        return msgValue >= usdc.balanceOf(address(this));
    }
}
