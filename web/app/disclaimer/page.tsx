import Link from "next/link";

export default function DisclaimerPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / DISCLAIMER</p><h1>免责声明</h1><p className="lede">检查通过只表示内容通过了项目当时实现的冻结规则，不代表任何平台、监管机关或专业人员批准。</p><section><h2>不替代专业审核</h2><p>本项目不是法律、监管或医疗建议，不是专业翻译认证，也不是 Google、TikTok、商家平台或广告平台的批准。平台规则会变化，并可能受账户、品类、活动目标、落地页和司法辖区影响。</p></section><section><h2>发布前</h2><p>请完成最新平台规则、法律、事实与目标语言审核。Demo 中的人工确认只记录工作流决定，不转移最终发布责任。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/DISCLAIMER.md">查看仓库原文 ↗</a></p></main>;
}
