// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function decimals() external view returns (uint8);
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Negative ARC-002: 1e12 gap, decimals() subtracted from 18, whole dollars * 1e6.
contract ScaledDecimals {
    IERC20 usdc;
    uint8 constant NATIVE_DECIMALS = 18;
    uint8 constant ERC20_DECIMALS = 6;
    uint256 constant SCALE = 10 ** (NATIVE_DECIMALS - ERC20_DECIMALS);

    function fromNative(uint256 priceUsdc) external payable returns (bool) {
        return msg.value / SCALE >= priceUsdc;
    }

    function viaDecimals(uint256 priceUsdc) external payable returns (bool) {
        return msg.value / (10 ** (18 - usdc.decimals())) >= priceUsdc;
    }

    function fromWhole(uint256 wholeUsdc) external pure returns (uint256) {
        return wholeUsdc * (10 ** uint256(ERC20_DECIMALS));
    }

    function erc20IsSix() external view returns (bool) {
        return usdc.decimals() == 6;
    }

    function oneNativeUnit() external payable returns (bool) {
        return msg.value >= 1e18;
    }

    function payOneErc20(address to) external {
        usdc.transfer(to, 10 ** 6);
    }
}
