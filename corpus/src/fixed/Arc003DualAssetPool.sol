// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {UsdcUnits} from "../lib/UsdcUnits.sol";

/// @title ARC-003 fixed — one USDC reserve, native view only
/// @notice Native USDC and the ERC-20 interface are the same asset. This pool
///         accounts a single reserve and converts debt into native units
///         before computing LTV.
/// @dev Rule: native-erc20-dual-asset-pool.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc003DualAssetPoolFixed {
    receive() external payable {}

    function reservesNative() public view returns (uint256) {
        return address(this).balance;
    }

    function ltvBps(uint256 debtErc20) external view returns (uint256) {
        uint256 reserves = reservesNative();
        if (reserves == 0) return 0;
        uint256 debtNative = UsdcUnits.erc20ToNative(debtErc20);
        return (debtNative * 10_000) / reserves;
    }
}
