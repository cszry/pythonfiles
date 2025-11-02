import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_driver(user_agent, headless=False):
    """创建并返回配置好的 Chrome 驱动"""
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if headless:
        chrome_options.add_argument("--headless")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        """
    })
    return driver

def extract_img_links(html):
    """提取 <div class="nbodys"> 中所有 img 标签中的 src 链接"""
    soup = BeautifulSoup(html, "html.parser")
    nbodys_div = soup.find("div", class_="nbodys")
    img_tags = nbodys_div.find_all("img", class_="details-banner-imgs") if nbodys_div else []
    img_links = [img.get("src") for img in img_tags if img.get("src")]
    return img_links

def extract_title(html):
    """提取 <h1> 标签中的文本作为文件夹名称"""
    soup = BeautifulSoup(html, "html.parser")
    h1_tag = soup.find("h1")
    title = h1_tag.text.strip() if h1_tag else "default_title"
    return title

def download_image(img_url, folder, img_name):
    """下载图片并保存到指定文件夹"""
    try:
        response = requests.get(img_url)
        if response.status_code == 200:
            img_path = os.path.join(folder, f"{img_name}.jpg")
            with open(img_path, "wb") as file:
                file.write(response.content)
            print(f"Image {img_name} downloaded successfully.")
        else:
            print(f"Failed to download {img_name}.")
    except Exception as e:
        print(f"Error downloading {img_name}: {e}")

def download_images_parallel(img_links, folder):
    """使用多线程下载图片"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, img_url in enumerate(img_links, start=1):
            futures.append(executor.submit(download_image, img_url, folder, str(i)))
        for future in as_completed(futures):
            future.result()  # 获取结果，等待任务完成

def main():
    # 让用户输入URL
    url = input("请输入要爬取图片的网页链接（《https://sxccgknmm.top/main.html》查询）：")
    
    ua = UserAgent()
    user_agent = ua.random

    print("启动 Selenium，打开网页 ...")
    driver = create_driver(user_agent, headless=False)
    driver.get(url)

    try:
        print("等待页面 JavaScript 渲染 ...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(random.uniform(2, 4))  # 模拟人类操作延时
        after_html = driver.page_source

        # 提取标题用于命名文件夹
        title = extract_title(after_html)
        folder_path = os.path.join(os.getcwd(), title)
        os.makedirs(folder_path, exist_ok=True)

        print("提取图片链接...")
        img_links = extract_img_links(after_html)

        print("下载图片...")
        download_images_parallel(img_links, folder_path)

    except Exception as e:
        print("渲染等待失败:", e)
    finally:
        driver.quit()
        print("浏览器关闭，任务完成。")

if __name__ == "__main__":
    main()
