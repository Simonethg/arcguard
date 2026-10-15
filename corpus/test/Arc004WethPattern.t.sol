// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc004WethPatternVulnerable, IWETH} from "../src/vulnerable/Arc004WethPattern.sol";
import {Arc004WethPatternFixed} from "../src/fixed/Arc004WethPattern.sol";

contract Arc004WethPatternTest is Test {
    address private constant ETHEREUM_WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address private constant ARC_USDC = 0x3600000000000000000000000000000000000000;

    Arc004WethPatternVulnerable internal bad;
    Arc004WethPatternFixed internal fixed_;

    function setUp() public {
        bad = new Arc004WethPatternVulnerable();
        fixed_ = new Arc004WethPatternFixed();
    }

    function test_vulnerableWrapsThroughEthereumWeth() public {
        assertEq(bad.WETH(), ETHEREUM_WETH);
        vm.mockCall(ETHEREUM_WETH, abi.encodeWithSelector(IWETH.deposit.selector), "");
        vm.mockCall(ETHEREUM_WETH, abi.encodeWithSelector(IWETH.withdraw.selector), "");
        vm.expectCall(ETHEREUM_WETH, 1 ether, abi.encodeWithSelector(IWETH.deposit.selector));
        bad.wrap{value: 1 ether}();
        vm.expectCall(
            ETHEREUM_WETH, abi.encodeWithSelector(IWETH.withdraw.selector, uint256(1 ether))
        );
        bad.unwrap(1 ether);
    }

    function test_fixedAccountsNativeWithoutAWrapper() public {
        assertEq(fixed_.USDC(), ARC_USDC);
        fixed_.receiveNative{value: 1 ether}();
        assertEq(fixed_.creditedErc20(address(this)), 1e6);
    }
}
