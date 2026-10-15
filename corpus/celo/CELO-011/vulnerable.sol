// Corpus CELO-011 (vulnerable). Calls the removed epochSize precompile (Celo L1).
pragma solidity ^0.8.20;
contract Epochs {
    address constant EPOCH_SIZE = address(0xff - 7);
    function epochSize() public view returns (uint256 size) {
        (bool ok, bytes memory out) = EPOCH_SIZE.staticcall("");
        require(ok);
        size = abi.decode(out, (uint256));
    }
}
