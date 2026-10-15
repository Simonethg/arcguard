// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Negative ARC-004: vault deposit/withdraw take an amount. They are not WETH.
contract Vault {
    function deposit(uint256 assets) external pure returns (uint256) {
        return assets;
    }

    function withdraw(uint256 assets) external pure returns (uint256) {
        return assets;
    }
}
