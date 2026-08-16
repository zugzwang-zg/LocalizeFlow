import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  const title = "LocalizeFlow｜证据驱动的跨境内容工作台";
  const description = "独立主导的 AI 产品作品集：把商品事实、目标市场语言与平台规则放进可追溯、失败关闭的内容工作流。公开 Demo 不调用模型 API。";
  return {
    title,
    description,
    openGraph: { title, description, images: [{ url: `${origin}/og-portfolio.png`, width: 1536, height: 1024 }] },
    twitter: { card: "summary_large_image", title, description, images: [`${origin}/og-portfolio.png`] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
