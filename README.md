# API 接口自动化测试框架

基于 Python + Pytest 的通用接口自动化测试框架，开箱即用。

## 更新日志

### v1.1.0（2026-05-27）

**接口依赖编排 + 变量提取替换 & 工程优化**

- **用例执行引擎**：新增 `utils/case_executor.py`，抽离通用执行逻辑（`execute_case` / `execute_chain` / `parse_csv_case`），测试文件只需一行调用
- **飞猪接口接入**：新增接机查价 + 创单用例（`data/test_fliggy_pickup.yaml`），完整串行链路：查价 → 提取报价编码 → 创单
- **环境变量管理**：通过 `.env` 文件管理敏感信息（clientId / clientSecret），新增 `.env.example` 模板，新电脑 `cp .env.example .env` 填值即用
- **模块合并优化**：`context.py` + `variable_parser.py` 合并为 `context.py`，减少文件数，降低理解成本
- **数据加载日志开关**：`config.yaml` 新增 `show_data_loader` 配置，控制加载日志显示/隐藏
- **请求唯一 Key 恢复**：修复 `[R-xxxx]` 唯一请求标识丢失的问题
- **Git 规范化**：从仓库中移除 `.idea/` IDE 配置目录

### v1.0.0（2026-05-26）

**框架基础搭建**

- 统一 HTTP 请求封装（GET/POST/PUT/DELETE/PATCH/上传）
- 多格式数据驱动（YAML / JSON / Excel / CSV）
- 通用断言工具（状态码 / jsonpath / 包含 / 类型 / 非空）
- 多环境切换（dev / test / pre / prod）
- 全局上下文 + `${变量名}` 语法替换
- 日志双输出（控制台 + 按天切分文件）
- Allure 报告支持

---

## 核心特性

- **统一请求封装** — GET/POST/PUT/DELETE/PATCH/文件上传，自动重试、日志记录、Session 管理
- **多格式数据驱动** — 支持 YAML / JSON / Excel / CSV 四种用例格式，自动识别加载
- **通用断言工具** — 状态码校验、jsonpath 字段提取校验、包含/类型/非空断言
- **多环境切换** — 通过配置文件一键切换 dev / test / pre / prod
- **接口依赖编排** — 支持接口间串行调用，前一个接口的返回值自动传给下一个
- **变量提取与替换** — `${变量名}` 语法，从响应中用 jsonpath 提取值，后续接口自动引用
- **请求唯一 Key** — 每次请求自动生成唯一标识 `[R-xxxx]`，日志排查一搜即达
- **日志双输出** — 控制台 + 按天切分的日志文件，支持 DEBUG/INFO 级别切换
- **Allure 报告** — 支持生成美观的可视化测试报告

## 项目结构

```
apitestzgs/
├── config/
│   ├── config.yaml          # 环境配置（域名、超时、重试、日志级别等）
│   └── settings.py          # 配置读取工具
├── utils/
│   ├── http_client.py       # 统一 HTTP 请求封装（含唯一 Key、重试、日志）
│   ├── case_executor.py     # 用例执行引擎（execute_case / execute_chain）
│   ├── data_loader.py       # 多格式用例数据加载器
│   ├── assertion.py         # 通用断言工具
│   ├── context.py           # 全局上下文 + 变量解析器（${} 替换 + jsonpath 提取）
│   └── logger.py            # 日志初始化（控制台 + 文件双输出）
├── api/
│   └── base_api.py          # 接口层基类
├── testcases/
│   ├── conftest.py          # pytest fixture（日志初始化、http_client、用例加载）
│   └── test_demo.py         # 示例用例（数据驱动 + 依赖编排）
├── data/
│   ├── test_demo.yaml       # YAML 格式用例（独立接口）
│   ├── test_demo.json       # JSON 格式用例
│   ├── test_demo.csv        # CSV 格式用例
│   ├── test_dependency.yaml # 接口依赖编排用例（串行 + 变量传递）
│   └── test_fliggy_pickup.yaml # 飞猪接机查价+创单用例
├── logs/                    # 日志文件目录（按天切分，自动保留 30 天）
├── reports/                 # 测试报告输出目录
├── example_usage.py         # HttpClient 使用示例（调试学习用）
├── run.py                   # 一键执行入口
├── pytest.ini               # pytest 配置
└── requirements.txt         # 依赖清单
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env，填入真实的认证信息
```

### 3. 运行测试

```bash
# 运行全部测试用例
python3 run.py

# 指定环境运行
python3 run.py --env dev

# 按关键词筛选用例
python3 run.py -k test_yaml

# 只运行接口依赖编排用例
python3 -m pytest testcases/test_demo.py::test_dependency_chain -v

# 运行 HttpClient 使用示例（调试学习用）
python3 example_usage.py
```

### 4. 生成 Allure 报告

```bash
pytest testcases/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

### 5. 查看日志

```bash
# 查看当天日志
cat logs/$(date +%Y-%m-%d).log

# 搜索某次请求的完整链路（用唯一 Key）
grep "R-a3f8" logs/2026-05-27.log
```

## 用例数据格式

### YAML 格式（独立接口）

```yaml
- case_name: "查询用户"
  method: GET
  url: /api/user/1
  params:
    _limit: 10
  headers:
    Authorization: "Bearer xxx"
  expect:
    status_code: 200
    jsonpath:
      $.code: 0
      $.data.name: "张三"
```

### YAML 格式（接口依赖编排）

```yaml
# 步骤1：登录获取 Token
- case_name: "登录"
  method: POST
  url: /api/login
  json:
    username: "admin"
    password: "123456"
  extract:
    token: $.data.token           # 用 jsonpath 从响应中提取 token
    user_id: $.data.id            # 提取 user_id
  expect:
    status_code: 200

# 步骤2：用 Token 查询用户信息（引用上一步提取的变量）
- case_name: "查询当前用户"
  method: GET
  url: /api/user/${user_id}       # ${user_id} 会被替换为步骤1提取的值
  headers:
    Authorization: "Bearer ${token}"  # ${token} 同理
  expect:
    status_code: 200
    jsonpath:
      $.data.id: "${user_id}"
```

### JSON 格式

```json
[
  {
    "case_name": "创建用户",
    "method": "POST",
    "url": "/api/user",
    "json": {"name": "test", "age": 20},
    "expect": {"status_code": 200}
  }
]
```

### CSV 格式

| case_name | method | url | params | json | expect |
|-----------|--------|-----|--------|------|--------|
| 查询用户 | GET | /api/user/1 | | | {"status_code": 200} |

### Excel 格式

第一行为表头，字段名与上述一致，后续每行为一条用例。

## 接口依赖编排详解

### 核心概念

| 概念 | 语法 | 说明 |
|------|------|------|
| **变量提取** | `extract` | 从接口响应中用 jsonpath 提取值，存入全局上下文 |
| **变量引用** | `${变量名}` | 在 url / headers / json / params 等任意位置引用已提取的变量 |
| **全局上下文** | `context` | 整个测试过程中共享的变量池，所有用例都能读写 |

### 工作流程

```
用例1 执行请求 → 响应 JSON → extract 提取变量存入 context
                                         ↓
用例2 读取 context → ${} 替换 → 执行请求 → extract 继续提取
                                         ↓
用例3 读取 context → ${} 替换 → 执行请求 → 断言验证
```

### 变量替换规则

- **纯变量引用**：`"${user_id}"` → 保留原始类型（如 int `123`）
- **字符串拼接**：`"Bearer ${token}"` → 字符串 `"Bearer abc123"`
- **支持嵌套**：url、headers、params、json、expect 中均可使用

### 用例文件位置

- 独立接口用例：`data/test_demo.yaml`（用 parametrize 并行执行）
- 依赖编排用例：`data/test_dependency.yaml`（串行顺序执行）

## 环境配置

编辑 `config/config.yaml`：

```yaml
# 当前使用的环境
current_env: "test"

# 各环境配置
environments:
  dev:
    base_url: "http://dev-api.example.com"
  test:
    base_url: "https://jsonplaceholder.typicode.com"
  pre:
    base_url: "https://pre-api.example.com"
  prod:
    base_url: "https://api.example.com"

# 请求配置
request:
  timeout: 30          # 请求超时（秒）
  retry_count: 3       # 失败重试次数
  retry_interval: 1    # 重试间隔（秒）
  verify_ssl: false    # 是否验证 SSL 证书

# 日志配置
logging:
  level: "DEBUG"       # DEBUG=全部细节 / INFO=仅关键信息
```

运行时通过 `--env` 参数切换环境，或设置环境变量 `API_TEST_ENV`。

## 日志说明

### 日志格式

```
时间戳 [级别] 模块名 - [唯一Key] 内容
```

### 示例

```log
2026-05-27 16:03:16 [INFO]  utils.http_client - [R-2358] >>> [GET] https://xxx/posts (attempt 1)
2026-05-27 16:03:16 [DEBUG] utils.http_client - [R-2358]     Params: {'_limit': 1}
2026-05-27 16:03:17 [INFO]  utils.http_client - [R-2358] <<< [200] https://xxx/posts?_limit=1 (0.594s)
2026-05-27 16:03:17 [DEBUG] utils.http_client - [R-2358]     Response: [{'userId': 1, ...}]
2026-05-27 16:03:17 [INFO]  utils.variable_parser - 提取变量: post_id = 1 (from $[0].id)
```

### 唯一 Key 排查

每次请求都有 `[R-xxxx]` 唯一标识，搜索即可找到完整请求链路：

```bash
grep "R-2358" logs/2026-05-27.log
```

### 级别说明

| 级别 | 内容 | 适用场景 |
|------|------|----------|
| **INFO** | 请求发出、状态码、耗时、变量提取 | 日常运行 |
| **DEBUG** | 请求参数、请求体、完整响应体 | 排查问题 |

## 常用命令速查

```bash
# 运行全部用例
python3 run.py

# 运行指定文件
python3 -m pytest testcases/test_demo.py -v

# 运行指定用例
python3 -m pytest testcases/test_demo.py::test_dependency_chain -v

# 按关键词筛选
python3 -m pytest -k "yaml" -v

# 生成 HTML 报告
python3 -m pytest testcases/ --html=reports/report.html

# 生成 Allure 报告
python3 -m pytest testcases/ --alluredir=reports/allure-results
allure serve reports/allure-results
```
