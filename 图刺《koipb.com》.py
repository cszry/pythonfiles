import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os
import time

# 记录开始时间
start_time = time.time()

# 用户手动输入网页链接
url = input("请输入网页URL（《koipb.com》查询）: ")

# 模拟浏览器请求头，防止反爬虫
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 发送GET请求获取网页内容
response = requests.get(url, headers=headers)

# 确保请求成功
if response.status_code == 200:
    # 解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取网页标题中的昵称并去掉 " - Girl Atlas"
    title = soup.title.string if soup.title else ""
    folder_name = title.replace(" - Girl Atlas", "").strip()
    
    # 创建保存图片的文件夹
    os.makedirs(folder_name, exist_ok=True)

    # 查找所有的 <a> 标签，其中包含图片链接
    links = soup.find_all('a', {'data-src': True})
    
    # 提取所有图片的URL
    img_urls = [link['data-src'] for link in links]
    
    def download_image(url, index):
        try:
            # 发送GET请求获取图片
            img_data = requests.get(url, headers=headers).content
            # 使用顺序数字作为图片文件名
            img_name = f"{index+1}.jpg"
            # 保存图片到本地
            with open(f'{folder_name}/{img_name}', 'wb') as file:
                file.write(img_data)
            print(f"已成功下载: {img_name}")
        except Exception as e:
            print(f"下载失败: {url}，错误: {e}")

    # 使用ThreadPoolExecutor进行多线程下载
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda i: download_image(img_urls[i], i), range(len(img_urls)))
    
    # 记录结束时间
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"所有图片下载完成！")
    print(f"程序运行时长: {elapsed_time:.2f} 秒")
else:
    print("网页请求失败，状态码:", response.status_code)
