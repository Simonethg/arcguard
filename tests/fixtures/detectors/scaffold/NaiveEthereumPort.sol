// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title NaiveEthereumPort — intentionally wrong patterns for Arc
/// @notice DO NOT USE IN PRODUCTION. Exists so tests can prove why copying
///         Ethereum ETH/ERC-20 mental models onto Arc USDC produces wrong
///         accounting (off by 10^12) or unsafe assumptions.
///
///         On Ethereum, native ETH (18d) and an ERC-20 USDC (6d) are DIFFERENT
///         assets. On Arc they are the SAME funds under two views. These
///         helpers encode the broken comparisons that ports often ship.
library NaiveEthereumPort {
    /// @dev WRONG on Arc: compares raw msg.value (18d) to an ERC-20 amount (6d).
    function naiveValueCoversErc20(uint256 msgValue, uint256 requiredErc20) internal pure returns (bool) {
        return msgValue >= requiredErc20;
    }

    /// @dev WRONG on Arc: adds native balance to ERC-20 balanceOf as if they
    ///      were two separate assets (double-counts the same USDC).
    function naiveTotalBalance(uint256 nativeBalance, uint256 erc20Balance) internal pure returns (uint256) {
        return nativeBalance + erc20Balance;
    }

    /// @dev WRONG on Arc: treats balanceOf == 0 as "account is empty".
    function naiveIsEmpty(uint256 erc20Balance) internal pure returns (bool) {
        return erc20Balance == 0;
    }
}
