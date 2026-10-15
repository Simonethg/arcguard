// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc007SelfdestructVulnerable} from "../src/vulnerable/Arc007Selfdestruct.sol";
import {Arc007SelfdestructFixed} from "../src/fixed/Arc007Selfdestruct.sol";

/// @notice Creates, funds, destroys, and pays the destroyed account in one tx.
contract Arc007SameTxHarness {
    function createDestroyAndPay(address payable beneficiary)
        external
        payable
        returns (bool ok, bytes memory data)
    {
        Arc007SelfdestructVulnerable created = new Arc007SelfdestructVulnerable();
        created.fund{value: msg.value / 2}();
        created.destroyTo(beneficiary);
        (ok, data) = address(created).call{value: msg.value / 2}("");
    }
}

contract Arc007SelfdestructTest is Test {
    function test_destroyToSelfWithBalanceReverts() public {
        Arc007SelfdestructVulnerable bad = new Arc007SelfdestructVulnerable();
        vm.deal(address(bad), 1 ether);
        vm.expectRevert();
        bad.destroyToSelf();
    }

    function test_destroyToZeroWithBalanceReverts() public {
        Arc007SelfdestructVulnerable bad = new Arc007SelfdestructVulnerable();
        vm.deal(address(bad), 1 ether);
        vm.expectRevert(bytes("Zero address not allowed"));
        bad.destroyToZero();
    }

    function test_destroyToZeroWithNoBalanceSucceeds() public {
        Arc007SelfdestructVulnerable bad = new Arc007SelfdestructVulnerable();
        bad.destroyToZero();
    }

    function test_valueToAccountDestroyedInThisTxFails() public {
        Arc007SameTxHarness harness = new Arc007SameTxHarness();
        (bool ok, bytes memory data) =
            harness.createDestroyAndPay{value: 2}(payable(address(0xBEEF)));
        assertFalse(ok);
        assertEq(_errorString(data), "Cannot increase the balance of selfdestructed account");
    }

    function test_fixedRejectsSelfAndZero() public {
        Arc007SelfdestructFixed fixed_ = new Arc007SelfdestructFixed();
        vm.deal(address(fixed_), 1 ether);
        vm.expectRevert(Arc007SelfdestructFixed.BeneficiaryForbidden.selector);
        fixed_.withdraw(payable(address(0)), 1);
        vm.expectRevert(Arc007SelfdestructFixed.BeneficiaryForbidden.selector);
        fixed_.withdraw(payable(address(fixed_)), 1);
        assertEq(address(fixed_).balance, 1 ether);
    }

    function test_fixedWithdrawsToABeneficiary() public {
        Arc007SelfdestructFixed fixed_ = new Arc007SelfdestructFixed();
        vm.deal(address(fixed_), 5);
        address sink = address(0xBEEF);
        fixed_.withdraw(payable(sink), 5);
        assertEq(sink.balance, 5);
        assertEq(address(fixed_).balance, 0);
    }

    function _errorString(bytes memory data) internal pure returns (string memory) {
        if (data.length < 68) return "";
        bytes memory payload = new bytes(data.length - 4);
        for (uint256 i = 0; i < payload.length; i++) {
            payload[i] = data[i + 4];
        }
        return abi.decode(payload, (string));
    }
}
