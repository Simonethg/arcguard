// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title NaiveEthereumPort — intentionally wrong patterns for Arc
/// @notice Port of https://github.com/Simonethg/scaffold-arc
///         packages/foundry/src/examples/NaiveEthereumPort.sol (MIT).
///         DO NOT USE IN PRODUCTION. Exists so tests and the scanner can
///         prove why copying Ethereum ETH/ERC-20 mental models onto Arc USDC
///         produces wrong accounting (off by 10^12) or unsafe assumptions.
///
///         On Ethereum, native ETH (18 decimals) and an ERC-20 USDC (6 decimals)
///         are different assets. On Arc they are the same funds under two views.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
library NaiveEthereumPort {
    /// @dev WRONG on Arc: compares raw msg.value (18 decimals) to an ERC-20 amount (6 decimals).
    function naiveValueCoversErc20(uint256 msgValue, uint256 requiredErc20)
        internal
        pure
        returns (bool)
    {
        return msgValue >= requiredErc20;
    }

    /// @dev WRONG on Arc: adds native balance to ERC-20 balanceOf as if they
    ///      were two separate assets (double-counts the same USDC).
    function naiveTotalBalance(uint256 nativeBalance, uint256 erc20Balance)
        internal
        pure
        returns (uint256)
    {
        return nativeBalance + erc20Balance;
    }

    /// @dev WRONG on Arc: treats balanceOf == 0 as "account is empty".
    ///      The ERC-20 view truncates anything below 10^12 native units.
    function naiveIsEmpty(uint256 erc20Balance) internal pure returns (bool) {
        return erc20Balance == 0;
    }
}
