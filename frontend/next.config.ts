import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Real, license-clear stock photography (Unsplash CDN) used for hero
    // banners, category tiles and trust sections across the site — never
    // for the individual per-medicine product-photo slots, which stay
    // generic icon placeholders on purpose.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
};

export default nextConfig;
