// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Regression: calling another contract's public state-variable getter.
/// Slither resolves the callee to a StateVariable, not a Function; the engine
/// used to crash on it (seen on a launchpad that reads its token's getters).
contract GetterToken {
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    uint8 public constant decimals = 18;

    function mint(address to, uint256 amount) external {
        totalSupply += amount;
        balanceOf[to] += amount;
    }
}

contract GetterReader {
    function supplyOf(GetterToken token) external view returns (uint256) {
        return token.totalSupply();
    }

    function heldBy(GetterToken token, address who) external view returns (uint256) {
        return token.balanceOf(who);
    }

    function payout(GetterToken token, address payable to) external {
        uint256 amount = token.balanceOf(address(this));
        (bool ok,) = to.call{value: amount}("");
        require(ok, "send failed");
    }
}
