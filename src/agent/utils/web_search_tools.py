import json
from typing import Annotated
from urllib.parse import quote

import requests
from langchain_core.tools import tool
from bs4 import BeautifulSoup

from agent.utils.log_util import log


@tool
def web_search(
    query: Annotated[str, "搜索关键词"],
    num_results: Annotated[int, "返回结果数量，默认10条"] = 10,
) -> str:
    """执行百度网页搜索，返回相关网页结果。

    Args:
        query: 搜索关键词
        num_results: 返回结果数量，默认10条

    Returns:
        搜索结果列表，包含标题、链接和摘要
    """
    try:
        encoded_query = quote(query)
        url = f"https://www.baidu.com/s?wd={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        containers = soup.select(".result, .c-container")

        for container in containers[:num_results]:
            try:
                title_elem = container.select_one("h3, .t")
                link_elem = container.select_one("a")
                abstract_elem = container.select_one(
                    ".content-right_8Zs40, .c-abstract, .content"
                )

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    href = link_elem.get("href", "")
                    abstract = (
                        abstract_elem.get_text(strip=True)
                        if abstract_elem
                        else "暂无摘要"
                    )

                    results.append({
                        "title": title,
                        "link": href,
                        "abstract": abstract,
                    })
            except Exception as e:
                log.debug(f"解析单个结果时出错: {e}")
                continue

        if not results:
            return json.dumps({
                "status": "no_results",
                "message": "未找到搜索结果，请尝试其他关键词",
                "query": query,
            }, ensure_ascii=False)

        return json.dumps({
            "status": "success",
            "query": query,
            "total_results": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        log.error(f"搜索失败: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "query": query,
        }, ensure_ascii=False)


@tool
def search_news(
    query: Annotated[str, "搜索关键词"],
    num_results: Annotated[int, "返回结果数量，默认10条"] = 10,
) -> str:
    """执行百度新闻搜索，专门搜索新闻类内容。

    Args:
        query: 搜索关键词
        num_results: 返回结果数量，默认10条

    Returns:
        新闻搜索结果列表，包含标题、链接、摘要和来源
    """
    try:
        encoded_query = quote(query)
        url = f"https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&word={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        news_items = soup.select(".result, .news-list li")

        for item in news_items[:num_results]:
            try:
                title_elem = item.select_one("h3, .title, a")
                link_elem = item.select_one("a")
                source_elem = item.select_one(
                    ".c-color-gray, .source, .c-span-color-gray"
                )
                time_elem = item.select_one(".c-color-gray2, .time")

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    href = link_elem.get("href", "")
                    source = (
                        source_elem.get_text(strip=True) if source_elem else "未知来源"
                    )
                    publish_time = (
                        time_elem.get_text(strip=True) if time_elem else "未知时间"
                    )

                    results.append({
                        "title": title,
                        "link": href,
                        "source": source,
                        "publish_time": publish_time,
                    })
            except Exception as e:
                log.debug(f"解析新闻结果时出错: {e}")
                continue

        if not results:
            return json.dumps({
                "status": "no_results",
                "message": "未找到新闻结果，请尝试其他关键词",
                "query": query,
            }, ensure_ascii=False)

        return json.dumps({
            "status": "success",
            "query": query,
            "total_results": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        log.error(f"新闻搜索失败: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"新闻搜索失败: {str(e)}",
            "query": query,
        }, ensure_ascii=False)
