import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from sphinx.util import requests
from webdriver_manager.chrome import ChromeDriverManager
import time


class Page:
    def __init__(self, operation_system: str, version: str, bay: str, model: str):
        self._operation_system = operation_system
        self._version = version
        self._bay = bay
        self._model = model

    def __str__(self) -> str:
        return f"Page(operation_system = {self._operation_system}, version = {self._version}, bay = {self._bay} model = {self._model})"

    def get_operation_system(self) -> str:
        return self._operation_system

    def get_version(self) -> str:
        return self._version

    def get_bay(self) -> str:
        return self._bay

    def get_model(self) -> str:
        return self._model

    def get_file_path(self, base_path):
        return f"{base_path}/{self._operation_system}/{self._version}/{self._bay}/{self._model}"


def get_options(set, close):
    # 修改aria-hidden属性，使其可交互
    driver.execute_script("arguments[0].setAttribute('aria-hidden', 'false');", set)
    # 打开下拉框
    wait_and_click(set)
    # 定位到div.css-13gtfdj-menu
    wait_select = WebDriverWait(driver, 3)
    select = wait_select.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-13gtfdj-menu')))
    # 在div.css-13gtfdj-menu中找到div.css-uvrstl
    options_select = select.find_element(By.CSS_SELECTOR, 'div.css-uvrstl')
    # 获取所有的product_option元素
    options = wait_select.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="option"]')))
    if close:
        # 关闭product下拉框
        wait_and_click(set)
    return options, wait_select


def download_file(url, local_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"文件已下载至：{local_path}")
    else:
        print(f"下载失败，状态码：{response.status_code}")


def file_name_exists(file_name, folder_path):
    record_file_path = os.path.join(folder_path, 'record_app_center.txt')
    if os.path.exists(record_file_path):
        with open(record_file_path, 'r') as file:
            for line in file:
                record_file_name, record_file_path, release_url = line.strip().split('|')
                if record_file_name == file_name:
                    return record_file_path  # 返回存在的文件路径
    return ""


def save_file_name(file_name, folder_path, file_path, release_url):
    record_file_path = os.path.join(folder_path, 'record_app_center.txt')
    with open(record_file_path, 'a') as file:
        file.write(f"{file_name}|{file_path}|{release_url}\n")


def wait_for_search_sets():
    # 等待所有div.css-xn98a3加载完成并且可交互
    wait_search_sets = WebDriverWait(driver, 5)
    search_sets = wait_search_sets.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.css-xn98a3')))
    return search_sets


def click_close_button():
    wait_for_close_button = WebDriverWait(driver, 5)
    # 首先，等待div元素出现
    wait_for_close_button.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.modal.fade.show')))
    # 然后，等待button元素出现
    close_button = wait_for_close_button.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'div.modal.fade.show button[type="button"]')))
    # 点击关闭按钮
    close_button.click()


def get_options_for_select(wait_select):
    select = wait_select.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-13gtfdj-menu')))
    options_select = select.find_element(By.CSS_SELECTOR, 'div.css-uvrstl')
    options = options_select.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
    return options


def wait_and_click(element):
    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(element))
    element.click()


def process_bay_and_model(bay_set, model_set, product_folder, version_folder, wait_bay_select, k):
    try:
        # 处理Bay选项
        wait_and_click(bay_set)
        bay_options = get_options_for_select(wait_bay_select)
        bay_folder = bay_options[k].text.strip()
        wait_and_click(bay_options[k])

        # 处理Model选项
        model_options, wait_model_select = get_options(model_set, False)
        for model_option in model_options:
            page = Page(product_folder, version_folder, bay_folder, model_option.text.strip())
            page_list.append(page)
            print(page)
        wait_and_click(model_set)
        return True  # 成功处理
    except IndexError:
        print(f"捕获到list index out of range异常，直接返回True, index = {k}")
        return True  # 捕获到list index out of range异常，直接返回True
    except Exception as e:
        print(f"处理过程中发生异常：{e}，将重试...")
        return False  # 发生异常，需要重试


def scroll(element, wait_seconds, driver_scroll):
    driver_scroll.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                 element)
    time.sleep(wait_seconds)


def download_apps(operation_system, get_version, get_model):
    driver_new = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver_new.delete_all_cookies()
    driver_new.set_window_size(1920, 1080)
    driver_new.get(
        f'https://www.qnap.com/en-us/app-center?os={operation_system}'
        f'&version={get_version}'
        f'&model={get_model}')
    # 遍历下载列表并下载
    # 等待item-container中的所有li元素加载完成
    wait_for_items = WebDriverWait(driver_new, 3)
    items = wait_for_items.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.items-container li')))
    for item in items:
        arrow = item.find_element(By.CSS_SELECTOR, 'div.arrow')
        # 滚动到arrow元素可见
        scroll(arrow, 2, driver_new)
        wait_arrow = WebDriverWait(driver_new, 5)
        try:
            wait_arrow.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.arrow')))
            wait_arrow.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.arrow')))
            driver_new.execute_script("arguments[0].click();", arrow)
        except Exception as e:
            print('failed:  ' + item.text.strip())
            print(e)
            continue
        # 等待页面加载
        wait_for_button_container = WebDriverWait(driver_new, 5)
        # 定位到包含下载链接的div容器
        button_container = (wait_for_button_container
                            .until(EC.presence_of_element_located((By.XPATH, '//div[@class="d-flex '
                                                                             'flex-wrap '
                                                                             'justify-content-center '
                                                                             'qnap-bs-btn-container '
                                                                             'dark-bg '
                                                                             'justify-content-xl-end"]'))))

        # 在容器中找到所有的a标签
        links = button_container.find_elements(By.TAG_NAME, 'a')

        # 从这些a标签中找到下载链接
        download_link = None
        if 'btn-bs-arrow--secondary' in links[-1].get_attribute('class'):
            download_link = links[-1]

        # 获取下载链接的URL
        if download_link:
            download_url = download_link.get_attribute('href')
            # 构造下载路径
            folder_name = page.get_file_path(download_path)
            os.makedirs(folder_name, exist_ok=True)
            file_name = download_url.split('/')[-1]
            local_file_path = os.path.join(folder_name, file_name)

            existing_file_path = file_name_exists(file_name, download_path)
            if existing_file_path != "":
                print(f"文件名 {file_name} 已存在，创建软链接至{folder_name}。")
                try:
                    os.symlink(existing_file_path, local_file_path)  # 创建软链接
                except FileExistsError:
                    pass
            else:
                download_file(download_url, local_file_path)
                release_link = None
                release_url = "None"
                if 'btn-bs-arrow--secondary-outline' in links[0].get_attribute('class'):
                    release_link = links[0]
                if release_link:
                    release_url = release_link.get_attribute('href')

                save_file_name(file_name, download_path, local_file_path, release_url)  # 记录文件名、路径和release链接
        else:
            print("Download link not found")
        click_close_button()
    driver_new.quit()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("请提供下载路径作为参数。")
        exit(1)

    download_path = sys.argv[1] + '/app_center_download'

    if not os.path.exists(download_path):
        print(f"下载路径 {download_path} 不存在，正在创建...")
        os.makedirs(download_path, exist_ok=True)
    page_list = []

    # 设置Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--incognito")  # 使用无痕模式
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_window_size(1920, 1080)  # 设置窗口大小为1920x1080
    download_center_url = 'https://www.qnap.com/en-us/app-center?os=qts&version=5.2.1'

    # 访问页面
    driver.get(download_center_url)

    search_sets = wait_for_search_sets()

    product_set = search_sets[0]
    version_set = search_sets[1]
    bay_set = search_sets[2]
    model_set = search_sets[3]

    # Product
    product_options, wait_product_select = get_options(product_set, True)

    # 依次点击选择所有product_option
    for i in range(len(product_options)):
        # 打开product下拉框
        wait_and_click(product_set)
        product_options = get_options_for_select(wait_product_select)
        product_folder = product_options[i].text.strip()
        wait_and_click(product_options[i])

        # Version
        version_options, wait_version_select = get_options(version_set, True)
        for j in range(len(version_options)):
            wait_and_click(version_set)
            version_options = get_options_for_select(wait_version_select)
            version_folder = version_options[j].text.strip()
            wait_and_click(version_options[j])
            try:
                # Bay
                bay_options, wait_bay_select = get_options(bay_set, True)
            except Exception as e:
                print("get bays failed! continue...")
                print(e)
                continue

            if len(bay_options) > 0:
                for k in range(len(bay_options)):
                    # 重试逻辑
                    max_retries = 3  # 设置最大重试次数
                    retry_count = 0
                    while retry_count < max_retries:
                        if process_bay_and_model(bay_set, model_set, product_folder, version_folder, wait_bay_select,
                                                 k):
                            break  # 如果处理成功，退出循环
                        retry_count += 1
                        if retry_count == max_retries:
                            print(f"处理Bay选项 {k} 时已达到最大重试次数，放弃处理。")
                            break  # 达到最大重试次数，退出循环
    driver.quit()
    time.sleep(5)

    # 依次访问所有页面 遍历下载其中内容
    for page in page_list:
        download_apps(page.get_operation_system(), page.get_version(), page.get_model())
