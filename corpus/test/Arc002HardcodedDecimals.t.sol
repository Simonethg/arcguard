// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc002HardcodedDecimalsVulnerable} from "../src/vulnerable/Arc002HardcodedDecimals.sol";
import {Arc002HardcodedDecimalsFixed} from "../src/fixed/Arc002HardcodedDecimals.sol";
import {MockUsdc} from "./mocks/MockUsdc.sol";

contract Arc002HardcodedDecimalsTest is Test {
    MockUsdc internal usdc;
    Arc002HardcodedDecimalsVulnerable internal bad;
    Arc002HardcodedDecimalsFixed internal fixed_;

    function setUp() public {
        usdc = new MockUsdc();
        bad = new Arc002HardcodedDecimalsVulnerable(address(usdc));
        fixed_ = new Arc002HardcodedDecimalsFixed(address(usdc));
    }

    function test_vulnerableAcceptsSixDecimalsOfNative() public {
        bad.requireNativePayment{value: 1e6}();
    }

    function test_fixedRejectsSixDecimalsOfNative() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                Arc002HardcodedDecimalsFixed.NeedOneUsdc.selector, uint256(1e6), uint256(1e18)
            )
        );
        fixed_.requireNativePayment{value: 1e6}();
    }

    function test_fixedAcceptsOneNativeUsdc() public {
        fixed_.requireNativePayment{value: 1e18}();
        assertEq(fixed_.oneNative(), 1e18);
        assertEq(fixed_.oneErc20(), 1e6);
    }

    function test_vulnerableTransfersEighteenDecimalsOfErc20() public {
        usdc.mint(address(bad), 10 ** 18);
        bad.payErc20(address(0xBEEF));
        assertEq(usdc.lastAmount(), 10 ** 18);
    }

    function test_fixedTransfersSixDecimalsOfErc20() public {
        usdc.mint(address(fixed_), 1e6);
        fixed_.payErc20(address(0xBEEF));
        assertEq(usdc.lastAmount(), 1e6);
        assertEq(usdc.balanceOf(address(0xBEEF)), 1e6);
    }
}
