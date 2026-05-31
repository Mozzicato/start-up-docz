import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StartupDocs",
  description: "AI-powered startup planning workspace"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="grain" />
        {children}
      </body>
    </html>
  );
}
