// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @dev Ethereum mainnet WETH surface. Arc has no WETH-style wrapper for USDC.
interface IWETH {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
}

/// @title ARC-004 vulnerable — WETH deposit/withdraw ported onto Arc
/// @notice Do not deploy. Wraps native value through the Ethereum WETH
///         constant and unwraps it back. On Arc the ERC-20 USDC interface
///         already exposes the native balance; a wrapper fragments liquidity.
/// @dev Rule: weth-pattern.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc004WethPatternVulnerable {
    address public constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    function wrap() external payable {
        IWETH(WETH).deposit{value: msg.value}();
    }

    function unwrap(uint256 amount) external {
        IWETH(WETH).withdraw(amount);
    }
}
