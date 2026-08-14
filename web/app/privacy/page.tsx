import Link from "next/link";

export default function PrivacyPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / PRIVACY</p><h1>隐私说明</h1><p className="lede">当前公开 Demo 完全在浏览器中运行，不调用模型 API，也不会自动把选择、编辑、反馈或体验指标传给项目维护者。</p><section><h2>本地保存的数据</h2><p>最多 100 条且不超过 30 天的体验事件：匿名运行 ID、事件名、时间、耗时、市场、内容类型与步骤；用途仅为你自行检查体验路径。不会记录正文、姓名、邮箱、IP 地址或 API 凭证。你可以在 Demo 终审页停用、导出或清除这些数据。</p></section><section><h2>反馈与第三方</h2><p>只有当你主动打开并提交 GitHub Issue 时，结构化反馈才会离开浏览器；默认不含终稿。GitHub 链接适用 GitHub 自己的隐私条款。本 Demo 不使用第三方分析或广告 Cookie。</p></section><section><h2>使用边界</h2><p>请勿输入个人、客户、机密或生产数据。若未来引入账号、服务端存储或第三方分析，上线前必须更新本说明并重新评估同意机制。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/PRIVACY.md">查看仓库原文 ↗</a></p></main>;
}
