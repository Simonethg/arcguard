// Corpus CELO-010 (fixed). Timelock by timestamp; independent of block time.
pragma solidity ^0.8.20;
contract Timelock {
    uint256 public unlockAt;
    function queue() external { unlockAt = block.timestamp + 2 days; }
    function execute() external view { require(block.timestamp >= unlockAt, "locked"); }
}
