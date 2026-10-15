// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Demo fixture. The value send checks its result and scales 6-decimal amounts.
/// A comment may name selfdestruct or block.prevrandao without using them.
/// Sources: https://docs.arc.io/arc/references/evm-differences
/// https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
contract GuardedPort {
    uint256 internal constant NATIVE_PER_TOKEN = 1e12;

    error ZeroAddress();

    function mix(IERC20 usdc, uint256 price) external payable {
        uint256 nativePrice = price * NATIVE_PER_TOKEN;
        require(msg.value == nativePrice, "scaled");
        usdc.transfer(msg.sender, price);
    }

    function forward(address payable to) external payable {
        if (to == address(0)) revert ZeroAddress();
        (bool ok, ) = to.call{value: msg.value}("");
        require(ok, "native send failed");
    }
}
