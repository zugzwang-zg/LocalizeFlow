import Link from "next/link";

export default function TermsPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / TERMS</p><h1>预览版使用条款</h1><p className="lede">本条款只描述当前公开 Demo 与仓库预览软件，不是托管账号或免费试用服务条款。软件依 Apache-2.0 许可按“现状”提供。</p><section><h2>你的权利与责任</h2><p>你必须有权使用输入到本地安装中的材料，并对输入、指令、编辑、终稿和发布决定负责。发布前须核对商品事实、明示和暗示宣称、译文、价格、知识产权、当前平台规则及适用法律。Demo 不会自动发布内容，也不应接收个人、客户、机密、生产或受监管数据。</p></section><section><h2>自动化与模拟材料</h2><p>检查和模型辅助内容可能不完整、过时或错误；检查通过不代表专业或平台批准。仓库中的品牌、SKU、商品事实、价格、营销内容和评测材料均为 AI 生成的虚构示例，不对应真实商品、客户、结果或背书。</p></section><section><h2>可接受使用</h2><p>不得绕过安全、访问或配额控制，不得用于违法、侵权、欺骗、未经证实的医疗化宣称或高影响决策。完整边界见 <Link href="/acceptable-use">可接受使用政策</Link>。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/TERMS.md">查看仓库原文 ↗</a></p></main>;
}
