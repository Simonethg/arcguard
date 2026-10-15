// Corpus CELO-011 (fixed). Reads the epoch length from configuration instead of a precompile.
pragma solidity ^0.8.20;
contract Epochs {
    uint256 public immutable epochLength;
    constructor(uint256 len) { epochLength = len; }
}
