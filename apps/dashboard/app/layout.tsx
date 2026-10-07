import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { Cinzel, DM_Sans, DM_Mono, Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import { CookieBanner } from "@/app/(components)/(privacy)/CookieBanner";
import { PrivacyNotice } from "@/app/(components)/(privacy)/PrivacyNotice";
import "./globals.css";
import { QueryProvider, SupabaseProvider } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const focusDisplay = Cinzel({
  variable: "--font-focus-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const dmMono = DM_Mono({
  variable: "--font-dm-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const SITE_DESCRIPTION =
  "Two-tiered detection of volcanic unrest from satellite deformation and seismic waveforms.";

export const metadata: Metadata = {
  metadataBase: new URL("https://fiery-spirit.earth"),
  title: { default: "Fiery Spirit", template: "%s | Fiery Spirit" },
  description: SITE_DESCRIPTION,
  openGraph: {
    title: "Fiery Spirit",
    description: SITE_DESCRIPTION,
    url: "/",
    siteName: "Fiery Spirit",
    images: [{ url: "/og.png" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Fiery Spirit",
    description: SITE_DESCRIPTION,
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${focusDisplay.variable} ${dmSans.variable} ${dmMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <SupabaseProvider>{children}</SupabaseProvider>
        </QueryProvider>
        <CookieBanner />
        <PrivacyNotice />
        <Toaster richColors closeButton position="top-center" />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
