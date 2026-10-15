// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Negative ARC-006: the native boolean is checked. ERC-20 transfer is not a native send.
contract CheckedSend {
    function viaCall(address payable to) external payable {
        (bool ok,) = to.call{value: msg.value}("");
        if (!ok) revert("native send failed");
    }

    function erc20(IERC20 usdc, address to, uint256 amountErc20) external {
        require(usdc.transfer(to, amountErc20), "erc20");
    }
}
