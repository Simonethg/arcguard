// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IUsdc} from "../lib/IUsdc.sol";

/// @title ARC-002 vulnerable — hardcoded decimal assumptions
/// @notice Do not deploy. Treats native `msg.value` as 6 decimals (`1e6`)
///         and the ERC-20 amount as 18 decimals (`10**18`).
/// @dev Rule: usdc-decimals-hardcoded.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc002HardcodedDecimalsVulnerable {
    IUsdc public immutable usdc;

    /// @dev Wrong unit for native USDC. One USDC native is 10^18, not 10^6.
    uint256 public constant ONE_NATIVE = 1e6;

    constructor(address usdc_) {
        usdc = IUsdc(usdc_);
    }

    function requireNativePayment() external payable {
        require(msg.value >= 1e6, "need 1 token");
        require(msg.value >= ONE_NATIVE, "need 1 token constant");
    }

    function payErc20(address to) external {
        usdc.transfer(to, 10 ** 18);
    }
}
