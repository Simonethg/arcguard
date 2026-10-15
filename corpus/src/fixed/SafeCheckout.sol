// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {UsdcUnits} from "../lib/UsdcUnits.sol";

/// @title SafeCheckout — Arc-safe counterpart of NaiveCheckout
/// @notice Converts `msg.value` to ERC-20 units before comparing it to the
///         price. Does not add `address.balance` to `balanceOf`.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract SafeCheckout {
    error Underpaid(uint256 paidErc20, uint256 priceErc20);

    uint256 public immutable priceErc20;
    mapping(address => uint256) public paidErc20;

    constructor(uint256 priceErc20_) {
        priceErc20 = priceErc20_;
    }

    function buy() external payable {
        uint256 paid = UsdcUnits.nativeToErc20(msg.value);
        if (paid < priceErc20) revert Underpaid(paid, priceErc20);
        paidErc20[msg.sender] += paid;
    }

    /// @notice One USDC balance, native view. The ERC-20 view is the same funds.
    function reportedNative(address account) external view returns (uint256) {
        return account.balance;
    }
}
