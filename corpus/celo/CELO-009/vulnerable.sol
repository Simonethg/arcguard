// Corpus CELO-009 (vulnerable). Double counts CELO: native balance and GoldToken are the same funds.
pragma solidity ^0.8.20;
interface IERC20 { function balanceOf(address) external view returns (uint256); }
contract Vault {
    IERC20 public constant CELO = IERC20(0x471EcE3750Da237f93B8E339c536989b8978a438);
    function totalAssets() public view returns (uint256) {
        return address(this).balance + CELO.balanceOf(address(this));
    }
}
