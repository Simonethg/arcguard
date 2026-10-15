// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IUsdc} from "../lib/IUsdc.sol";
import {UsdcUnits} from "../lib/UsdcUnits.sol";

/// @title ARC-004 fixed — use the ERC-20 USDC interface, do not wrap
/// @notice Canonical USDC on Arc testnet (and the same address on mainnet,
///         which this corpus does not target): 0x3600...0000.
///         Native value is accounted by scaling to 6 decimals. There is no
///         wrap or unwrap step.
/// @dev Rule: weth-pattern.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc004WethPatternFixed {
    error TransferFailed();

    address public constant USDC = 0x3600000000000000000000000000000000000000;

    mapping(address => uint256) public creditedErc20;

    function receiveNative() external payable {
        creditedErc20[msg.sender] += UsdcUnits.nativeToErc20(msg.value);
    }

    function sendErc20(address to, uint256 amountErc20) external {
        bool ok = IUsdc(USDC).transfer(to, amountErc20);
        if (!ok) revert TransferFailed();
    }
}
