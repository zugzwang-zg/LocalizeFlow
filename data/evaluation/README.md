# A/B 评测数据说明

## 当前状态

60 条候选、30 组 A/B 已完成评分和揭盲，评测报告与失败案例分析已生成。

## 文件

- `human_evaluation.xlsx`：原始匿名盲评模板
- `human_evaluation_scored_revealed.xlsx`：保留评分数据并新增揭盲结果、公式化统计、图表、完整失败案例和行级版本映射的最终工作簿
- `blind_manifest.json`：匿名候选与覆盖信息
- `admin_do_not_open_before_scoring/blind_key.json`：揭盲密钥

## 完整性

- 候选完成度：60/60
- A/B 组完成度：30/30
- 候选 ID：60 个唯一值
- Group ID：30 个唯一值，每组两个候选
- 内容哈希：60/60 与揭盲密钥一致
- 评分范围和必填项：无错误

## 结果入口

最终工作簿中的主要工作表：

- `Results Dashboard`：总体 KPI 和 A/B 图表
- `Results Detail`：总体、英语和西语的公式化统计
- `Failure Cases`：全部 30 条真实失败案例
- `Revealed Data`：60 条候选的行级版本映射和原始评分

书面报告位于 `reports/evaluation_report.md`，代表性失败案例位于 `reports/evaluation_failure_cases.md`。
