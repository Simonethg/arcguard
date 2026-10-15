// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

/// Positive ARC-003: the two USDC views are stored and added as two assets.
contract NativeErc20Pool {
    IERC20 usdc;
    uint256 public reserveNative;
    uint256 public reserveToken;

    function totalAssets() external view returns (uint256) {
        return address(this).balance + usdc.balanceOf(address(this));
    }

    function sync() external {
        reserveNative = address(this).balance;
        reserveToken = usdc.balanceOf(address(this));
    }
}
