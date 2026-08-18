import Link from "next/link";

export default function AcceptableUsePage() {
  return <main className="legalPage"><p className="eyebrow">在线体验 / 使用要求</p><h1>可接受使用政策</h1><p className="lede">只使用你有权处理的材料，并优先使用虚构或妥善脱敏的数据。当前免费试用只在浏览器内处理文件，不提供账号、云端保存或在线模型服务。</p><section><h2>禁止用途</h2><p>不得上传个人、客户、机密、支付、健康、登录凭证或其他敏感数据；不得生成违法、侵权、冒充、欺骗、歧视、骚扰、未经证实或虚假宣称获得批准的内容；不得用于医疗、就业、住房、教育、信贷、保险、法律服务等高影响决策。</p></section><section><h2>系统与平台安全</h2><p>不得传播恶意软件、钓鱼、账号盗取或垃圾信息，不得探测他人数据、绕过访问限制、过度占用服务或掩盖自动化滥用。</p></section><section><h2>发布责任</h2><p>自动检查和页面内确认均不转移发布责任。对外使用前必须完成最新的商品资料、法律、平台、品牌、知识产权和目标语言审核。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/ACCEPTABLE_USE_POLICY.md">查看仓库原文 ↗</a></p></main>;
}
