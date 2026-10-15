// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IBomb {
    function destroy() external;
}

/// Positive ARC-007: selfdestruct beneficiaries, assembly, and a later value send.
contract MovesUsdc {
    function toSelf() external {
        selfdestruct(payable(address(this)));
    }

    function toZero() external {
        selfdestruct(payable(address(0)));
    }

    function toBeneficiary(address payable beneficiary) external {
        selfdestruct(beneficiary);
    }

    function viaAssembly(address payable beneficiary) external {
        assembly {
            selfdestruct(beneficiary)
        }
    }
}

contract AfterDestroy {
    function go(address payable bomb) external payable {
        IBomb(bomb).destroy();
        (bool ok,) = bomb.call{value: 1}("");
        require(ok, "native send failed");
    }
}
