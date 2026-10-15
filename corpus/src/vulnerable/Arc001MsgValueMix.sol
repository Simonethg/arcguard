// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IUsdc} from "../lib/IUsdc.sol";

/// @title ARC-001 vulnerable — msg.value mixed with balanceOf
/// @notice Do not deploy. Compares and adds 18-decimal `msg.value` to a
///         6-decimal `balanceOf` and a 6-decimal price, with no 10^12 scale.
/// @dev Rule: msg-value-vs-balanceof-mix.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc001MsgValueMixVulnerable {
    IUsdc public immutable usdc;
    uint256 public immutable priceErc20;
    mapping(address => uint256) public credited;

    constructor(address usdc_, uint256 priceErc20_) {
        usdc = IUsdc(usdc_);
        priceErc20 = priceErc20_;
    }

    function buy() external payable {
        uint256 erc20Balance = usdc.balanceOf(address(this));
        require(msg.value + erc20Balance >= priceErc20, "short");
        credited[msg.sender] = msg.value + erc20Balance - priceErc20;
    }
}
