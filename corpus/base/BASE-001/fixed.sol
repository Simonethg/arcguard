// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-001 (fixed): INTERSECT = on KYC AND not sanctioned (docs.base.org, Policies §4.2).
interface IPolicyRegistry {
    enum PolicyType { ALLOWLIST, BLOCKLIST, UNION, INTERSECT }
    function createCompositePolicy(address admin, IPolicyRegistry.PolicyType t, uint64[] calldata children) external returns (uint64);
}
contract TransferGateFixed {
    function build(IPolicyRegistry reg, uint64 kycAllowlistId, uint64 sanctionsBlocklistId) external returns (uint64) {
        uint64[] memory children = new uint64[](2);
        children[0] = kycAllowlistId;
        children[1] = sanctionsBlocklistId;
        return reg.createCompositePolicy(msg.sender, IPolicyRegistry.PolicyType.INTERSECT, children);
    }
}
