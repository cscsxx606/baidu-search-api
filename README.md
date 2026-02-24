# Baidu Search API

一个简单易用的百度搜索 API 封装，支持网页搜索、图片搜索、新闻搜索等功能。

## 功能特性

- 🔍 网页搜索
- 🖼️ 图片搜索  
- 📰 新闻搜索
- 🎥 视频搜索
- 📚 学术搜索
- ⚡ 异步支持
- 🛡️ 请求重试机制
- 📝 完整的日志记录

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 基本使用

```python
from baidu_search import BaiduSearch

# 初始化搜索客户端
search = BaiduSearch()

# 网页搜索
results = search.web_search("Python 教程")
for result in results:
    print(f"标题: {result['title']}")
    print(f"链接: {result['url']}")
    print(f"摘要: {result['abstract']}")
    print("-" * 50)
```

### 高级用法

```python
from baidu_search import BaiduSearch, SearchType

search = BaiduSearch(
    timeout=10,
    retries=3,
    delay=1.0
)

# 图片搜索
images = search.image_search("猫咪", num=10)

# 新闻搜索
news = search.news_search("科技", num=20)

# 视频搜索
videos = search.video_search("Python", num=15)
```

## API 说明

### BaiduSearch 类

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `timeout` | int | 10 | 请求超时时间（秒） |
| `retries` | int | 3 | 重试次数 |
| `delay` | float | 1.0 | 请求间隔（秒） |
| `headers` | dict | None | 自定义请求头 |

### 搜索方法

| 方法 | 参数 | 返回值 |
|------|------|--------|
| `web_search(query, num=10, page=1)` | query: 搜索关键词<br>num: 结果数量<br>page: 页码 | List[Dict] |
| `image_search(query, num=10, page=1)` | 同上 | List[Dict] |
| `news_search(query, num=10, page=1)` | 同上 | List[Dict] |
| `video_search(query, num=10, page=1)` | 同上 | List[Dict] |

## 返回数据格式

```python
{
    "title": "搜索结果标题",
    "url": "https://www.example.com",
    "abstract": "搜索结果摘要...",
    "source": "来源网站",
    "timestamp": "2024-01-01 12:00:00"
}
```

## 注意事项

1. 请遵守百度搜索引擎的使用条款
2. 建议设置合理的请求间隔，避免频繁请求
3. 本工具仅供学习和研究使用

## License

MIT License
