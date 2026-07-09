import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Repo Scout | Local repository intelligence",
  description:
    "A compact, dependency-free snapshot of a local repository for reviews and handoffs.",
};

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
