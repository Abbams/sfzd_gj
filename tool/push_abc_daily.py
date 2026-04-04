import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 缓存根目录
CACHE_DIR = "atcoder_cache"

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(contest_id, task_suffix):
    """生成缓存文件路径，例如: atcoder_cache/awc0039_b.html"""
    filename = f"{contest_id}_{task_suffix}.html"
    return os.path.join(CACHE_DIR, filename)

def fetch_or_load(url, cache_path, force_refresh=False):
    """
    如果缓存存在且不强制刷新，则从本地读取；
    否则发起网络请求，保存到缓存，并返回内容（字符串）。
    """
    if not force_refresh and os.path.exists(cache_path):
        print(f"使用缓存: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"拉取: {url}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            content = resp.text
            # 写入缓存
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"已保存缓存: {cache_path}")
            return content
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            raise

def parse_task_page(html_content):
    """示例：解析页面，这里可以根据需要提取题目信息，当前仅返回 BeautifulSoup 对象"""
    return BeautifulSoup(html_content, 'html.parser')

def main():
    races = [39]  # 可扩展多个
    ensure_cache_dir()

    for race_id in races:
        contest_id = f"awc{str(race_id).zfill(4)}"
        task_suffix = "b"   # 本题为 _b，可改成变量
        url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{task_suffix}"
        cache_path = get_cache_path(contest_id, task_suffix)

        try:
            html = fetch_or_load(url, cache_path, force_refresh=False)
            soup = parse_task_page(html)
            # 示例：打印页面标题，确认成功
            statement_div = soup.find_all('div', class_='part')
            print(statement_div[10].text)
            print(f"页面标题: {soup.title.string if soup.title else '无标题'}")
        except Exception as e:
            print(f"处理 {contest_id} 失败: {e}")

if __name__ == "__main__":
    main()