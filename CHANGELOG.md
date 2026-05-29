# 更新日志

## v1.1.0（2026-05-27）

**接口依赖编排 + 变量提取替换 & 工程优化**

- **用例执行引擎**：新增 `utils/case_executor.py`，抽离通用执行逻辑（`execute_case` / `execute_chain` / `parse_csv_case`），测试文件只需一行调用
- **飞猪接口接入**：新增接机查价 + 创单用例（`data/test_fliggy_pickup.yaml`），完整串行链路：查价 → 提取报价编码 → 创单
- **环境变量管理**：通过 `.env` 文件管理敏感信息（clientId / clientSecret），新增 `.env.example` 模板，新电脑 `cp .env.example .env` 填值即用
- **模块合并优化**：`context.py` + `variable_parser.py` 合并为 `context.py`，减少文件数，降低理解成本
- **数据加载日志开关**：`config.yaml` 新增 `show_data_loader` 配置，控制加载日志显示/隐藏
- **请求唯一 Key 恢复**：修复 `[R-xxxx]` 唯一请求标识丢失的问题
- **Git 规范化**：从仓库中移除 `.idea/` IDE 配置目录

## v1.0.0（2026-05-26）

**框架基础搭建**

- 统一 HTTP 请求封装（GET/POST/PUT/DELETE/PATCH/上传），自动重试、日志记录、Session 管理
- 多格式数据驱动（YAML / JSON / Excel / CSV），自动识别加载
- 通用断言工具（状态码 / jsonpath / 包含 / 类型 / 非空）
- 多环境切换（dev / test / pre / prod），通过 config.yaml 一键切换
- 全局上下文 + `${变量名}` 语法替换，支持接口间变量传递
- 日志双输出（控制台 + 按天切分文件），每次请求带唯一标识 `[R-xxxx]`
- Allure 报告支持
