// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc003DualAssetPoolVulnerable} from "../src/vulnerable/Arc003DualAssetPool.sol";
import {Arc003DualAssetPoolFixed} from "../src/fixed/Arc003DualAssetPool.sol";
import {MockUsdc} from "./mocks/MockUsdc.sol";

contract Arc003DualAssetPoolTest is Test {
    MockUsdc internal usdc;
    Arc003DualAssetPoolVulnerable internal bad;
    Arc003DualAssetPoolFixed internal fixed_;

    function setUp() public {
        usdc = new MockUsdc();
        bad = new Arc003DualAssetPoolVulnerable(address(usdc));
        fixed_ = new Arc003DualAssetPoolFixed();
        vm.deal(address(bad), 1e18);
        vm.deal(address(fixed_), 1e18);
        usdc.mint(address(bad), 1e6);
    }

    function test_vulnerableSumsBothViews() public view {
        assertEq(bad.tvl(), 1e18 + 1e6);
        assertEq(bad.ltvBps(1e6), 0);
    }

    function test_fixedUsesOneReserve() public view {
        assertEq(fixed_.reservesNative(), 1e18);
        assertEq(fixed_.ltvBps(1e6), 10_000);
    }
}
