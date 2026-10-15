// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc006UncheckedSendVulnerable} from "../src/vulnerable/Arc006UncheckedSend.sol";
import {Arc006UncheckedSendFixed} from "../src/fixed/Arc006UncheckedSend.sol";

contract RevertingSink {
    receive() external payable {
        revert("nope");
    }
}

/// @notice On Arc, `call{value:}` to address(0) returns false instead of
///         burning. The vulnerable contract still records success.
contract Arc006UncheckedSendTest is Test {
    Arc006UncheckedSendVulnerable internal bad;
    Arc006UncheckedSendFixed internal fixed_;

    function setUp() public {
        bad = new Arc006UncheckedSendVulnerable();
        fixed_ = new Arc006UncheckedSendFixed();
        vm.deal(address(bad), 1 ether);
        vm.deal(address(fixed_), 1 ether);
    }

    function test_vulnerableCallToZeroRecordsSuccess() public {
        bad.forwardCall(payable(address(0)), 1);
        assertTrue(bad.recordedSuccess());
        assertEq(address(bad).balance, 1 ether);
    }

    function test_vulnerableSendToZeroRecordsSuccess() public {
        bad.forwardSend(payable(address(0)), 1);
        assertTrue(bad.recordedSuccess());
        assertEq(address(bad).balance, 1 ether);
    }

    function test_vulnerableIgnoresRevertingRecipient() public {
        RevertingSink sink = new RevertingSink();
        bad.forwardCall(payable(address(sink)), 1);
        assertTrue(bad.recordedSuccess());
        assertEq(address(sink).balance, 0);
        assertEq(address(bad).balance, 1 ether);
    }

    function test_fixedCallToZeroReverts() public {
        vm.expectRevert(Arc006UncheckedSendFixed.ZeroAddress.selector);
        fixed_.forwardCall(payable(address(0)), 1);
        assertFalse(fixed_.recordedSuccess());
        assertEq(address(fixed_).balance, 1 ether);
    }

    function test_fixedSendToZeroReverts() public {
        vm.expectRevert(Arc006UncheckedSendFixed.ZeroAddress.selector);
        fixed_.forwardSend(payable(address(0)), 1);
        assertFalse(fixed_.recordedSuccess());
    }

    function test_fixedCallToRevertingRecipientReverts() public {
        RevertingSink sink = new RevertingSink();
        vm.expectRevert(Arc006UncheckedSendFixed.NativeSendFailed.selector);
        fixed_.forwardCall(payable(address(sink)), 1);
        assertFalse(fixed_.recordedSuccess());
        assertEq(address(fixed_).balance, 1 ether);
    }

    function test_fixedDeliversToARecipient() public {
        address sink = address(0xBEEF);
        fixed_.forwardCall(payable(sink), 1);
        assertTrue(fixed_.recordedSuccess());
        assertEq(sink.balance, 1);
    }
}
