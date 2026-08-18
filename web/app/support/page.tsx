import Link from "next/link";

export default function SupportPage() {
  return <main className="legalPage"><p className="eyebrow">在线体验 / 支持</p><h1>支持与故障报告</h1><p className="lede">当前提供开源版本和浏览器内表格试用，由维护者尽力维护，但不提供全天候支持或保证响应时间。</p><section><h2>选择合适的反馈方式</h2><p>安装、文档或操作流程问题请使用 GitHub Support request；能够重复出现的故障请使用 Bug report。安全漏洞或疑似数据暴露必须按照 SECURITY.md 私下报告，不要创建公开反馈。</p></section><section><h2>不要提交敏感信息</h2><p>公开反馈中不得包含密钥、个人信息、客户正文、未公开商品资料、生产账号或漏洞利用细节。请使用虚构或妥善脱敏的材料，并说明版本、受影响页面、预期结果和实际结果。</p></section><section><h2>试用范围</h2><p>表格只在浏览器本地处理，不提供账号、云端保存或在线模型服务。报告导入问题时，请附模板列名和脱敏后的最小示例文件。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/issues/new?template=support_request.yml">创建支持工单 ↗</a> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/SUPPORT.md">查看支持政策 ↗</a></p></main>;
}
