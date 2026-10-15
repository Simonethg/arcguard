// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc005ValueToZeroVulnerable} from "../src/vulnerable/Arc005ValueToZero.sol";
import {Arc005ValueToZeroFixed} from "../src/fixed/Arc005ValueToZero.sol";

/// @notice Requires `arc-forge test --network arc`. Upstream anvil lets a
///         non-zero value transfer to address(0) succeed.
contract Arc005ValueToZeroTest is Test {
    Arc005ValueToZeroVulnerable internal bad;
    Arc005ValueToZeroFixed internal fixed_;

    function setUp() public {
        bad = new Arc005ValueToZeroVulnerable();
        fixed_ = new Arc005ValueToZeroFixed();
    }

    function test_nonzeroValueToZeroReverts() public {
        vm.deal(address(bad), 1 ether);
        vm.expectRevert(bytes("Zero address not allowed"));
        bad.burnNative(1);
        assertEq(address(bad).balance, 1 ether);
    }

    function test_zeroValueToZeroSucceeds() public {
        bad.burnZeroValue();
    }

    function test_fixedRejectsZeroAddressBeforeSending() public {
        vm.deal(address(fixed_), 1 ether);
        vm.expectRevert(Arc005ValueToZeroFixed.ZeroAddressForbidden.selector);
        fixed_.forward(payable(address(0)), 1);
        vm.expectRevert(Arc005ValueToZeroFixed.ZeroAddressForbidden.selector);
        fixed_.forward(payable(address(0)), 0);
        assertEq(address(fixed_).balance, 1 ether);
    }

    function test_fixedForwardsToANormalRecipient() public {
        address sink = address(0xBEEF);
        vm.deal(address(fixed_), 1 ether);
        fixed_.forward(payable(sink), 1);
        assertEq(sink.balance, 1);
    }
}
