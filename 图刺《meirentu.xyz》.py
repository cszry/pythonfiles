import requests
from PIL import Image
from io import BytesIO
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 创建一个会话对象
session = requests.Session()

# 配置重试机制
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)

# 用户手动输入网页链接
url = input("请输入网页URL（《meirentu.xyz》查询）: ")

# 模拟浏览器请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
}

def random_sleep():
    """随机等待，模拟人类行为"""
    time.sleep(random.uniform(1, 3))

def download_image(img_url, title, idx):
    """下载图片"""
    try:
        if not img_url.startswith("http"):
            img_url = "https:" + img_url  # 补全 URL
        
        img_headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
            ]),
            "Referer": url,
            "Dnt": "1"
        }

        img_response = session.get(img_url, headers=img_headers)
        if img_response.status_code == 200:
            img = Image.open(BytesIO(img_response.content))
            img_path = os.path.join(title, f"{idx + 1}.jpg")
            img.save(img_path)
            print(f"图片 {idx + 1} 已保存到 {title} 文件夹！")
        else:
            print(f"图片 {idx + 1} 请求失败，状态码：{img_response.status_code}")
        random_sleep()
    except Exception as e:
        print(f"下载图片 {idx + 1} 时出错: {e}")

def download_images_from_page(url, start_idx=0):
    """下载页面上的所有图片并获取下页链接"""
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功

        if response.status_code == 200:
            # 解析网页源码
            soup = BeautifulSoup(response.text, 'html.parser')

            # 获取页面标题并创建文件夹
            title = soup.title.string if soup.title else 'default_title'
            title = title.replace("_写真美图 - 美人图", "").strip()  # 去掉不需要的部分
            if not os.path.exists(title):
                os.makedirs(title)

            # 找到所有的 img 标签，并提取 src 属性
            img_tags = soup.find_all('img', {'src': True})
            img_urls = [img['src'] for img in img_tags]

            # 从第二个链接开始下载图片
            img_urls_to_download = img_urls[1:]  # 从第二个图片链接开始

            # 创建线程池进行并发下载
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_idx = {executor.submit(download_image, img_url, title, idx): idx
                                 for idx, img_url in enumerate(img_urls_to_download, start=start_idx)}
                
                # 等待下载任务完成
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        future.result()  # 捕获下载时的异常
                    except Exception as e:
                        print(f"图片 {idx + 1} 下载失败，错误：{e}")

            # 检查是否有“下页”链接
            next_page_tag = soup.find('a', string="下页")
            if next_page_tag:
                next_page_url = next_page_tag.get('href')
                if next_page_url:
                    next_page_url = 'https://meirentu.xyz' + next_page_url  # 完善链接
                    print(f"找到下页，正在下载 {next_page_url}")
                    # 递归调用下载下一个页面的内容，并传递新的起始索引
                    download_images_from_page(next_page_url, start_idx=start_idx + len(img_urls_to_download))
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

# 开始下载第一页
download_images_from_page(url)
print(f"所有图片已下载完毕！")
