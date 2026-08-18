import Link from "next/link";

export default function StatusPage() {
  return <main className="legalPage"><p className="eyebrow">服务状态 / 2026-08-18</p><h1>服务状态</h1><p className="lede">在线体验已提供示例数据和浏览器内表格试用，但没有全天候自动监控，请以实际页面访问结果为准。账号、云端保存和在线模型服务尚未开放。</p><section><h2>当前可用范围</h2><p>示例数据和上传的 CSV/XLSX 只在浏览器中处理，不会连接在线模型服务，也不会自动上传文件。仓库中的本地版本也可以在用户自己的电脑上运行。</p></section><section><h2>状态说明的局限</h2><p>这是人工维护的状态说明，不是实时监控页面，也不承诺持续可用。未来如开放云端服务，还需要补充独立监控、长期记录和服务中断提醒。</p></section><section><h2>报告问题</h2><p>一般问题请使用 <Link href="/support">支持页面</Link>。安全漏洞或疑似数据泄露请使用仓库 SECURITY.md 中的私密渠道，不要提交公开反馈。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/STATUS.md">查看仓库状态原文 ↗</a></p></main>;
}
