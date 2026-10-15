// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {UsdcUnits} from "../src/lib/UsdcUnits.sol";

/// @notice Documents the 10^12 gap between the two USDC views.
/// @dev https://docs.arc.io/arc/references/evm-differences
contract UsdcUnitsTest is Test {
    uint256 private constant ONE_ERC20 = 1e6;
    uint256 private constant ONE_NATIVE = 1e18;

    function test_oneUsdcMatchesAcrossViews() public pure {
        assertEq(UsdcUnits.erc20ToNative(ONE_ERC20), ONE_NATIVE);
        assertEq(UsdcUnits.nativeToErc20(ONE_NATIVE), ONE_ERC20);
        assertEq(UsdcUnits.SCALE, 1e12);
    }

    function test_erc20ViewTruncatesDust() public pure {
        uint256 dust = UsdcUnits.SCALE - 1;
        assertEq(UsdcUnits.nativeToErc20(dust), 0);
        assertGt(dust, 0);
    }

    function testFuzz_roundTripKeepsErc20Units(uint256 erc20Amount) public pure {
        erc20Amount = bound(erc20Amount, 0, type(uint256).max / UsdcUnits.SCALE);
        assertEq(UsdcUnits.nativeToErc20(UsdcUnits.erc20ToNative(erc20Amount)), erc20Amount);
    }
}
