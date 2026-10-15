// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Negative ARC-008: timestamp and block number are not PREVRANDAO.
contract Ordering {
    function nowBlock() external view returns (uint256) {
        return block.timestamp + block.number;
    }
}
