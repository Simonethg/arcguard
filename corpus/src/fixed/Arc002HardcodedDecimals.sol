// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IUsdc} from "../lib/IUsdc.sol";
import {UsdcUnits} from "../lib/UsdcUnits.sol";

/// @title ARC-002 fixed — decimals follow the view being used
/// @notice Native payments use 18 decimals. ERC-20 transfers use 6 decimals.
///         The unit is derived from UsdcUnits, not from a literal pasted onto
///         the wrong view.
/// @dev Rule: usdc-decimals-hardcoded.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc002HardcodedDecimalsFixed {
    error NeedOneUsdc(uint256 sentNative, uint256 requiredNative);
    error TransferFailed();

    IUsdc public immutable usdc;

    constructor(address usdc_) {
        usdc = IUsdc(usdc_);
    }

    function oneErc20() public pure returns (uint256) {
        return 10 ** uint256(UsdcUnits.ERC20_DECIMALS);
    }

    function oneNative() public pure returns (uint256) {
        return UsdcUnits.erc20ToNative(oneErc20());
    }

    function requireNativePayment() external payable {
        uint256 requiredNative = oneNative();
        if (msg.value < requiredNative) revert NeedOneUsdc(msg.value, requiredNative);
    }

    function payErc20(address to) external {
        bool ok = usdc.transfer(to, oneErc20());
        if (!ok) revert TransferFailed();
    }
}
