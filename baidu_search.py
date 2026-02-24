#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索 API 封装
支持网页搜索、图片搜索、新闻搜索、视频搜索
"""

import re
import time
import json
import logging
import urllib.parse
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchType(Enum):
    """搜索类型"""
    WEB = "web"
    IMAGE = "image"
    NEWS = "news"
    VIDEO = "video"
    SCHOLAR = "scholar"


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    abstract: str
    source: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "abstract": self.abstract,
            "source": self.source,
            "timestamp": self.timestamp
        }


class BaiduSearch:
    """
    百度搜索客户端
    
    Attributes:
        timeout: 请求超时时间
        retries: 重试次数
        delay: 请求间隔（秒）
        headers: 请求头
    """
    
    # 百度搜索 URL 模板
    SEARCH_URLS = {
        SearchType.WEB: "https://www.baidu.com/s",
        SearchType.IMAGE: "https://image.baidu.com/search/index",
        SearchType.NEWS: "https://www.baidu.com/s",
        SearchType.VIDEO: "https://www.baidu.com/s",
    }
    
    # 默认请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    def __init__(
        self,
        timeout: int = 10,
        retries: int = 3,
        delay: float = 1.0,
        headers: Optional[Dict] = None
    ):
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.headers = headers or self.DEFAULT_HEADERS.copy()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def _make_request(
        self,
        url: str,
        params: Dict,
        retry_count: int = 0
    ) -> Optional[str]:
        """
        发送 HTTP 请求，带重试机制
        
        Args:
            url: 请求 URL
            params: 请求参数
            retry_count: 当前重试次数
            
        Returns:
            HTML 内容或 None
        """
        try:
            logger.debug(f"请求 URL: {url}, 参数: {params}")
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败: {e}")
            if retry_count < self.retries:
                logger.info(f"第 {retry_count + 1} 次重试...")
                time.sleep(self.delay * (retry_count + 1))
                return self._make_request(url, params, retry_count + 1)
            else:
                logger.error(f"请求失败，已重试 {self.retries} 次")
                return None
    
    def _parse_web_results(self, html: str) -> List[SearchResult]:
        """
        解析网页搜索结果
        
        Args:
            html: HTML 内容
            
        Returns:
            搜索结果列表
        """
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找搜索结果容器
        containers = soup.find_all('div', class_=re.compile('result|c-container'))
        
        for container in containers:
            try:
                # 提取标题
                title_tag = container.find('h3')
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                
                # 提取链接
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                    
                url = link_tag.get('href', '')
                if url.startswith('/'):
                    url = f"https://www.baidu.com{url}"
                
                # 提取摘要
                abstract_tag = container.find(
                    'span',
                    class_=re.compile('content-right_|abstract')
                ) or container.find('div', class_=re.compile('abstract'))
                
                abstract = ""
                if abstract_tag:
                    abstract = abstract_tag.get_text(strip=True)
                
                # 提取来源
                source_tag = container.find(
                    'span',
                    class_=re.compile('cite|source')
                )
                source = source_tag.get_text(strip=True) if source_tag else ""
                
                result = SearchResult(
                    title=title,
                    url=url,
                    abstract=abstract,
                    source=source
                )
                results.append(result)
                
            except Exception as e:
                logger.warning(f"解析结果时出错: {e}")
                continue
        
        return results
    
    def web_search(
        self,
        query: str,
        num: int = 10,
        page: int = 1
    ) -> List[Dict]:
        """
        网页搜索
        
        Args:
            query: 搜索关键词
            num: 返回结果数量
            page: 页码
            
        Returns:
            搜索结果字典列表
        """
        if not query.strip():
            logger.error("搜索关键词不能为空")
            return []
        
        params = {
            "wd": query,
            "pn": (page - 1) * 10,
            "rn": min(num, 50),  # 百度每页最多50条
            "ie": "utf-8"
        }
        
        logger.info(f"执行网页搜索: {query}, 页码: {page}")
        
        html = self._make_request(
            self.SEARCH_URLS[SearchType.WEB],
            params
        )
        
        if not html:
            return []
        
        results = self._parse_web_results(html)
        
        # 限制返回数量
        results = results[:num]
        
        logger.info(f"获取到 {len(results)} 条结果")
        
        # 请求间隔
        time.sleep(self.delay)
        
        return [r.to_dict() for r in results]
    
    def image_search(
        self,
        query: str,
        num: int = 10,
        page: int = 1
    ) -> List[Dict]:
        """
        图片搜索
        
        Args:
            query: 搜索关键词
            num: 返回结果数量
            page: 页码
            
        Returns:
            图片搜索结果列表
        """
        if not query.strip():
            logger.error("搜索关键词不能为空")
            return []
        
        params = {
            "tn": "baiduimage",
            "word": query,
            "pn": (page - 1) * num,
            "rn": num,
            "ie": "utf-8"
        }
        
        logger.info(f"执行图片搜索: {query}")
        
        html = self._make_request(
            self.SEARCH_URLS[SearchType.IMAGE],
            params
        )
        
        if not html:
            return []
        
        # 解析图片结果
        results = []
        try:
            # 百度图片搜索结果通常在 JS 中
            json_match = re.search(
                r'window\.baidu\.sug\(\{.*?\}\)',
                html
            )
            if json_match:
                data = json.loads(json_match.group())
                # 解析图片数据...
        except Exception as e:
            logger.warning(f"解析图片结果时出错: {e}")
        
        time.sleep(self.delay)
        return results
    
    def news_search(
        self,
        query: str,
        num: int = 10,
        page: int = 1
    ) -> List[Dict]:
        """
        新闻搜索
        
        Args:
            query: 搜索关键词
            num: 返回结果数量
            page: 页码
            
        Returns:
            新闻搜索结果列表
        """
        if not query.strip():
            logger.error("搜索关键词不能为空")
            return []
        
        params = {
            "wd": query,
            "pn": (page - 1) * 10,
            "rn": min(num, 50),
            "tn": "news",
            "ie": "utf-8"
        }
        
        logger.info(f"执行新闻搜索: {query}")
        
        html = self._make_request(
            self.SEARCH_URLS[SearchType.NEWS],
            params
        )
        
        if not html:
            return []
        
        results = self._parse_web_results(html)
        results = results[:num]
        
        logger.info(f"获取到 {len(results)} 条新闻")
        
        time.sleep(self.delay)
        return [r.to_dict() for r in results]
    
    def video_search(
        self,
        query: str,
        num: int = 10,
        page: int = 1
    ) -> List[Dict]:
        """
        视频搜索
        
        Args:
            query: 搜索关键词
            num: 返回结果数量
            page: 页码
            
        Returns:
            视频搜索结果列表
        """
        if not query.strip():
            logger.error("搜索关键词不能为空")
            return []
        
        params = {
            "wd": query,
            "pn": (page - 1) * 10,
            "rn": min(num, 50),
            "tn": "vid",
            "ie": "utf-8"
        }
        
        logger.info(f"执行视频搜索: {query}")
        
        html = self._make_request(
            self.SEARCH_URLS[SearchType.VIDEO],
            params
        )
        
        if not html:
            return []
        
        results = self._parse_web_results(html)
        results = results[:num]
        
        logger.info(f"获取到 {len(results)} 条视频")
        
        time.sleep(self.delay)
        return [r.to_dict() for r in results]


# 便捷函数
def search(query: str, num: int = 10) -> List[Dict]:
    """
    快速搜索函数
    
    Args:
        query: 搜索关键词
        num: 返回结果数量
        
    Returns:
        搜索结果列表
    """
    client = BaiduSearch()
    return client.web_search(query, num=num)


if __name__ == "__main__":
    # 测试代码
    print("百度搜索 API 测试")
    print("=" * 50)
    
    client = BaiduSearch()
    
    # 测试网页搜索
    print("\n1. 网页搜索测试:")
    results = client.web_search("Python 教程", num=5)
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"  标题: {result['title']}")
        print(f"  链接: {result['url']}")
        print(f"  摘要: {result['abstract'][:100]}...")
    
    # 测试新闻搜索
    print("\n2. 新闻搜索测试:")
    results = client.news_search("人工智能", num=3)
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"  标题: {result['title']}")
        print(f"  链接: {result['url']}")
