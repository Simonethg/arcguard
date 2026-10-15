// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Test double for the 6-decimal ERC-20 view. Not a case under scan.
///         In-process arc-forge does not predeploy USDC; fork tests hit the
///         real precompile. This mock only makes unit math executable.
contract MockUsdc {
    mapping(address => uint256) public balanceOf;
    uint8 public constant decimals = 6;
    address public lastTo;
    uint256 public lastAmount;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(to != address(0), "mock zero");
        require(balanceOf[msg.sender] >= amount, "mock balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        lastTo = to;
        lastAmount = amount;
        return true;
    }
}
