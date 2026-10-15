// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Negative ARC-001: both sides are scaled by 1e12 before they meet.
contract ScaledMix {
    IERC20 usdc;
    uint256 constant SCALE = 10 ** 12;

    function pay(uint256 priceUsdc) external payable {
        require(msg.value / SCALE >= priceUsdc, "short");
    }

    function credit(uint256 amountErc20) external payable {
        usdc.transfer(msg.sender, amountErc20);
        require(msg.value / 1e12 >= amountErc20, "short");
    }

    function cover(uint256 nativeAmount, uint256 requiredErc20) external pure returns (bool) {
        return nativeToErc20(nativeAmount) >= requiredErc20;
    }

    function nativeToErc20(uint256 nativeAmount) public pure returns (uint256) {
        return nativeAmount / 1e12;
    }
}

library ScaledPort {
    function covers(uint256 msgValue, uint256 priceErc20) internal pure returns (bool) {
        return msgValue >= priceErc20 * 1e12;
    }
}

/// Real msg.value passed into a helper that scales before comparing.
contract ScaledCheckout {
    uint256 public immutable priceErc20;

    constructor(uint256 priceErc20_) {
        priceErc20 = priceErc20_;
    }

    function buy() external payable returns (bool) {
        return ScaledPort.covers(msg.value, priceErc20);
    }
}
