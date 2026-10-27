import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroLab AI — Field Evidence Lab",
  description:
    "Explore auditable observational evidence from Ghana maize field trials with NeuroLab's bounded research agent.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
