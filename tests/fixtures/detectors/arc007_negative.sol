// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Negative ARC-007: `destroy` does not selfdestruct, and the send checks its boolean.
/// selfdestruct is intentionally not used.
contract KeepsBalance {
    event Closed(address account);

    function destroy(address account) external {
        emit Closed(account);
    }

    function pay(address payable to) external payable {
        (bool ok,) = to.call{value: msg.value}("");
        require(ok, "native send failed");
    }
}
