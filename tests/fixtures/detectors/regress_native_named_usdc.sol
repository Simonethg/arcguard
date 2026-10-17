// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Regression: a reserve named "...Usdc" that holds native USDC wei (18 dec),
/// filled from msg.value. Multiplying it by 1e18 to price a whole 18-dec token
/// is correct on Arc and must not be reported as ARC-002.
contract NativeReserveCurve {
    uint256 public immutable virtualUsdc; // native wei
    uint256 public immutable virtualTokens;
    uint256 public realUsdc; // native wei
    uint256 public sold;

    constructor(uint256 virtualUsdc_, uint256 virtualTokens_) {
        virtualUsdc = virtualUsdc_;
        virtualTokens = virtualTokens_;
    }

    function buy() external payable {
        (uint256 net, uint256 tokens) = _quote(msg.value);
        realUsdc += net;
        sold += tokens;
    }

    function _quote(uint256 usdcIn) internal view returns (uint256 net, uint256 tokens) {
        net = usdcIn - usdcIn / 100;
        tokens = net * (virtualTokens - sold) / (virtualUsdc + realUsdc + net);
    }

    function price() external view returns (uint256) {
        return (virtualUsdc + realUsdc) * 1e18 / (virtualTokens - sold);
    }
}

/// Control: the same name-only pattern in a contract that never touches native
/// value is still ARC-002 (an ERC-20 USDC amount scaled by 1e18).
contract Erc20OnlyScaler {
    function toWad(uint256 usdcAmount) external pure returns (uint256) {
        return usdcAmount * 1e18;
    }
}
