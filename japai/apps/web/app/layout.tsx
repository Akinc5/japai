import "./globals.css";

export const metadata = {
  title: "JA Assure AI Marketing OS",
  description: "AI Marketing OS — Phase 1 foundation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
