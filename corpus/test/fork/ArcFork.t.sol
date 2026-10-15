// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {IUsdc} from "../../src/lib/IUsdc.sol";
import {Arc005ValueToZeroVulnerable} from "../../src/vulnerable/Arc005ValueToZero.sol";
import {Arc008PrevrandaoVulnerable} from "../../src/vulnerable/Arc008Prevrandao.sol";

/// @title Fork tests against arc-anvil or Arc testnet state
/// @notice Skipped unless ARC_FORK=true. Run with
///         `arc-forge test --network arc --fork-url <rpc> --match-path test/fork/*`.
///         Chain id 31337 is local arc-anvil. Chain id 5042002 is Arc testnet.
///         Any other chain, including mainnet, fails closed.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract ArcForkTest is Test {
    address internal constant USDC = 0x3600000000000000000000000000000000000000;
    uint256 internal constant ARC_TESTNET_CHAIN_ID = 5042002;
    uint256 internal constant ARC_ANVIL_CHAIN_ID = 31337;

    function setUp() public {
        if (!vm.envOr("ARC_FORK", false)) {
            vm.skip(true);
            return;
        }
        if (block.chainid != ARC_TESTNET_CHAIN_ID && block.chainid != ARC_ANVIL_CHAIN_ID) {
            revert("fork chain is not arc-anvil or Arc testnet");
        }
    }

    function test_fork_usdcPredeployUsesSixDecimals() public view {
        assertGt(USDC.code.length, 0);
        assertEq(IUsdc(USDC).decimals(), 6);
    }

    function test_fork_valueToZeroReverts() public {
        Arc005ValueToZeroVulnerable bad = new Arc005ValueToZeroVulnerable();
        vm.deal(address(bad), 1 ether);
        vm.expectRevert(bytes("Zero address not allowed"));
        bad.burnNative(1);
        assertEq(address(bad).balance, 1 ether);
    }

    function test_fork_prevrandaoIsZero() public {
        Arc008PrevrandaoVulnerable bad = new Arc008PrevrandaoVulnerable();
        assertEq(block.prevrandao, 0);
        assertEq(bad.roll(), 0);
    }

    function test_fork_baseFeeMeetsTheFloor() public view {
        assertGe(block.basefee, 20 gwei);
    }
}
