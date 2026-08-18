import Link from "next/link";

export default function DisclaimerPage() {
  return <main className="legalPage"><p className="eyebrow">在线体验 / 免责声明</p><h1>免责声明</h1><p className="lede">检查通过只表示内容符合项目当前内置的检查条件，不证明资料准确、依据充分或符合法律要求，也不代表任何平台、监管机关或专业人员批准。</p><section><h2>不替代专业审核</h2><p>本项目不提供法律、监管、医疗、安全或财务建议，也不代表专业翻译认证、科学依据或 Google、TikTok 等平台的批准。平台要求会变化，并可能受账号、品类、活动目标、页面、受众和地区影响。</p></section><section><h2>美妆与健康表达</h2><p>美妆内容即使没有直接使用医疗词汇，也可能暗示治疗、效果或保证。发布前必须核对明确和暗示的效果、支持资料、标签要求、必要说明和目标市场要求。</p></section><section><h2>AI 与自动检查的局限</h2><p>模型和自动检查都可能遗漏语境、产生偏差、误译、虚构或使用过时信息。请完成最新的商品资料、法律、平台、知识产权、品牌、安全和目标语言审核。页面内的人工确认只记录一次决定，不转移最终责任。</p></section><p><Link href="/">← 返回在线体验</Link> · <a href="https://github.com/zugzwang-zg/LocalizeFlow/blob/main/DISCLAIMER.md">查看仓库原文 ↗</a></p></main>;
}
