// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Negative ARC-005: zero value to 0x0 is allowed, and other sends check the recipient.
contract AllowedZero {
    function zeroValue() external {
        address(0).call{value: 0}("");
    }

    function toUser(address payable to) external payable {
        require(to != address(0), "zero");
        (bool ok,) = to.call{value: msg.value}("");
        require(ok, "native send failed");
    }
}
