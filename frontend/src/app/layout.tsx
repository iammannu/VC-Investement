import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AI Investment Memo Generator",
  description: "Transform pitch decks into professional investment memos in minutes",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#0f172a",
                color: "#f8fafc",
                fontSize: "14px",
                borderRadius: "8px",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
