// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title Minimal ERC-20 surface of Arc USDC
/// @notice The canonical token is 0x3600000000000000000000000000000000000000
///         on Arc testnet and mainnet. This corpus only targets testnet and
///         local arc-anvil. The interface uses 6 decimals; native balances
///         use 18. They are one asset.
/// @dev https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
interface IUsdc {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function decimals() external view returns (uint8);
}
