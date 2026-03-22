import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "画宗制片中枢",
  description: "AI 影视制片管理平台 — 分镜管理、风格定调、团队协作",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
