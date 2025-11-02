import requests
import re
import os
from PIL import Image
from io import BytesIO
from threading import Thread
from queue import Queue
from bs4 import BeautifulSoup

# 设置请求头，模拟浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 从给定网址获取 HTML 内容
def fetch_html_from_url(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        return response.text
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

# 提取网页标题，并处理文件夹名
def extract_folder_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.string if soup.title else "默认标题"
    # 删除“妖精”两字
    folder_name = title.replace("妖精社 – ", "").replace(" – 風流雜誌", "").replace("愛絲 – ", "")
    folder_name = folder_name.strip()  # 去除两端空白字符
    return folder_name

# 提取具有 class="aligncenter" 的 <img> 标签中的 src 链接
def extract_img_src_links(content):
    return re.findall(r'<img [^>]*class="aligncenter"[^>]*src="([^"]+)"', content)

# 提取分页链接（“下一页”）
def extract_next_page_link(content):
    match = re.search(r'<a href="([^"]+)" class="post-page-numbers">下一頁 »</a>', content)
    return match.group(1) if match else None

# 保存图片到本地并重命名
def save_image(img_url, folder_name, img_counter):
    try:
        response = requests.get(img_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img_extension = img_url.split('.')[-1]
        img_name = f"{img_counter + 1}.{img_extension}"
        img.save(os.path.join(folder_name, img_name))
        print(f"图片 {img_name} 已保存。")
    except Exception as e:
        print(f"下载图片失败: {e}")

# 获取所有分页链接
def fetch_all_pages_links(url):
    all_links = []
    current_url = url
    while current_url:
        print(f"正在抓取: {current_url}")
        html_content = fetch_html_from_url(current_url)
        if not html_content:
            print("未能成功获取页面内容，停止抓取。")
            break
        img_src_links = extract_img_src_links(html_content)
        all_links.extend(img_src_links)
        next_page = extract_next_page_link(html_content)
        if next_page:
            current_url = next_page
        else:
            current_url = None
    return all_links

# 处理多线程下载图片
def download_images_threaded(img_links, folder_name):
    img_counter = 0
    queue = Queue()
    threads = []
    for img_url in img_links:
        queue.put(img_url)
    while not queue.empty():
        img_url = queue.get()
        img_counter += 1
        thread = Thread(target=save_image, args=(img_url, folder_name, img_counter))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

def main():
    # 让用户输入目标网址
    url = input("请输入目标网址（《trendszine.com》查询：")

    # 获取页面内容
    html_content = fetch_html_from_url(url)
    if not html_content:
        print("未能成功获取页面内容，程序终止。")
        return

    # 获取文件夹名称，并处理掉“妖精”
    folder_name = extract_folder_name(html_content)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    # 获取所有分页页面中的图片链接
    img_src_links = fetch_all_pages_links(url)

    # 使用多线程下载图片
    download_images_threaded(img_src_links, folder_name)

if __name__ == "__main__":
    main()
    print("任务已经完成，我的主人哟")
