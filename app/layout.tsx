import type { Metadata } from "next";
import "./globals.css";
import { ThemePreference } from "./theme-control";

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
      <body>
        <ThemePreference />
        {children}
      </body>
    </html>
  );
}
