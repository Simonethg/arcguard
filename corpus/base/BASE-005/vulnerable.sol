// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-005 (vulnerable). "1 day" assuming 2s blocks; after Denim (200ms) it lasts ~2.4 hours.
contract TimelockVulnerable {
    uint256 public constant DELAY_BLOCKS = 43_200;
    mapping(bytes32 => uint256) public readyAt;

    function queue(bytes32 id) external { readyAt[id] = block.number + DELAY_BLOCKS; }
    function execute(bytes32 id) external view returns (bool) { return readyAt[id] != 0 && block.number >= readyAt[id]; }
}
