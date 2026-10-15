// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-008 vulnerable — PREVRANDAO used as randomness
/// @notice Do not deploy. On Arc `block.prevrandao` and `block.difficulty`
///         are always 0, so any lottery or shuffle built on them is fixed.
/// @dev Rule: prevrandao-randomness.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc008PrevrandaoVulnerable {
    function roll() external view returns (uint256) {
        return uint256(block.prevrandao) % 100;
    }

    function rollLegacy() external view returns (uint256) {
        return uint256(block.difficulty);
    }
}
