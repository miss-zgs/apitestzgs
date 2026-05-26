"""
HttpClient 使用示例文件

使用公开免费的 JSONPlaceholder API (https://jsonplaceholder.typicode.com) 进行演示，
可以直接运行本文件体验各种请求方式。

运行方式:
    cd apitestzgs
    python3 example_usage.py
"""
import logging
import sys
import os

# 将项目根目录加入 sys.path，确保能正确导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.http_client import HttpClient

# 配置日志级别为 DEBUG，可以看到请求/响应的详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


def example_get():
    """示例1: GET 请求 - 查询帖子列表"""
    print("\n" + "=" * 60)
    print("示例1: GET 请求 - 查询帖子列表")
    print("=" * 60)

    client = HttpClient()

    # 带查询参数的 GET 请求，_limit=3 表示只返回 3 条
    response = client.get("/posts", params={"_limit": 3})

    print(f"状态码: {response.status_code}")
    print(f"返回数据条数: {len(response.json())}")
    for post in response.json():
        print(f"  - [{post['id']}] {post['title'][:30]}...")


def example_get_single():
    """示例2: GET 请求 - 查询单个资源"""
    print("\n" + "=" * 60)
    print("示例2: GET 请求 - 查询单个帖子详情")
    print("=" * 60)

    client = HttpClient()

    response = client.get("/posts/1")

    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"帖子ID: {data['id']}")
    print(f"标题: {data['title']}")
    print(f"内容: {data['body'][:50]}...")


def example_post():
    """示例3: POST 请求 - 创建资源"""
    print("\n" + "=" * 60)
    print("示例3: POST 请求 - 创建新帖子")
    print("=" * 60)

    client = HttpClient()

    # 使用 json_data 发送 JSON 格式的请求体
    response = client.post("/posts", json_data={
        "title": "这是一个测试帖子",
        "body": "通过 HttpClient 创建的帖子内容",
        "userId": 1,
    })

    print(f"状态码: {response.status_code}")  # 201 表示创建成功
    data = response.json()
    print(f"新建帖子ID: {data.get('id')}")
    print(f"标题: {data.get('title')}")


def example_put():
    """示例4: PUT 请求 - 全量更新资源"""
    print("\n" + "=" * 60)
    print("示例4: PUT 请求 - 更新帖子")
    print("=" * 60)

    client = HttpClient()

    response = client.put("/posts/1", json_data={
        "id": 1,
        "title": "更新后的标题",
        "body": "更新后的内容",
        "userId": 1,
    })

    print(f"状态码: {response.status_code}")
    print(f"更新后标题: {response.json().get('title')}")


def example_patch():
    """示例5: PATCH 请求 - 部分更新资源"""
    print("\n" + "=" * 60)
    print("示例5: PATCH 请求 - 部分更新帖子标题")
    print("=" * 60)

    client = HttpClient()

    # PATCH 只需要传需要修改的字段
    response = client.patch("/posts/1", json_data={
        "title": "只修改了标题",
    })

    print(f"状态码: {response.status_code}")
    print(f"更新后标题: {response.json().get('title')}")


def example_delete():
    """示例6: DELETE 请求 - 删除资源"""
    print("\n" + "=" * 60)
    print("示例6: DELETE 请求 - 删除帖子")
    print("=" * 60)

    client = HttpClient()

    response = client.delete("/posts/1")

    print(f"状态码: {response.status_code}")  # 200 表示删除成功
    print("删除成功!" if response.status_code == 200 else "删除失败!")


def example_custom_headers():
    """示例7: 自定义 Headers 和 Token"""
    print("\n" + "=" * 60)
    print("示例7: 设置自定义 Headers 和 Token")
    print("=" * 60)

    client = HttpClient()

    # 方式1: 设置全局 Token（后续所有请求自动携带）
    client.set_token("my_fake_token_12345")
    print(f"当前默认 Headers: {client._default_headers}")

    # 方式2: 追加自定义全局 Header
    client.set_headers({"X-Custom-Tag": "test-run"})
    print(f"追加后的 Headers: {client._default_headers}")

    # 方式3: 单次请求传入额外 Header（不影响全局）
    response = client.get("/posts/1", headers={"X-Request-Id": "req-001"})
    print(f"请求成功, 状态码: {response.status_code}")

    # 清空会话，恢复默认状态
    client.clear_session()
    print(f"清空后的 Headers: {client._default_headers}")


def example_session_share():
    """示例8: Session 共享（同一个 client 的请求共享 Cookie）"""
    print("\n" + "=" * 60)
    print("示例8: Session 共享演示")
    print("=" * 60)

    client = HttpClient()

    # 同一个 client 发出的多次请求会共享 Session（Cookie、连接池等）
    response_1 = client.get("/posts/1")
    response_2 = client.get("/posts/2")

    print(f"请求1 状态码: {response_1.status_code}")
    print(f"请求2 状态码: {response_2.status_code}")
    print("两次请求共享同一个 Session，Cookie 和连接池自动维护")


def example_full_url():
    """示例9: 传入完整 URL（跳过 base_url 拼接）"""
    print("\n" + "=" * 60)
    print("示例9: 直接传入完整 URL")
    print("=" * 60)

    client = HttpClient()

    # 如果 path 以 http:// 或 https:// 开头，会直接使用该 URL
    response = client.get("https://jsonplaceholder.typicode.com/users/1")

    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"用户名: {data['name']}")
    print(f"邮箱: {data['email']}")


# ==================== 主入口 ====================

if __name__ == "__main__":
    print("🚀 HttpClient 使用示例")
    print("使用 JSONPlaceholder (https://jsonplaceholder.typicode.com) 公开 API 进行演示\n")

    example_get()
    example_get_single()
    example_post()
    example_put()
    example_patch()
    example_delete()
    example_custom_headers()
    example_session_share()
    example_full_url()

    print("\n" + "=" * 60)
    print("✅ 所有示例执行完毕！")
    print("=" * 60)
