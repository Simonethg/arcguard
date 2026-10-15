// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/// Demo fixture. Vulnerable on Arc. Do not deploy.
/// Sources: https://docs.arc.io/arc/references/evm-differences
contract VulnerablePort {
    function mix(IERC20 usdc, uint256 price) external payable {
        require(msg.value == price, "unscaled");
        usdc.transfer(msg.sender, price);
    }

    function burnNative() external payable {
        address payable sink = payable(address(0));
        (bool ok, ) = sink.call{value: msg.value}("");
        ok;
    }

    function draw() external view returns (uint256) {
        return uint256(block.prevrandao);
    }

    function close() external {
        selfdestruct(payable(msg.sender));
    }

    function wrap(WETH weth) external payable {
        weth.deposit{value: msg.value}();
    }
}

interface WETH {
    function deposit() external payable;
}
