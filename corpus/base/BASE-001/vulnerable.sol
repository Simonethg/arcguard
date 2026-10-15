// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Corpus BASE-001 (vulnerable). Illustrative only; interface trimmed from docs.base.org B20 policies.
interface IPolicyRegistry {
    enum PolicyType { ALLOWLIST, BLOCKLIST, UNION, INTERSECT }
    function createCompositePolicy(address admin, PolicyType t, uint64[] calldata children) external returns (uint64);
}
contract TransferGateVulnerable {
    function build(IPolicyRegistry reg, uint64 kycAllowlistId, uint64 sanctionsBlocklistId) external returns (uint64) {
        uint64[] memory children = new uint64[](2);
        children[0] = kycAllowlistId;
        children[1] = sanctionsBlocklistId;
        // OR: a KYC'd but sanctioned account still passes because the KYC child authorizes it.
        return reg.createCompositePolicy(msg.sender, IPolicyRegistry.PolicyType.UNION, children);
    }
}
