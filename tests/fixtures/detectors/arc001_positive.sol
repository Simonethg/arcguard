// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Positive ARC-001: raw 18-decimal value combined with 6-decimal USDC amounts.
contract MsgValueMix {
    IERC20 usdc;

    function pay(uint256 priceUsdc) external payable {
        require(msg.value >= priceUsdc, "short");
    }

    function credit() external payable {
        usdc.transfer(msg.sender, msg.value);
    }

    function gap() external view returns (uint256) {
        return address(this).balance - usdc.balanceOf(address(this));
    }
}

/// Canonical Arc USDC address, without relying on the variable name.
contract CanonicalMix {
    function bad() external payable {
        IERC20 token = IERC20(0x3600000000000000000000000000000000000000);
        token.transfer(msg.sender, msg.value);
    }
}

/// Pure helper. The parameter is named msgValue, so the mix is not real msg.value.
library NaivePort {
    function naiveValueCoversErc20(uint256 msgValue, uint256 requiredErc20) internal pure returns (bool) {
        return msgValue >= requiredErc20;
    }
}

/// Call site: real msg.value is passed into the helper. This is the High ARC-001 hit.
contract Checkout {
    uint256 public immutable priceErc20;

    constructor(uint256 priceErc20_) {
        priceErc20 = priceErc20_;
    }

    function buy() external payable returns (bool accepted) {
        accepted = NaivePort.naiveValueCoversErc20(msg.value, priceErc20);
    }
}
