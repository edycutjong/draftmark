import type { Metadata, Viewport } from "next";
import { Anybody, IBM_Plex_Sans, Martian_Mono } from "next/font/google";
import { SiteFooter } from "@/components/SiteChrome";
import "./globals.css";

const display = Anybody({ subsets: ["latin"], axes: ["wdth"], variable: "--ff-display", display: "swap" });
const body = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--ff-body", display: "swap" });
const data = Martian_Mono({ subsets: ["latin"], variable: "--ff-data", display: "swap" });

// Social card: public/og-image.png is EXACTLY 1200x630 (< 500 KB). Bump ?v= whenever the image changes —
// platforms cache cards by URL, so a regenerated image without a new query string is never seen.
const OG_IMAGE = "/og-image.png?v=2";
const CARD_TITLE = "DraftMark — weigh a ship's cargo from a phone video";
const CARD_DESCRIPTION =
  "SAM 3.1 measures the waterline through the swell; Muse Wonder 1.0 writes and proves the ship's survey program.";

export const metadata: Metadata = {
  metadataBase: new URL("https://draftmark.edycu.dev"),
  title: "DraftMark — weigh a ship's cargo from a phone video of its draft marks",
  description:
    "SAM 3.1 measures the waterline through the swell; Muse Wonder 1.0 writes and proves a survey program for the ship; code prints every number.",
  authors: [{ name: "Edy Cu Tjong", url: "https://github.com/edycutjong" }],
  creator: "Edy Cu Tjong",
  icons: { icon: [{ url: "/icon.svg", type: "image/svg+xml" }], apple: "/icon-512.png" },
  openGraph: {
    type: "website",
    url: "/",
    siteName: "DraftMark",
    title: CARD_TITLE,
    description: CARD_DESCRIPTION,
    images: [
      {
        url: OG_IMAGE,
        width: 1200,
        height: 630,
        alt: "DraftMark — weigh a ship's cargo from a phone video of its draft marks; Muse Wonder's program reproduced 22/22 printed booklet conditions",
      },
    ],
  },
  twitter: { card: "summary_large_image", title: CARD_TITLE, description: CARD_DESCRIPTION, images: [OG_IMAGE] },
};

export const viewport: Viewport = { themeColor: "#17120F", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${data.variable}`}>
      <body>
        <a href="#main" className="skip">
          Skip to content
        </a>
        <div id="main">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
