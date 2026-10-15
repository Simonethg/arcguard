// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ARC-007 fixed — withdraw native USDC, do not selfdestruct
/// @notice Moves USDC with a checked call. Refuses address(0) and the
///         contract itself. There is no SELFDESTRUCT, so the balance cannot
///         be forwarded as a burn or to a destroyed account by this path.
/// @dev Rule: selfdestruct-moves-usdc.
///      https://docs.arc.io/arc/references/evm-differences
///      https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
///      https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
contract Arc007SelfdestructFixed {
    error BeneficiaryForbidden();
    error WithdrawFailed();

    receive() external payable {}

    function withdraw(address payable to, uint256 amount) external {
        if (to == address(0) || to == payable(address(this))) revert BeneficiaryForbidden();
        (bool ok,) = to.call{value: amount}("");
        if (!ok) revert WithdrawFailed();
    }
}
