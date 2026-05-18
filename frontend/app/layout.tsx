import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BI - Billionaire Intelligence",
  description: "Decision-pattern retrieval for founder and investor decisions",
  icons: {
    icon: "/favicon.svg"
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
