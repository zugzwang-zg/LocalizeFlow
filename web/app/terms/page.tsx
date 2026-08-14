import Link from "next/link";

export default function TermsPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / TERMS</p><h1>预览版使用条款</h1><p className="lede">LocalizeFlow 以 Apache-2.0 提供早期预览，用于评估、学习与贡献；软件按“现状”提供，不保证准确性、可用性、平台批准、法律合规或特定用途适用性。</p><section><h2>你的责任</h2><p>发布前必须自行核对商品事实、声明、译文、价格、平台规则、当地法律和最终发布决定。Demo 不会自动发布内容，也不应接收机密信息、个人数据、生产凭证或受监管决策数据。</p></section><section><h2>模拟材料</h2><p>品牌、SKU、商品事实、价格、营销内容和评测材料均为 AI 生成的虚构示例，不对应真实商品或背书。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/TERMS.md">查看仓库原文 ↗</a></p></main>;
}
