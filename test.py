import os
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sphinx.util import requests
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sys


class Model:
    def __init__(self, bay: str, name: str) -> None:
        self._bay = bay
        self._name = name

    def __str__(self) -> str:
        return f"Model(bay={self._bay}, name={self._name})"

    def get_bay(self) -> str:
        return self._bay

    def get_name(self) -> str:
        return self._name

    def download_document(self, base_url) -> None:
        url = f"{base_url}?model={self._name}&category=documents"

    def download_utility(self, base_url) -> None:
        url = f"{base_url}?model={self._name}&category=utility"

    def download_firmware_or_utility(self, base_url, driver, download_path, category) -> None:
        url = f"{base_url}?model={self._name}&category={category}"
        try:
            # 获取当前页面的窗口句柄
            current_window_handle = driver.current_window_handle

            # 使用driver打开新的窗口或标签页
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])  # 切换到新窗口

            driver.get(url)

            # 等待页面加载完成，确保download_list里的tr元素可见
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#download_list tr"))
            )

            # 获取页面源代码
            html = driver.page_source

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 定位到id为'download_list'的div元素
            download_list = soup.find('div', id='download_list')

            if download_list:
                # 遍历tbody中的每一个tr元素
                for tr in download_list.find_all('tr'):
                    # 提取下载链接
                    download_links = tr.find_all('a')
                    for link in download_links:
                        href = link.get('href')
                        if href:
                            # 构造下载路径
                            folder_name = f"{download_path}/{self._bay}/{self._name}/{self.get_category(driver.current_url)}"
                            os.makedirs(folder_name, exist_ok=True)
                            file_name = os.path.basename(urlparse(href).path)
                            download_url = href
                            local_file_path = os.path.join(folder_name, file_name)

                            # 检查MD5码是否已存在
                            md5_value = self.get_md5(tr)
                            if md5_value and not self.md5_exists(md5_value, file_name, download_path):
                                # 下载文件
                                self.download_file(download_url, local_file_path)
                                # 保存MD5码到record.txt
                                self.save_md5(md5_value, file_name, download_path)
                            else:
                                print(f"MD5值 {md5_value} 和文件名 {file_name} 已存在，跳过下载。")
                            break  # 成功一次后即停止

            # 关闭新窗口并切换回原来的窗口
            driver.close()
            driver.switch_to.window(current_window_handle)

        except Exception as e:
            print(f"发生错误：{e}")


    def get_category(self, url):
        if 'firmware' in url:
            return 'firmware'
        elif 'utility' in url:
            return 'utility'
        elif 'documents' in url:
            return 'documents'
        return 'unknown'

    def get_md5(self, tr):
        md5_inputs = tr.find_all('label', text='MD5')
        for md5_input in md5_inputs:
            md5_value = md5_input.find_next('input')['value']
            return md5_value
        return None

    def save_md5(self, md5_value, file_name, folder_path):
        record_file_path = os.path.join(folder_path, 'record.txt')
        with open(record_file_path, 'a') as file:
            file.write(f"{md5_value}:{file_name}\n")

    def md5_exists(self, md5_value, file_name, folder_path):
        record_file_path = os.path.join(folder_path, 'record.txt')
        if os.path.exists(record_file_path):
            with open(record_file_path, 'r') as file:
                for line in file:
                    record_md5, record_file_name = line.strip().split(':')
                    if record_md5 == md5_value and record_file_name == file_name:
                        return True
        return False

    def download_file(self, url, local_path):
        response = requests.get('https:' + url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            print(f"文件已下载至：{local_path}")
        else:
            print(f"下载失败，状态码：{response.status_code}")

    def get_download_list(self, driver, url):
        # 使用driver打开新的窗口或标签页
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])  # 切换到新窗口
        driver.get(url)
        # 等待页面加载完成，确保download_list里的tr元素可见
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#download_list tr"))
        )
        # 获取页面源代码
        html = driver.page_source
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        # 定位到id为'download_list'的div元素
        download_list = soup.find('div', id='download_list')
        return download_list


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("请提供下载路径作为参数。")
        exit(1)

    download_path = sys.argv[1]

    if not os.path.exists(download_path):
        print(f"下载路径 {download_path} 不存在，正在创建...")
        os.makedirs(download_path, exist_ok=True)

    # 设置Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    model_list = []  # 用于存放model

    download_center_url = 'https://www.qnap.com/en-us/download'
    # 访问页面
    driver.get(download_center_url)

    time.sleep(5)  # 等待5秒，确保页面加载完成

    # 查找下载中心的容器
    download_center_div = driver.find_element(By.ID, 'download_center')

    # 查找所有的com-select-set元素
    com_select_sets = download_center_div.find_elements(By.CSS_SELECTOR, 'div.com-select-set')

    if len(com_select_sets) >= 2:
        # Product Type
        product_type_select_div = com_select_sets[0]
        product_type_select = product_type_select_div.find_element(By.TAG_NAME, 'select')
        # NAS
        first_option = product_type_select.find_elements(By.TAG_NAME, 'option')[1]
        first_option.click()

        time.sleep(2)

        # Bay
        bay_select_div = com_select_sets[1]
        bay_select = bay_select_div.find_element(By.TAG_NAME, 'select')
        bay_select_options = bay_select.find_elements(By.TAG_NAME, 'option')
        del bay_select_options[0]

        for bay_option in bay_select_options:
            bay_option.click()

            wait = WebDriverWait(driver, 10)
            # 等待直到model-select元素中的所有option元素都可见
            wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "select#model-select option")))

            # Model
            model_select_div = (driver.find_element(By.ID, 'download_center')
                                .find_elements(By.CSS_SELECTOR, 'div.com-select-set'))[2]
            model_select = model_select_div.find_element(By.TAG_NAME, 'select')
            model_select_options = model_select.find_elements(By.TAG_NAME, 'option')
            del model_select_options[0]  # 去除choose

            # Check & Download
            for model_option in model_select_options:
                model = Model(bay_option.text.strip(), model_option.text.strip())
                print(model)
                model_list.append(model)

                model.download_firmware_or_utility(download_center_url, driver, download_path, 'firmware')
                model.download_firmware_or_utility(download_center_url, driver, download_path, 'utility')
                # model.download_document(download_center_url)

    driver.quit()
