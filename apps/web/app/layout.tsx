import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "KnowledgeForge AI — Your knowledge, connected",
  description: "A source-grounded intelligence workspace for your team.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
