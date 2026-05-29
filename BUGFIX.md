# Bug 记录

## BUG-001：飞猪查价用例 useTime 写死日期，过期后全链路失败

- **发现时间**：2026-05-29 15:47
- **严重程度**：🔴 高（影响飞猪全链路用例）
- **状态**：✅ 已修复

### 现象

飞猪接机用例 `test_fliggy_pickup_price` 在 2026-05-29 运行时，查价接口返回"搜索结果为空"，导致 `quotation_code` 提取失败，创单用例发送了未替换的原始变量 `${quotation_code}`。

### 请求与响应

**查价请求：**

```
[R-3669] >>> [POST] https://test-gateway-travelswitch.fliggy.com/open/distribution/daolvetravel/openapiSupplier/queryPrice (attempt 1)
[R-3669]     Body: {
  "flightNumber": "K6789",
  "endPoint": {"coordinates": {"lat": 34.6734038, "lon": 135.5013019}, "name": "大丸(心斋桥店)", "type": "2"},
  "startPoint": {"iata": "KIX", "name": "关西国际机场", "type": "1"},
  "luggage": 1,
  "passengers": 3,
  "useTime": "2026-05-28 21:44:00"    ← 写死的日期，已过期
}
```

**查价响应：**

```
[R-3669] <<< [200] .../queryPrice (1.008s)
[R-3669]     Response: {'success': False, 'code': 500, 'message': '搜索结果为空'}
```

**变量提取失败日志：**

```
WARNING - 提取变量失败: quotation_code (jsonpath '$.data.vehicleQuotationList[0].quotationCode' 未匹配)
WARNING - 变量 '${quotation_code}' 未定义，保持原样
```

**创单请求（变量未替换）：**

```
[R-dfb2]     Body: {
  "quotationCode": "${quotation_code}",    ← 未替换，原样发送
  "amount": 360,
  ...
}
```

**创单响应：**

```
[R-dfb2]     Response: {'success': False, 'code': 500, 'message': '系统异常，请联系管理员'}
```

### 根因分析

`data/test_fliggy_pickup.yaml` 中查价和创单的 `useTime` 均写死为 `2026-05-28`：

```yaml
useTime: "2026-05-28 21:44:00"    # 查价
useTime: "2026-05-28 13:55:00"    # 创单
```

接机查价接口要求 `useTime` 必须是**未来时间**，过了 2026-05-28 后该用例就永远失败。

### 影响范围

- `test_fliggy_pickup_price` — 飞猪查价+创单全链路用例
- 其他用例不受影响

### 修复方案

1. **`testcases/conftest.py`** — 在 `inject_env_variables` fixture 中注入 `${tomorrow}` 动态变量：

```python
from datetime import datetime, timedelta
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
context.set("tomorrow", tomorrow)
```

2. **`data/test_fliggy_pickup.yaml`** — `useTime` 改为动态引用：

```yaml
useTime: "${tomorrow} 21:44:00"    # 查价
useTime: "${tomorrow} 13:55:00"    # 创单
```

### 修复验证

修复后运行结果：

```
[R-db96]     Body: {..., "useTime": "2026-05-30 21:44:00"}     ← 动态明天日期
提取变量: quotation_code = '2247552092###eJyyy...'              ← 提取成功
[R-aa70]     Body: {"quotationCode": "2247552092###eJyyy..."}  ← 变量替换成功
PASSED
```

### 修复提交

```
commit 4aa7f1d
fix: 飞猪用例 useTime 改为动态日期，避免过期导致查价失败
```

---

## BUG-002：http_client.py 请求唯一标识 [R-xxxx] 丢失

- **发现时间**：2026-05-27 17:53
- **严重程度**：🟡 中（不影响功能，影响日志排查效率）
- **状态**：✅ 已修复

### 现象

日志中请求和响应不再带 `[R-xxxx]` 唯一标识，无法通过 grep 快速定位某次请求的完整链路。

**修复前日志：**

```
>>> [POST] https://xxx/queryPrice (attempt 1)
<<< [200] https://xxx/queryPrice (3.815s)
```

**修复后日志：**

```
[R-0c11] >>> [POST] https://xxx/queryPrice (attempt 1)
[R-0c11] <<< [200] https://xxx/queryPrice (4.676s)
```

### 根因分析

Git rebase 时 `utils/http_client.py` 被远程旧版本覆盖，丢失了以下代码：

- `import uuid`
- `request_id = f"R-{uuid.uuid4().hex[:4]}"` 生成唯一标识
- `_log_request` / `_log_response` 方法中的 `request_id` 参数和日志格式

### 修复方案

恢复 `uuid` 导入，在 `_request` 方法中生成 `request_id`，传入日志方法并在每条日志前缀添加 `[R-xxxx]`。

### 修复提交

```
commit 46f76e3
feat: 接口依赖编排+变量提取替换 & utils优化合并
```

---

## BUG-003：查价响应 jsonpath 提取路径错误

- **发现时间**：2026-05-27 17:42
- **严重程度**：🔴 高（导致创单用例无法获取 quotationCode）
- **状态**：✅ 已修复

### 现象

查价接口返回 200 成功，但 `quotation_code` 提取失败，日志报 `KeyError: 0`。

### 请求与响应

**查价响应结构：**

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "vehicleQuotationList": [
      {"quotationCode": "2247552092###...", "baseAmount": 60, ...},
      {"quotationCode": "2247552092###...", "baseAmount": 300, ...}
    ]
  }
}
```

### 根因分析

用例中 extract 的 jsonpath 写成了 `$.data.quotationCode`，但实际响应结构中 `quotationCode` 在 `data.vehicleQuotationList` 数组内部。

| 错误写法 | 正确写法 |
|----------|----------|
| `$.data.quotationCode` | `$.data.vehicleQuotationList[0].quotationCode` |

### 修复方案

`data/test_fliggy_pickup.yaml` 中修正 jsonpath：

```yaml
extract:
  quotation_code: $.data.vehicleQuotationList[0].quotationCode
```

### 修复提交

```
commit 46f76e3
feat: 接口依赖编排+变量提取替换 & utils优化合并
```
