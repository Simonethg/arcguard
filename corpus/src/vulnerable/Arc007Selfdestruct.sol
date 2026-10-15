// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-007 vulnerable — selfdestruct moves the contract USDC
/// @notice Do not deploy. On Arc the contract's USDC is its native balance,
///         so SELFDESTRUCT transfers that USDC to the beneficiary. Sending
///         the balance to self or to address(0) reverts. A later non-zero
///         value transfer to an account destroyed in the same transaction
///         reverts as a forbidden burn.
/// @dev Rule: selfdestruct-moves-usdc.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc007SelfdestructVulnerable {
    function fund() external payable {}

    function destroyToSelf() external {
        selfdestruct(payable(address(this)));
    }

    function destroyToZero() external {
        selfdestruct(payable(address(0)));
    }

    function destroyTo(address payable beneficiary) external {
        selfdestruct(beneficiary);
    }
}
