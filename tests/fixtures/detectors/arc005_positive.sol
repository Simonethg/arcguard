// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Positive ARC-005: value-bearing native sends to the zero address.
contract BurnNative {
    function burnTransfer() external payable {
        payable(address(0)).transfer(msg.value);
    }

    function burnCall() external payable {
        address(0).call{value: 1}("");
    }

    function burnSend() external payable {
        payable(address(0)).send(1);
    }
}
