// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-005 (fixed): wall-clock delay with block.timestamp (unaffected by Denim).
contract TimelockFixed {
    uint256 public constant DELAY = 1 days;
    mapping(bytes32 => uint256) public readyAt;

    function queue(bytes32 id) external { readyAt[id] = block.timestamp + DELAY; }
    function execute(bytes32 id) external view returns (bool) { return readyAt[id] != 0 && block.timestamp >= readyAt[id]; }
}
