import Link from "next/link";

export default function PrivacyPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / PRIVACY</p><h1>隐私说明</h1><p className="lede">本说明只适用于当前浏览器内运行的冻结样本 Demo。它不调用模型 API，不提供托管账号，也不会自动把选择、编辑、反馈或体验指标传给项目维护者。</p><section><h2>本地保存的数据</h2><p>启用本地体验指标后，浏览器最多保存 100 条且不超过 30 天的事件：匿名运行 ID、事件名、时间、耗时、市场、内容类型与步骤；用途仅为你自行检查体验路径。不会记录正文、姓名、邮箱、IP 地址或 API 凭证。你可以在 Demo 终审页停用、导出或清除这些数据。</p></section><section><h2>反馈与第三方</h2><p>只有当你主动打开并提交 GitHub Issue 时，结构化反馈才会离开浏览器；建议内容默认不含终稿。GitHub 链接适用 GitHub 自己的隐私条款。本 Demo 不使用第三方分析、广告 Cookie 或浏览器指纹。</p></section><section><h2>使用边界与联系</h2><p>请勿输入个人、客户、机密或生产数据，也不要在公开 Issue 中提交敏感信息。安全问题请使用仓库 SECURITY.md 中的私密报告渠道。当前没有托管试用或托管隐私请求通道；未来引入账号、服务端存储或模型处理前，必须另行发布与实际部署一致的隐私政策。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/PRIVACY.md">查看仓库原文 ↗</a></p></main>;
}
