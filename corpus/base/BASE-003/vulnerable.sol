// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-003 (vulnerable). This helper holds SEIZE_ROLE on the token and exposes seize to anyone.
interface IB20 {
    function seizeWithMemo(address from, address to, uint256 amount, bytes32 memo) external;
}
contract SeizeHelperVulnerable {
    IB20 public immutable token;
    address public immutable treasury;
    constructor(IB20 t, address tr) { token = t; treasury = tr; }

    function forfeit(address holder, uint256 amount) external {
        token.seizeWithMemo(holder, treasury, amount, bytes32(0));
    }
}
