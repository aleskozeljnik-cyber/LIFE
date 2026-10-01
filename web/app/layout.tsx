import type { Metadata } from "next";
import type { ReactNode } from "react";
import ErrorBoundary from "./ErrorBoundary";

export const metadata: Metadata = {
  title: "LIFE · Personal OS",
  description: "A private personal command center for commitments, inbox and calendar.",
  applicationName: "LIFE",
  appleWebApp: { capable: true, title: "LIFE", statusBarStyle: "default" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body><ErrorBoundary>{children}</ErrorBoundary></body>
    </html>
  );
}
