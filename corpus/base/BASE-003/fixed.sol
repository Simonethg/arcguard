// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-003 (fixed): only the compliance operator can seize, and every seizure carries a reason.
interface IB20 {
    function seizeWithMemo(address from, address to, uint256 amount, bytes32 memo) external;
}
contract SeizeHelperFixed {
    IB20 public immutable token;
    address public immutable treasury;
    address public immutable compliance;
    constructor(IB20 t, address tr, address c) { token = t; treasury = tr; compliance = c; }

    function forfeit(address holder, uint256 amount, bytes32 reason) external {
        require(msg.sender == compliance, "not compliance");
        require(reason != bytes32(0), "memo required");
        token.seizeWithMemo(holder, treasury, amount, reason);
    }
}
