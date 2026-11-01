/** Next.js UI + Python (FastAPI) functions under /api/py/* (Vercel's Next.js + FastAPI pattern). */
const nextConfig = {
  rewrites: async () => [
    // The judge-facing landing is one static file (public/index.html); the deck and the judge path are static pages in the same system; the recorded runs live at /runs.
    { source: "/", destination: "/index.html" },
    { source: "/deck", destination: "/deck/index.html" },
    { source: "/judge", destination: "/judge/index.html" },
    {
      source: "/api/py/:path*",
      destination: process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000/api/py/:path*" : "/api/",
    },
  ],
};
export default nextConfig;
