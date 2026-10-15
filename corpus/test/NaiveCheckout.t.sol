// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {NaiveCheckout} from "../src/vulnerable/NaiveCheckout.sol";
import {SafeCheckout} from "../src/fixed/SafeCheckout.sol";
import {UsdcUnits} from "../src/lib/UsdcUnits.sol";

/// @notice Port of the scaffold-arc NaiveEthereumPort failure, as a checkout.
contract NaiveCheckoutTest is Test {
    uint256 private constant PRICE = 1e6;

    NaiveCheckout internal naive;
    SafeCheckout internal safe;

    function setUp() public {
        naive = new NaiveCheckout(PRICE);
        safe = new SafeCheckout(PRICE);
    }

    function test_naiveAcceptsDustAsOneUsdc() public {
        bool accepted = naive.buy{value: PRICE}();
        assertTrue(accepted);
        assertEq(naive.paidRaw(address(this)), PRICE);
        assertEq(UsdcUnits.nativeToErc20(PRICE), 0);
    }

    function test_safeRejectsDust() public {
        vm.expectRevert(abi.encodeWithSelector(SafeCheckout.Underpaid.selector, uint256(0), PRICE));
        safe.buy{value: PRICE}();
    }

    function test_safeAcceptsOneNativeUsdc() public {
        safe.buy{value: 1e18}();
        assertEq(safe.paidErc20(address(this)), PRICE);
    }

    function test_naiveDoubleCountsTheSameFunds() public view {
        assertEq(naive.reportedBalance(1e18, 1e6), 1e18 + 1e6);
    }

    function test_naiveEmptyCheckMissesDust() public view {
        assertTrue(naive.reportedEmpty(0));
        assertGt(UsdcUnits.SCALE - 1, 0);
        assertEq(UsdcUnits.nativeToErc20(UsdcUnits.SCALE - 1), 0);
    }
}
