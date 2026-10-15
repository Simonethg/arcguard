// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IWETH {
    function deposit() external payable;
    function withdraw(uint256 wad) external;
}

/// Positive ARC-004: WETH surface, constant, and deposit/withdraw calls.
contract Wrap {
    IWETH public weth;
    address public constant WETH9 = address(0x1);

    function wrap() external payable {
        weth.deposit{value: msg.value}();
    }

    function unwrap(uint256 wad) external {
        weth.withdraw(wad);
    }
}
