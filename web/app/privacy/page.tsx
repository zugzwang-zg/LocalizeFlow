import Link from "next/link";

export default function PrivacyPage() {
  return <main className="legalPage"><p className="eyebrow">在线体验 / 隐私说明</p><h1>隐私说明</h1><p className="lede">本说明适用于示例数据和表格试用。页面不会把上传文件或编辑内容发送给项目维护者，也不会连接在线模型服务。</p><section><h2>保存在本机的数据</h2><p>如果启用匿名操作记录，浏览器最多保存 100 条且不超过 30 天的时间、市场、内容类型和操作步骤。不会保存正文、上传文件、姓名、邮箱、IP 地址或密钥。你可以在确认和下载页面停用、下载或清除这些记录。</p></section><section><h2>反馈与外部链接</h2><p>只有当你主动打开并提交 GitHub 反馈时，填写的信息才会离开浏览器；默认不会附带最终内容。GitHub 链接适用 GitHub 自己的隐私条款。本项目不使用第三方分析、广告追踪或浏览器指纹。</p></section><section><h2>使用范围与联系</h2><p>请勿输入个人、客户、机密或生产数据，也不要在公开反馈中提交敏感信息。安全问题请使用仓库 SECURITY.md 中的私密报告渠道。当前仅提供浏览器内试用，尚未开放账号、云端保存或在线模型处理。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/PRIVACY.md">查看仓库原文 ↗</a></p></main>;
}
