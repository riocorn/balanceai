import type { MetadataRoute } from "next";

// Matches the domain already referenced in public/robots.txt.
const SITE_URL = "https://balanceai.app";

// Real, public, indexable routes only — account/cart/dashboard pages are
// excluded here (and disallowed in robots.ts) since they carry no unique
// public content and shouldn't be crawled.
export default function sitemap(): MetadataRoute.Sitemap {
  const routes: { path: string; priority: number; changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"] }[] = [
    { path: "/", priority: 1, changeFrequency: "weekly" },
    { path: "/symptom-checker", priority: 1, changeFrequency: "weekly" },
    { path: "/pharmacy", priority: 0.9, changeFrequency: "weekly" },
    { path: "/consult-a-doctor", priority: 0.8, changeFrequency: "monthly" },
    { path: "/wellness", priority: 0.8, changeFrequency: "weekly" },
    { path: "/medicines", priority: 0.9, changeFrequency: "daily" },
    { path: "/medicines/by-category", priority: 0.7, changeFrequency: "weekly" },
    { path: "/legal/privacy-policy", priority: 0.3, changeFrequency: "yearly" },
    { path: "/legal/terms-of-service", priority: 0.3, changeFrequency: "yearly" },
    { path: "/legal/medical-disclaimer", priority: 0.3, changeFrequency: "yearly" },
  ];

  return routes.map(({ path, priority, changeFrequency }) => ({
    url: `${SITE_URL}${path}`,
    lastModified: new Date(),
    changeFrequency,
    priority,
  }));
}
