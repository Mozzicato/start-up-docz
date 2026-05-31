/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    typedRoutes: true
  },
  // Proxy API calls to the backend. In the combined container the backend runs
  // on 127.0.0.1:8000; override with BACKEND_INTERNAL_URL if needed.
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  }
};

export default nextConfig;
