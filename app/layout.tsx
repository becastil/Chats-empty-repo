import type { Metadata } from "next";
import { headers } from "next/headers";
import { SITE_DESCRIPTION, SITE_TITLE, SITE_URL } from "./site-config";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const forwardedHost = requestHeaders.get("x-forwarded-host")?.split(",")[0].trim();
  const host = forwardedHost || requestHeaders.get("host") || "localhost";
  const forwardedProtocol = requestHeaders
    .get("x-forwarded-proto")
    ?.split(",")[0]
    .trim();
  const protocol =
    forwardedProtocol === "http" || forwardedProtocol === "https"
      ? forwardedProtocol
      : host.startsWith("localhost")
        ? "http"
        : "https";
  let origin = "http://localhost";

  try {
    origin = new URL(`${protocol}://${host}`).origin;
  } catch {
    // Keep metadata valid when a development proxy sends a malformed host.
  }

  const imageUrl = `${origin}/og.png`;
  return {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    alternates: { canonical: `${SITE_URL}/` },
    robots: { index: true, follow: true },
    openGraph: {
      title: SITE_TITLE,
      description: SITE_DESCRIPTION,
      type: "website",
      url: `${SITE_URL}/`,
      images: [{ url: imageUrl, width: 1200, height: 630, alt: SITE_DESCRIPTION }],
    },
    twitter: {
      card: "summary_large_image",
      title: SITE_TITLE,
      description: SITE_DESCRIPTION,
      images: [imageUrl],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
