import Link from "next/link";

export default function StatusPage() {
  return <main className="legalPage"><p className="eyebrow">MANUAL STATUS / 2026-08-16</p><h1>服务状态</h1><p className="lede">公开确定性 Demo 提供预览入口，但没有持续可用性监控，请以实际页面访问结果为准。托管账号、真实资料上传、托管模型调用和托管内容导出均未开放。</p><section><h2>当前运行边界</h2><p>公开 Demo 使用冻结虚拟材料，只在浏览器中处理，不调用模型 API。仓库与 Streamlit Demo 可在用户自己的本地环境运行。当前没有托管免费试用。</p></section><section><h2>状态说明的局限</h2><p>这是人工维护的状态说明，不是实时状态页、独立可用性探针或正常运行时间保证。过期的核验日期不能作为服务可用证据；未来托管试用必须接入外部探针、持久化指标和服务外告警渠道。</p></section><section><h2>报告问题</h2><p>一般问题请使用 <Link href="/support">支持页面</Link>。安全漏洞或疑似数据泄露请使用仓库 SECURITY.md 中的私密渠道，不要提交公开 Issue。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/STATUS.md">查看仓库状态原文 ↗</a></p></main>;
}
