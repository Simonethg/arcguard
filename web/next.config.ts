import type { NextConfig } from "next";

// No analytics, no remote images, no third-party scripts.
const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
