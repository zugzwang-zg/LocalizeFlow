import Link from "next/link";

export default function AcceptableUsePage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / ACCEPTABLE USE</p><h1>可接受使用政策</h1><p className="lede">只使用你有权处理的材料，并优先使用虚构或妥善脱敏的数据评估本项目。当前没有托管免费试用。</p><section><h2>禁止用途</h2><p>不得上传个人、客户、机密、支付、健康、凭证或其他敏感数据；不得生成违法、侵权、冒充、欺骗、歧视、骚扰、未经证实或宣称虚假批准的内容；不得用于医疗、就业、住房、教育、信贷、保险、法律服务等高影响决策。</p></section><section><h2>系统与平台安全</h2><p>不得传播恶意软件、钓鱼、凭证盗取或垃圾信息，不得探测他人数据、跨越租户边界、绕过访问控制或配额、压垮服务或掩盖滥用自动化。</p></section><section><h2>发布责任</h2><p>自动检查和工作流内人工确认均不转移发布责任。外部使用前必须完成最新的事实、法律、平台、品牌、知识产权和目标语言审核。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/ACCEPTABLE_USE_POLICY.md">查看仓库原文 ↗</a></p></main>;
}
