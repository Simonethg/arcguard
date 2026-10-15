// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Positive ARC-008: PREVRANDAO and its difficulty alias are always 0 on Arc.
contract Random {
    function roll(uint256 players) external view returns (uint256) {
        return block.prevrandao % players;
    }

    function legacy(uint256 players) external view returns (uint256) {
        return block.difficulty % players;
    }
}
