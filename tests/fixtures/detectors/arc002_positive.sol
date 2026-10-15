// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function decimals() external view returns (uint8);
    function transfer(address to, uint256 amount) external returns (bool);
}

/// Positive ARC-002: 6 decimals on native value, 18 on an ERC-20 amount.
contract HardcodedDecimals {
    IERC20 usdc;

    function fromNative() external payable returns (uint256) {
        return msg.value / 1e6;
    }

    function fromErc20(uint256 erc20Bal) external pure returns (uint256) {
        return erc20Bal * 1e18;
    }

    function viaDecimals() external payable returns (uint256) {
        return msg.value / (10 ** usdc.decimals());
    }

    function assumeEighteen() external view returns (bool) {
        return usdc.decimals() == 18;
    }

    uint256 public constant ONE_NATIVE = 1e6;

    function requireNativePayment() external payable {
        require(msg.value >= 1e6, "need 1 token");
        require(msg.value >= ONE_NATIVE, "need 1 token constant");
    }

    function payErc20(address to) external {
        usdc.transfer(to, 10 ** 18);
    }
}
