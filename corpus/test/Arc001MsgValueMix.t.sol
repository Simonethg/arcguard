// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc001MsgValueMixVulnerable} from "../src/vulnerable/Arc001MsgValueMix.sol";
import {Arc001MsgValueMixFixed} from "../src/fixed/Arc001MsgValueMix.sol";
import {MockUsdc} from "./mocks/MockUsdc.sol";

contract Arc001MsgValueMixTest is Test {
    uint256 private constant PRICE = 1e6;

    MockUsdc internal usdc;
    Arc001MsgValueMixVulnerable internal bad;
    Arc001MsgValueMixFixed internal fixed_;

    function setUp() public {
        usdc = new MockUsdc();
        bad = new Arc001MsgValueMixVulnerable(address(usdc), PRICE);
        fixed_ = new Arc001MsgValueMixFixed(PRICE);
    }

    function test_vulnerableTreatsErc20BalanceAsNativePayment() public {
        usdc.mint(address(bad), PRICE);
        bad.buy{value: 0}();
        assertEq(bad.credited(address(this)), 0);
    }

    function test_fixedRejectsZeroNativePayment() public {
        vm.expectRevert(
            abi.encodeWithSelector(Arc001MsgValueMixFixed.Underpaid.selector, uint256(0), PRICE)
        );
        fixed_.buy{value: 0}();
    }

    function test_fixedCreditsTheScaledRemainder() public {
        fixed_.buy{value: 2e18}();
        assertEq(fixed_.credited(address(this)), 1e6);
    }

    function test_vulnerableCreditsMixedUnits() public {
        usdc.mint(address(bad), PRICE);
        bad.buy{value: 2e18}();
        assertEq(bad.credited(address(this)), 2e18);
    }
}
