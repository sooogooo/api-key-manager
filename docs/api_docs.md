# API密钥管理系统 API文档

## API概述

本文档详细说明了API密钥管理系统提供的所有API端点。系统使用REST风格的API设计，支持JSON格式的数据交换。

## 基本信息

- 基础URL: `https://your-domain.com`
- API版本: v1
- 内容类型: `application/json`
- 认证方式: Bearer Token

## 认证

所有API请求都需要在Header中包含有效的API密钥：

```http
Authorization: Bearer your-api-key
```

## 错误处理

系统使用标准的HTTP状态码表示请求结果：

- 200: 请求成功
- 400: 请求参数错误
- 401: 未授权或密钥无效
- 403: 禁止访问（如超出限制）
- 404: 资源不存在
- 429: 请求过于频繁
- 500: 服务器内部错误

错误响应格式：
```json
{
    "error": {
        "code": "error_code",
        "message": "详细错误信息",
        "details": {
            "field": "具体错误字段",
            "reason": "具体原因"
        }
    }
}
```

## API端点

### Chat Completions API

#### 创建聊天补全

```http
POST /v1/chat/completions
```

请求体：
```json
{
    "model": "gpt-3.5-turbo",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Hello!"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 150,
    "stream": false
}
```

响应：
```json
{
    "id": "chatcmpl-123abc",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "gpt-3.5-turbo",
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 7,
        "total_tokens": 20
    },
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop",
            "index": 0
        }
    ]
}
```

#### 流式响应

设置 `stream: true` 获取流式响应：

```http
POST /v1/chat/completions
```

请求体：
```json
{
    "model": "gpt-3.5-turbo",
    "messages": [...],
    "stream": true
}
```

响应（每个事件）：
```text
data: {"id":"chatcmpl-123abc","object":"chat.completion.chunk","created":1677858242,"model":"gpt-3.5-turbo","choices":[{"delta":{"content":"Hello"},"index":0,"finish_reason":null}]}

data: {"id":"chatcmpl-123abc","object":"chat.completion.chunk","created":1677858242,"model":"gpt-3.5-turbo","choices":[{"delta":{"content":"!"},"index":0,"finish_reason":null}]}

data: [DONE]
```

### Completions API

#### 创建文本补全

```http
POST /v1/completions
```

请求体：
```json
{
    "model": "text-davinci-003",
    "prompt": "Once upon a time",
    "max_tokens": 100,
    "temperature": 0.7
}
```

响应：
```json
{
    "id": "cmpl-123abc",
    "object": "text_completion",
    "created": 1677858242,
    "model": "text-davinci-003",
    "choices": [
        {
            "text": " there was a magical kingdom...",
            "index": 0,
            "finish_reason": "length"
        }
    ],
    "usage": {
        "prompt_tokens": 4,
        "completion_tokens": 7,
        "total_tokens": 11
    }
}
```

### 嵌入（Embeddings）API

#### 创建嵌入

```http
POST /v1/embeddings
```

请求体：
```json
{
    "model": "text-embedding-ada-002",
    "input": "The quick brown fox jumped over the lazy dog."
}
```

响应：
```json
{
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "embedding": [0.0023064255, -0.009327292, ...],
            "index": 0
        }
    ],
    "model": "text-embedding-ada-002",
    "usage": {
        "prompt_tokens": 10,
        "total_tokens": 10
    }
}
```

### 模型API

#### 列出可用模型

```http
GET /v1/models
```

响应：
```json
{
    "object": "list",
    "data": [
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": 1677858242,
            "owned_by": "openai"
        },
        {
            "id": "text-davinci-003",
            "object": "model",
            "created": 1677858242,
            "owned_by": "openai"
        }
    ]
}
```

#### 获取模型详情

```http
GET /v1/models/{model_id}
```

响应：
```json
{
    "id": "gpt-3.5-turbo",
    "object": "model",
    "created": 1677858242,
    "owned_by": "openai",
    "permission": [],
    "root": "gpt-3.5-turbo",
    "parent": null
}
```

## 使用限制

### 速率限制

- 默认每分钟请求限制：60次
- 每日总调用限制：由API密钥设置决定
- 并发请求限制：10个

超出限制时返回429状态码：
```json
{
    "error": {
        "code": "rate_limit_exceeded",
        "message": "请求过于频繁，请稍后重试",
        "details": {
            "reset_at": "2024-01-20T10:00:00Z"
        }
    }
}
```

### 令牌限制

- 每个请求的最大令牌数：4096
- 上下文窗口大小：视模型而定

## 最佳实践

### 错误处理

1. 实现指数退避重试：
```python
import time

def make_request_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)
```

2. 处理流式响应：
```python
import requests

def stream_response(url, headers, data):
    with requests.post(url, headers=headers, json=data, stream=True) as r:
        for line in r.iter_lines():
            if line:
                yield line.decode('utf-8')
```

### 性能优化

1. 使用连接池：
```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

2. 批量请求：
```python
async def batch_requests(texts, batch_size=5):
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        tasks = [process_text(text) for text in batch]
        results.extend(await asyncio.gather(*tasks))
    return results
```

### 安全建议

1. 安全存储API密钥：
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')
```

2. 实现请求签名：
```python
import hmac
import hashlib

def sign_request(payload, secret):
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

## 示例代码

### Python

```python
import requests

class APIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://your-domain.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def chat_completion(self, messages, model="gpt-3.5-turbo"):
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": model,
                "messages": messages
            }
        )
        response.raise_for_status()
        return response.json()
    
    def create_embedding(self, text, model="text-embedding-ada-002"):
        response = self.session.post(
            f"{self.base_url}/embeddings",
            json={
                "model": model,
                "input": text
            }
        )
        response.raise_for_status()
        return response.json()

# 使用示例
client = APIClient("your-api-key")

# 聊天补全
response = client.chat_completion([
    {"role": "user", "content": "Hello!"}
])
print(response['choices'][0]['message']['content'])

# 创建嵌入
embedding = client.create_embedding("Hello, world!")
print(embedding['data'][0]['embedding'])
```

### JavaScript

```javascript
class APIClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://your-domain.com/v1';
    }

    async chatCompletion(messages, model = 'gpt-3.5-turbo') {
        const response = await fetch(`${this.baseUrl}/chat/completions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model,
                messages
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        return response.json();
    }

    async createEmbedding(text, model = 'text-embedding-ada-002') {
        const response = await fetch(`${this.baseUrl}/embeddings`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model,
                input: text
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        return response.json();
    }
}

// 使用示例
const client = new APIClient('your-api-key');

// 聊天补全
client.chatCompletion([
    { role: 'user', content: 'Hello!' }
])
.then(response => {
    console.log(response.choices[0].message.content);
})
.catch(error => {
    console.error('Error:', error);
});

// 创建嵌入
client.createEmbedding('Hello, world!')
.then(response => {
    console.log(response.data[0].embedding);
})
.catch(error => {
    console.error('Error:', error);
});
```

## 更新日志

### v1.0.0 (2024-01-20)
- 初始版本发布
- 支持基本的聊天补全和嵌入API
- 实现速率限制和认证

### v1.1.0 (计划中)
- 添加批量处理API
- 支持更多模型
- 改进错误处理
- 添加请求日志API

## 支持

如果遇到问题或需要帮助：
1. 查看系统日志
2. 检查错误响应中的详细信息
3. 联系系统管理员

## 附录

### 状态码列表

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |

### 常见错误代码

| 错误代码 | 描述 |
|----------|------|
| invalid_api_key | API密钥无效 |
| rate_limit_exceeded | 超出速率限制 |
| quota_exceeded | 超出配额限制 |
| invalid_request | 请求参数无效 |
| model_not_found | 模型不存在 |
| server_error | 服务器内部错误 |