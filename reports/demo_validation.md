# Streamlit Demo 验证记录

验证日期：2026-07-28

## 自动化验证

执行命令：

```powershell
.\.venv\Scripts\python.exe -m compileall -q app src tests
.\.venv\Scripts\python.exe app\main.py --smoke-test
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

结果：

- Python 编译检查通过。
- Streamlit 启动烟雾检查通过。
- 40 项单元测试全部通过。
- Demo 专项测试覆盖 5 个商品、2 个市场、3 种内容类型，共 30 种生成组合。
- JSON/CSV 导出格式通过解析检查。
- 已知包装矛盾可以阻断导出，人工修订后可以解除阻断。

## 浏览器端到端验证

在本地 `http://localhost:8501` 依次完成：

1. 商品资料页加载结构化事实、允许表达、上传与粘贴入口。
2. 营销任务页默认进入美国市场，显示 `en-US`，并正确初始化营销目标与品牌语调。
3. 生成结果页展示 Listing、TikTok、社媒三类内容及声明级事实来源。
4. 质量检查页识别 `a opaque → an opaque` 英文语言问题，事实错误数保持为 0。
5. 版本页展示 Baseline/增强版对比并载入最终编辑器。
6. 将 `a opaque` 人工修改为 `an opaque` 后重新预检。
7. 未勾选终审时确认按钮禁用；勾选后可确认。
8. 确认成功后 JSON 与 CSV 下载入口同时开放。
9. 390×844 移动视口下，版本、确认结果与两个下载入口仍可访问。
10. 未发现应用运行错误；为加载修订后的服务模块而主动重启本地服务器时，浏览器记录了 1 条预期内的 WebSocket 断开警告，重连后流程正常。

## 验证结论

规定路径“选择商品 → 市场/平台 → 生成 → 检查 → 编辑/确认 → 导出”已完整走通。其输出来自离线确定性内容，不应被解释为真实模型在线生成、平台审核结果或生产发布能力。

## 截图

- `assets/streamlit_demo_home.jpg`
- `assets/streamlit_demo_quality.jpg`
- `assets/streamlit_demo_export.jpg`
- `assets/streamlit_demo_mobile.jpg`
