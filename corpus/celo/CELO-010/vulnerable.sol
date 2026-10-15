// Corpus CELO-010 (vulnerable). Timelock in blocks assuming Celo L1 5 s blocks.
pragma solidity ^0.8.20;
contract Timelock {
    uint256 public constant BLOCKS_PER_DAY = 17280;
    uint256 public unlockBlock;
    function queue() external { unlockBlock = block.number + 2 * BLOCKS_PER_DAY; }
    function execute() external view { require(block.number >= unlockBlock, "locked"); }
}
