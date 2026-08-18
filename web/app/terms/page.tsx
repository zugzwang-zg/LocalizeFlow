import Link from "next/link";

export default function TermsPage() {
  return <main className="legalPage"><p className="eyebrow">在线体验 / 使用条款</p><h1>预览版使用条款</h1><p className="lede">本条款适用于当前在线体验、浏览器内免费试用与仓库预览软件。它不提供账号、云端保存或在线模型服务；软件依 Apache-2.0 许可按“现状”提供。</p><section><h2>你的权利与责任</h2><p>你必须有权使用输入到本地安装或浏览器中的材料，并对输入、编辑、最终内容和发布决定负责。发布前须核对商品资料、明确或暗示的效果、译文、价格、知识产权、当前发布要求及适用法律。页面不会自动发布内容，也不应接收个人、客户、机密、生产或受监管数据。</p></section><section><h2>自动检查与模拟材料</h2><p>自动检查和内容草稿可能不完整、过时或错误；检查通过不代表专业人员或平台批准。仓库中的品牌、商品编号、商品资料、价格、营销内容和评测材料均为 AI 生成的虚构示例，不对应真实商品、客户、结果或背书。</p></section><section><h2>可接受使用</h2><p>不得绕过安全、访问或使用次数限制，不得用于违法、侵权、欺骗、未经证实的医疗效果宣称或高影响决策。完整边界见 <Link href="/acceptable-use">可接受使用政策</Link>。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/TERMS.md">查看仓库原文 ↗</a></p></main>;
}
