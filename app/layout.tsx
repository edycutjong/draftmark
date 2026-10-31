import type { Metadata, Viewport } from "next";
import { Anybody, IBM_Plex_Sans, Martian_Mono } from "next/font/google";
import { SiteFooter } from "@/components/SiteChrome";
import "./globals.css";

const display = Anybody({ subsets: ["latin"], axes: ["wdth"], variable: "--ff-display", display: "swap" });
const body = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--ff-body", display: "swap" });
const data = Martian_Mono({ subsets: ["latin"], variable: "--ff-data", display: "swap" });

export const metadata: Metadata = {
  title: "DraftMark — weigh a ship's cargo from a phone video of its draft marks",
  description:
    "SAM 3.1 measures the waterline through the swell; Muse Wonder 1.0 writes and proves a survey program for the ship; code prints every number.",
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
