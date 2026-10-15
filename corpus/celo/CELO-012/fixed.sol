// Corpus CELO-012 (fixed). PREVRANDAO (still predictable-ish; use a VRF for value at stake).
pragma solidity ^0.8.20;
contract Lottery {
    function draw(uint256 n) external view returns (uint256) { return block.prevrandao % n; }
}
