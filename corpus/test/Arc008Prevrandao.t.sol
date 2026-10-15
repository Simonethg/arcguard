// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Arc008PrevrandaoVulnerable} from "../src/vulnerable/Arc008Prevrandao.sol";
import {Arc008PrevrandaoFixed} from "../src/fixed/Arc008Prevrandao.sol";

/// @notice Requires Arc execution. On Ethereum, PREVRANDAO is not zero.
contract Arc008PrevrandaoTest is Test {
    function test_prevrandaoAndDifficultyAreZero() public {
        Arc008PrevrandaoVulnerable bad = new Arc008PrevrandaoVulnerable();
        assertEq(block.prevrandao, 0);
        assertEq(bad.roll(), 0);
        assertEq(bad.rollLegacy(), 0);
    }

    function test_fixedUsesOracleEntropy() public {
        Arc008PrevrandaoFixed fixedRoll = new Arc008PrevrandaoFixed();
        assertEq(fixedRoll.roll(137), 37);
    }
}
