// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc008PrevrandaoVulnerable} from "../src/vulnerable/Arc008Prevrandao.sol";
import {Arc008PrevrandaoFixed} from "../src/fixed/Arc008Prevrandao.sol";

/// @notice The vulnerable roll is wired to PREVRANDAO. Foundry's empty
///         block reports 0 on every network, so this file does not claim
///         that default is Arc-specific. The Arc testnet fork test asserts
///         the live header is 0. Local arc-anvil in this Foundry build is not.
contract Arc008PrevrandaoTest is Test {
    function test_vulnerableRollTracksPrevrandao() public {
        Arc008PrevrandaoVulnerable bad = new Arc008PrevrandaoVulnerable();
        assertEq(bad.roll(), uint256(block.prevrandao) % 100);
        assertEq(bad.rollLegacy(), uint256(block.difficulty));
    }

    function test_fixedUsesOracleEntropy() public {
        Arc008PrevrandaoFixed fixedRoll = new Arc008PrevrandaoFixed();
        assertEq(fixedRoll.roll(137), 37);
    }
}
