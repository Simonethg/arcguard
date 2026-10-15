// Corpus CELO-009 (fixed). Counts CELO once.
pragma solidity ^0.8.20;
contract Vault {
    function totalAssets() public view returns (uint256) {
        return address(this).balance;
    }
}
