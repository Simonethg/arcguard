// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

/// Negative ARC-003: native value is scaled to 6 decimals before it is added.
contract OneAsset {
    IERC20 usdc;
    uint256 constant SCALE = 10 ** 12;

    function totalAssets() external view returns (uint256) {
        return address(this).balance / SCALE + usdc.balanceOf(address(this));
    }
}
