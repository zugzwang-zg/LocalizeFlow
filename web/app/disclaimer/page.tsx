import Link from "next/link";

export default function DisclaimerPage() {
  return <main className="legalPage"><p className="eyebrow">PUBLIC DEMO / DISCLAIMER</p><h1>免责声明</h1><p className="lede">检查通过只表示内容通过了项目当时实现的冻结规则，不证明事实、安全、依据充分、法律合规，也不代表任何平台、监管机关或专业人员批准。</p><section><h2>不替代专业审核</h2><p>本项目不是法律、监管、医疗、安全或财务建议，不是专业翻译认证或科学依据，也不是 Google、TikTok、商家平台、广告平台或公共机关的批准。平台规则会变化，并可能受账户、品类、活动目标、落地页、受众和司法辖区影响。</p></section><section><h2>美妆与健康宣称</h2><p>美妆文案即使没有直接使用医疗词汇，也可能暗示治疗、效果或保证。免责声明不能修复具有误导性的整体印象。发布前必须核对明示和暗示宣称、证据质量、标签要求、必要限定语和目标市场规则。</p></section><section><h2>AI 与自动化局限</h2><p>模型和确定性规则都可能遗漏语境、产生偏差、误译、虚构或过时。请完成最新的事实、法律、平台、知识产权、品牌、安全和目标语言审核。工作流内的人工确认只记录一次决定，不转移最终责任。</p></section><p><Link href="/">← 返回 Demo</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/DISCLAIMER.md">查看仓库原文 ↗</a></p></main>;
}
