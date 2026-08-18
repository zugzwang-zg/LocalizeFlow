import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  const title = "LocalizeFlow｜跨境商品内容工作台";
  const description = "面向跨境电商内容运营的浏览器工作台：导入商品表格，整理目标市场内容，检查风险并导出处理记录。文件不会上传，也不调用模型 API。";
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
