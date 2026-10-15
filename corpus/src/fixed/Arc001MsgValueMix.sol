// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {UsdcUnits} from "../lib/UsdcUnits.sol";

/// @title ARC-001 fixed — scale msg.value before comparing it to a price
/// @notice Payment accounting stays in ERC-20 units. Native dust below 10^12
///         does not count as a whole ERC-20 unit.
/// @dev Rule: msg-value-vs-balanceof-mix.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc001MsgValueMixFixed {
    error Underpaid(uint256 paidErc20, uint256 priceErc20);

    uint256 public immutable priceErc20;
    mapping(address => uint256) public credited;

    constructor(uint256 priceErc20_) {
        priceErc20 = priceErc20_;
    }

    function buy() external payable {
        uint256 paidErc20 = UsdcUnits.nativeToErc20(msg.value);
        if (paidErc20 < priceErc20) revert Underpaid(paidErc20, priceErc20);
        credited[msg.sender] = paidErc20 - priceErc20;
    }
}
