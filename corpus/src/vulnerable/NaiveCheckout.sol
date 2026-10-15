// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {NaiveEthereumPort} from "./NaiveEthereumPort.sol";

/// @title NaiveCheckout — contract that ships the NaiveEthereumPort helpers
/// @notice Do not deploy. ARC-001 / ARC-003 shaped checkout: it accepts a
///         native payment by comparing raw `msg.value` to a 6-decimal price,
///         and it reports balances by adding the two views together.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract NaiveCheckout {
    uint256 public immutable priceErc20;
    mapping(address => uint256) public paidRaw;

    constructor(uint256 priceErc20_) {
        priceErc20 = priceErc20_;
    }

    function buy() external payable returns (bool accepted) {
        accepted = NaiveEthereumPort.naiveValueCoversErc20(msg.value, priceErc20);
        if (accepted) paidRaw[msg.sender] += msg.value;
    }

    function reportedBalance(uint256 nativeBalance, uint256 erc20Balance)
        external
        pure
        returns (uint256)
    {
        return NaiveEthereumPort.naiveTotalBalance(nativeBalance, erc20Balance);
    }

    function reportedEmpty(uint256 erc20Balance) external pure returns (bool) {
        return NaiveEthereumPort.naiveIsEmpty(erc20Balance);
    }
}
