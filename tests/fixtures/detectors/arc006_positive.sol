// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Positive ARC-006: native transfer, unchecked send, and unchecked call.
contract AssumeSuccess {
    function viaTransfer(address payable to) external payable {
        to.transfer(msg.value);
    }

    function viaSend(address payable to) external payable {
        to.send(msg.value);
    }

    function viaCall(address payable to) external payable {
        to.call{value: msg.value}("");
    }
}
