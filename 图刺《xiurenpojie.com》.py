import requests
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# 设置请求头，模拟浏览器行为
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

# 提取 HTML 内容中的倒数第二个 <script> 标签
def extract_second_last_script(content):
    script_tags = re.findall(r'<script[^>]*>.*?</script>', content, re.DOTALL)
    if len(script_tags) >= 2:
        return script_tags[-2]
    else:
        print("HTML中<script>标签不足两个，无法提取倒数第二个。")
        return None

# 对 HTML 内容进行 Unicode 转义，还原转义字符
def decode_unicode_escape(content):
    return content.encode('utf-8').decode('unicode_escape')

# 提取所有 src="..." 链接
def extract_src_links(content):
    return re.findall(r'src="([^"]+)"', content)

# 下载图片并重命名
def download_image(image_url, save_path, index):
    try:
        response = requests.get(image_url, headers=headers, stream=True)
        response.raise_for_status()  # 确保请求成功

        # 获取文件格式
        content_type = response.headers.get('Content-Type')
        if content_type:
            if 'image/jpeg' in content_type:
                extension = '.jpg'
            elif 'image/png' in content_type:
                extension = '.png'
            elif 'image/gif' in content_type:
                extension = '.gif'
            else:
                extension = '.jpg'  # 默认使用 .jpg 格式
        else:
            extension = '.jpg'

        # 图片保存路径
        image_name = f"{index + 1}{extension}"
        image_file_path = os.path.join(save_path, image_name)

        # 保存图片
        with open(image_file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"图片 {index + 1} 下载完成：{image_file_path}")
    except requests.RequestException as e:
        print(f"下载图片失败: {image_url}, 错误: {e}")

# 提取图集名称
def extract_album_name(content):
    match = re.search(r'<title>(.*?)</title>', content)
    if match:
        album_name = match.group(1).replace(" - 秀人网破解版", "").replace("風流雜誌", "").replace("#038;", "").replace("#8211;", "")
        return album_name
    return "Unknown_Album"

# 防反爬机制：添加延时
def delay_request():
    time.sleep(1)

def main():
    # 获取用户输入的网址
    url = input("请输入想要下载的网页地址（《xiurenpojie.com》查询）: ")

    # 获取网页内容
    html_content = fetch_html_from_url(url)
    if html_content:
        # 提取图集名称
        album_name = extract_album_name(html_content)

        # 创建保存图片的文件夹
        if not os.path.exists(album_name):
            os.makedirs(album_name)

        # 提取倒数第二个 <script> 标签的内容
        second_last_script = extract_second_last_script(html_content)
        if second_last_script:
            # 对倒数第二个<script>标签内容进行Unicode转义还原
            decoded_content = decode_unicode_escape(second_last_script)

            # 提取所有 src="..." 链接
            src_links = extract_src_links(decoded_content)
            print(f"提取到 {len(src_links)} 个图片链接，开始下载...")

            # 使用线程池来下载图片
            with ThreadPoolExecutor(max_workers=10) as executor:
                for index, link in enumerate(src_links):
                    executor.submit(download_image, link, album_name, index)
                    delay_request()  # 防反爬延时

            print("所有图片下载任务已提交。")
        else:
            print("未能成功提取倒数第二个<script>标签。")
    else:
        print("未能成功获取网页内容。")

if __name__ == "__main__":
    main()
