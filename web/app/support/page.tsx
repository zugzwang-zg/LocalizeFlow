import Link from "next/link";

export default function SupportPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC PREVIEW / SUPPORT</p><h1>支持与故障报告</h1><p className="lede">当前为开源项目预览，按尽力而为方式维护，不提供 24/7 支持、保证响应时间或托管服务 SLA。</p><section><h2>选择正确渠道</h2><p>安装、确定性 Demo、文档或工作流问题请使用 GitHub Support request；可复现缺陷使用 Bug report。安全漏洞或疑似数据暴露必须遵循 SECURITY.md 使用私密报告，不要创建公开 Issue。</p></section><section><h2>不要提交敏感信息</h2><p>公开工单中不得包含密钥、个人信息、客户正文、未公开商品事实、生产凭证或漏洞利用细节。请使用虚构或妥善脱敏的复现材料，并附版本、受影响页面、预期结果和实际结果。</p></section><section><h2>托管试用状态</h2><p>当前没有托管支持邮箱或隐私请求通道，因为托管试用尚未开放。专用联系渠道、真实告警投递和值守演练仍是上线阻断项。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/issues/new?template=support_request.yml">创建支持工单 ↗</a> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/SUPPORT.md">查看支持政策 ↗</a></p></main>;
}
