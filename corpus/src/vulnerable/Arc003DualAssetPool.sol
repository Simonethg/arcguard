// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IUsdc} from "../lib/IUsdc.sol";

/// @title ARC-003 vulnerable — native USDC and ERC-20 USDC as two assets
/// @notice Do not deploy. TVL and a toy LTV add `address.balance` (18 decimals)
///         to `balanceOf` (6 decimals) as if they were two reserves.
/// @dev Rule: native-erc20-dual-asset-pool.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc003DualAssetPoolVulnerable {
    IUsdc public immutable usdc;

    constructor(address usdc_) {
        usdc = IUsdc(usdc_);
    }

    receive() external payable {}

    function tvl() public view returns (uint256) {
        return address(this).balance + usdc.balanceOf(address(this));
    }

    /// @dev `debtErc20` is 6 decimals. `tvl()` is a mixed integer. The ratio is meaningless.
    function ltvBps(uint256 debtErc20) external view returns (uint256) {
        uint256 reserves = tvl();
        if (reserves == 0) return 0;
        return (debtErc20 * 10_000) / reserves;
    }
}
