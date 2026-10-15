// Corpus CELO-012 (vulnerable). Uses the deactivated Celo Random contract.
pragma solidity ^0.8.20;
interface IRandom { function random() external view returns (bytes32); }
contract Lottery {
    IRandom public rng;
    constructor(IRandom r) { rng = r; }
    function draw(uint256 n) external view returns (uint256) { return uint256(rng.random()) % n; }
}
