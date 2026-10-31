import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DraftMark — weigh a ship's cargo from a phone video of its draft marks",
  description:
    "SAM 3.1 measures the waterline through the swell; Muse Wonder 1.0 writes and proves a survey program for the ship; code prints every number.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
