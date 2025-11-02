import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from multiprocessing.dummy import Pool as ThreadPool

# ========== 基础配置 ==========
BASE_URL = "https://www.xftoon.com"
DIRECTORY_URL = f"{BASE_URL}/comic/7264"
SAVE_ROOT = r"E:\娱乐\漫画"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36 Edg/115.0.1901.157',
    'Referer': DIRECTORY_URL
}

# ========== 工具函数 ==========

def create_folder(folder_path):
    """创建文件夹"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"✅ 文件夹已创建: {folder_path}")
    else:
        print(f"📁 文件夹已存在: {folder_path}")

def write_file(file_path, data):
    """写入文本文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"💾 文件已保存: {file_path}")

def read_file(file_path):
    """读取文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def fetch_html(url):
    """带重试机制的网页请求"""
    for i in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 请求失败 ({i+1}/3): {url} - {e}")
            time.sleep(2)
    print(f"❌ 彻底失败: {url}")
    with open("error.txt", "a", encoding="utf-8") as err:
        err.write(f"{url}\n")
    return None

# ========== 数据解析部分 ==========

def fetch_directory_page():
    """下载目录页并保存为 HTML"""
    html = fetch_html(DIRECTORY_URL)
    if html:
        write_file("directory.html", html)

def parse_directory():
    """从目录页提取章节 JSON 数据"""
    html = read_file("directory.html")
    soup = BeautifulSoup(html, 'html.parser')
    data_script = soup.find_all('script')[11]
    json_text = str(data_script)[132:-519]  # xftoon 特定偏移
    write_file("directory.json", json_text)
    print("📑 目录 JSON 解析完成")

def get_title():
    """获取漫画标题+作者"""
    soup = BeautifulSoup(read_file("directory.html"), 'html.parser')
    book_title = soup.select('.subHeader .BarTit')[0].get_text(strip=True)
    author_name = soup.select('.txtItme a')[0].get_text(strip=True)
    return f"{book_title} ({author_name})"

# ========== 图片下载部分 ==========

def download_image(image_url, path_name):
    """下载图片（带重试机制）"""
    if os.path.exists(path_name):
        print(f"✅ 已存在: {path_name}")
        return
    for attempt in range(3):
        try:
            res = requests.get(image_url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            with open(path_name, "wb") as f:
                f.write(res.content)
            print(f"🖼️ 已下载: {path_name}")
            return
        except Exception as e:
            print(f"⚠️ 下载失败 ({attempt+1}/3): {image_url} - {e}")
            time.sleep(2)
    with open("error.txt", "a", encoding="utf-8") as err:
        err.write(f"{image_url}\n")

def download_images(image_list, file_name, head_word):
    """多线程下载章节图片"""
    create_folder(head_word)
    pool = ThreadPool(5)
    for img in image_list:
        img_url = img["imgUrl"]
        img_id = img["id"]
        suffix = os.path.splitext(os.path.basename(urlparse(img_url).path))[1]
        path_name = os.path.join(head_word, f"{img_id}_{file_name}{suffix}")
        pool.apply_async(download_image, (img_url, path_name))
    pool.close()
    pool.join()

# ========== 页面爬取部分 ==========

def get_page_links(start_url, chapter_list):
    """递归获取页面链接"""
    retries = 3
    for _ in range(retries):
        try:
            print(f"📖 正在获取章节分页链接: {start_url}")
            soup = BeautifulSoup(requests.get(start_url, headers=HEADERS, timeout=10).text, 'html.parser')
            next_link_tag = soup.select('.letchepter .ChapterLestMune')
            if not next_link_tag:
                return chapter_list

            next_link = next_link_tag[0].get('href')
            next_text = next_link_tag[0].get_text(strip=True)

            # 判断是否为下一页
            if "下一页" in next_text:
                # 处理正常和短路径两种情况
                if len(next_link) > 12:
                    next_url = BASE_URL + next_link
                else:
                    script_data = soup.find_all('script')[12]
                    part1 = str(script_data)[50:54]
                    part2 = str(script_data)[79:85]
                    next_url = f"{BASE_URL}/view/{part1}/{part2}/{next_link}"

                if next_url not in chapter_list:
                    chapter_list.append(next_url)
                    return get_page_links(next_url, chapter_list)
            return chapter_list
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 获取页面链接错误: {start_url} - {e}")
            time.sleep(2)
            if _ == retries - 1:
                return chapter_list

def process_chapters():
    """解析章节并下载所有图片"""
    json_array = json.loads(read_file("directory.json"))
    title_folder = os.path.join(SAVE_ROOT, get_title())
    create_folder(title_folder)

    for item in json_array:
        chapter_id = item["id"]
        chapter_title = item["title"].replace("?", "").replace(":", "").replace(".", "")
        start_url = f"{BASE_URL}/view/{item['comic_id']}/{chapter_id}"
        head_word = os.path.join(title_folder, chapter_title)

        print(f"\n📘 开始处理章节: {chapter_title}")
        chapter_pages = get_page_links(start_url, [start_url])
        print(f"➡️ 共 {len(chapter_pages)} 页")

        # 收集所有图片链接
        image_list = []
        for page_url in chapter_pages:
            html = fetch_html(page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            imgs = soup.select('#commicBox .charpetBox img')
            for idx, img in enumerate(imgs, start=len(image_list) + 1):
                img_url = img.get('data-original', '').replace("httpss", "https")
                if img_url:
                    image_list.append({"id": idx, "imgUrl": img_url})

        # 下载章节图片
        if image_list:
            print(f"📸 共 {len(image_list)} 张图片，开始下载...")
            download_images(image_list, chapter_title, head_word)
        else:
            print(f"⚠️ 未发现图片: {chapter_title}")

# ========== 主程序入口 ==========

if __name__ == "__main__":
    print("🚀 启动xftoon 漫画下载器")
    open("error.txt", "w", encoding="utf-8").close()
    fetch_directory_page()
    parse_directory()
    process_chapters()
    print("🎉 所有章节下载完成！")
