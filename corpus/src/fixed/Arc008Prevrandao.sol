// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-008 fixed — randomness comes from a VRF or oracle input
/// @notice The contract does not read PREVRANDAO or DIFFICULTY. The caller
///         supplies entropy from an oracle. This corpus does not vendor a
///         VRF integration; it only removes the Arc-broken source.
/// @dev Rule: prevrandao-randomness.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc008PrevrandaoFixed {
    function roll(uint256 oracleEntropy) external pure returns (uint256) {
        return oracleEntropy % 100;
    }
}
