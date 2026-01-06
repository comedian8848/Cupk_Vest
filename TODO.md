# 项目待优化清单

## 🔧 代码质量改进

### 1. 异常处理增强
- [ ] **ths_impl.py**: `get_industry_comparison` 和 `get_supply_chain_info` 缺少对 pywencai 返回 None 的健壮处理
- [ ] **data_fetcher.py**: `fetch_current_valuation` 的多次重试逻辑可封装为装饰器
- [ ] **stock_analysis_v2.py**: 大量 `next()` 查找列名的逻辑，可提取为通用函数并添加缓存

### 2. 配置与文档
- [ ] **config.py**: 增加配置验证函数，检查参数合理性（如 `DISCOUNT_RATE` 不应 > 1）
- [ ] **README.md**: 补充 pywencai 安装失败的常见问题（如 Node.js 版本要求）
- [ ] **ths_impl.py**: 添加 docstring 示例，说明问财查询语法的可调优方向

### 3. 性能优化
- [ ] **data_fetcher.py**: `fetch_all_data` 中部分数据可设置缓存（如公司信息、行业分类）
- [ ] **stock_analysis_v2.py**: `_calculate_single_quarter_data` 对大数据集效率较低，考虑向量化
- [ ] **analysis.py**: `calculate_ttm_series` 循环计算可用 pandas rolling 优化

### 4. 数据质量
- [ ] **增加数据异常检测**: 财务数据突变（如营收/利润暴涨 >300%）应标记预警
- [ ] **供应链数据验证**: ths_impl 返回的百分比格式不统一（有的带 %，有的是小数），需统一处理
- [ ] **历史估值清洗**: `_plot_company_analysis` 的分位点计算需过滤极端值（如 PE < 0 或 > 1000）

## 🆕 功能扩展

### 5. 新增分析维度
- [ ] **机构持仓追踪**: 利用 akshare 的 `stock_institute_hold_detail` 接口
- [ ] **行业景气度**: 从同花顺获取行业 PE、PB 中位数，判断行业估值水位
- [ ] **管理层持股变动**: 解析董监高增减持数据（akshare 已有接口）
- [ ] **财务造假风险模型**: 集成 Beneish M-Score 或简化版指标

### 6. 回测增强
- [ ] **多策略对比**: 在 `run_backtest` 中支持同时运行 3-5 种策略并对比
- [ ] **止损止盈**: 当前 `SmaCross` 策略无风控，建议增加最大回撤止损
- [ ] **参数优化**: 支持网格搜索最佳均线组合（如 MA(10, 50) vs MA(20, 60)）

### 7. 报告增强
- [ ] **PDF 导出**: 集成 reportlab 或 weasyprint 生成 PDF 报告
- [ ] **Web 可视化**: 使用 Plotly 替代部分 Matplotlib 图表，支持交互
- [ ] **邮件/企微推送**: 分析完成后自动发送摘要到指定邮箱

## 🐛 Bug 修复

### 8. 已知问题
- [ ] **ths_impl.py L52**: `my_code = ths_impl.check_dependencies` 赋值错误（应为字符串处理）
- [ ] **stock_analysis_v2.py L1324**: 同行业对比时未正确识别本公司（代码匹配逻辑有误）
- [ ] **delete_file.py & inspect_akshare.py**: 调试脚本应移入 `tests/` 目录或删除

### 9. 边界情况
- [ ] **期货分析**: `FuturesAnalyzer` 未集成回测功能，建议复用股票回测框架
- [ ] **新股/次新股**: IPO 不满 3 年的公司，CAGR 计算会失败，需特殊处理
- [ ] **ST 股票**: 特殊处理类股票应在分析开始时标注风险

## 📁 项目结构

### 10. 代码组织
- [ ] 创建 `tests/` 目录，移入 test_fix.py、delete_file.py、inspect_akshare.py
- [ ] 创建 `utils/` 目录，抽取通用函数（如 `_safe_float`, `_format_number`）
- [ ] 创建 `strategies/` 目录，独立存放回测策略类
- [ ] 创建 `examples/` 目录，存放示例用法脚本

### 11. 文档完善
- [ ] 增加 `CONTRIBUTING.md` - 贡献指南
- [ ] 增加 `CHANGELOG.md` - 版本更新日志
- [ ] 增加 `docs/` 目录 - API 文档与设计说明
- [ ] 补充 `requirements-dev.txt` - 开发依赖（pytest, black, flake8）

## 🔐 安全与合规

### 12. 数据隐私
- [ ] **API 限流**: akshare 和 pywencai 应增加请求频率控制
- [ ] **敏感数据**: 分析报告中不应包含用户个人信息
- [ ] **免责声明**: README 应明确"仅供学习，不构成投资建议"

## 🎯 优先级建议

**P0 (高优先级 - 影响功能)**:
- Bug #8: 修复 ths_impl.py 代码匹配逻辑
- 性能 #3: 优化 TTM 计算效率
- 数据质量 #4: 供应链数据格式统一

**P1 (中优先级 - 增强体验)**:
- 功能 #5: 机构持仓追踪
- 功能 #6: 回测止损止盈
- 文档 #11: 补充 CHANGELOG

**P2 (低优先级 - 长期规划)**:
- 功能 #7: Web 可视化
- 结构 #10: 代码重构为包结构
