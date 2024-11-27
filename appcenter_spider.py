import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from sphinx.util import requests
from webdriver_manager.chrome import ChromeDriverManager
import time


def get_options(set):
    # 修改aria-hidden属性，使其可交互
    driver.execute_script("arguments[0].setAttribute('aria-hidden', 'false');", set)
    # 滚动到元素可见
    driver.execute_script("arguments[0].scrollIntoView();", set)
    # 打开下拉框
    set.click()
    # 定位到div.css-13gtfdj-menu
    wait_select = WebDriverWait(driver, 10)
    select = wait_select.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-13gtfdj-menu')))
    # 在div.css-13gtfdj-menu中找到div.css-uvrstl
    options_select = select.find_element(By.CSS_SELECTOR, 'div.css-uvrstl')
    # 获取所有的product_option元素
    options = options_select.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
    # 关闭product下拉框
    set.click()
    return options, wait_select


def get_options_for_select(wait_select):
    select = wait_select.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.css-13gtfdj-menu')))
    options_select = select.find_element(By.CSS_SELECTOR, 'div.css-uvrstl')
    options = options_select.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
    return options


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
                record_file_name = line.strip()
                if record_file_name == file_name:
                    return True
    return False


def save_file_name(file_name, folder_path):
    record_file_path = os.path.join(folder_path, 'record_app_center.txt')
    with open(record_file_path, 'a') as file:
        file.write(f"{file_name}\n")


def wait_for_search_sets():
    # 等待所有div.css-xn98a3加载完成并且可交互
    wait_search_sets = WebDriverWait(driver, 10)
    search_sets = wait_search_sets.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.css-xn98a3')))
    return search_sets


def click_close_button():
    wait_for_close_button = WebDriverWait(driver, 10)
    # 首先，等待div元素出现
    wait_for_close_button.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.modal.fade.show')))
    # 然后，等待button元素出现
    close_button = wait_for_close_button.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'div.modal.fade.show button[type="button"]')))
    # 点击关闭按钮
    close_button.click()


def scroll(element, wait_seconds):
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                          element)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(model_set))
    time.sleep(wait_seconds)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("请提供下载路径作为参数。")
        exit(1)

    download_path = sys.argv[1] + '/app_center_download'

    if not os.path.exists(download_path):
        print(f"下载路径 {download_path} 不存在，正在创建...")
        os.makedirs(download_path, exist_ok=True)

    # 设置Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.set_window_size(1920, 1080)  # 设置窗口大小为1920x1080

    download_center_url = 'https://www.qnap.com/en-us/app-center?os=qts&version=5.2.1'

    # 访问页面
    driver.get(download_center_url)

    # 等待页面加载
    time.sleep(2)

    search_sets = wait_for_search_sets()

    product_set = search_sets[0]
    version_set = search_sets[1]
    bay_set = search_sets[2]
    model_set = search_sets[3]

    # Product
    product_options, wait_product_select = get_options(product_set)

    # 依次点击选择所有product_option
    for i in range(len(product_options)):
        scroll(product_set, 5)
        wait_for_search_sets()
        # 打开product下拉框
        product_set.click()
        # 等待下拉框可见
        time.sleep(2)
        # 重新获取下拉菜单和选项的最新引用
        product_options = get_options_for_select(wait_product_select)
        product_folder = product_options[i].text.strip()
        product_options[i].click()

        # Version
        version_options, wait_version_select = get_options(version_set)
        for j in range(len(version_options)):
            scroll(version_set, 5)
            wait_for_search_sets()
            version_set.click()
            time.sleep(2)
            version_options = get_options_for_select(wait_version_select)
            version_folder = version_options[j].text.strip()
            version_options[j].click()

            # Bay
            bay_options, wait_bay_select = get_options(bay_set)
            for k in range(len(bay_options)):
                scroll(bay_set, 5)
                wait_for_search_sets()
                bay_set.click()
                time.sleep(2)
                bay_options = get_options_for_select(wait_bay_select)
                bay_folder = bay_options[k].text.strip()
                bay_options[k].click()

                # Model
                model_options, wait_model_select = get_options(model_set)
                for n in range(len(model_options)):
                    scroll(model_set, 5)
                    model_set.click()
                    time.sleep(2)
                    model_options = get_options_for_select(wait_model_select)
                    model_folder = model_options[n].text.strip()
                    model_options[n].click()

                    # 遍历下载列表并下载
                    # 等待item-container中的所有li元素加载完成
                    wait_for_items = WebDriverWait(driver, 10)
                    items = wait_for_items.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.items-container li')))
                    for item in items:
                        arrow = item.find_element(By.CSS_SELECTOR, 'div.arrow')
                        # 滚动到arrow元素可见
                        try:
                            scroll(arrow, 2)
                            wait_arrow = WebDriverWait(driver, 20)
                        except Exception as e:
                            print('failed:  ' + item.text.strip())
                            print(e)
                            click_close_button()
                            continue
                        try:
                            wait_arrow.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.arrow')))
                            wait_arrow.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.arrow')))
                        except Exception as e:
                            print('failed:  ' + item.text.strip())
                            print(e)
                            click_close_button()
                            continue
                        driver.execute_script("arguments[0].click();", arrow)
                        # 等待页面加载
                        wait_for_button_container = WebDriverWait(driver, 10)
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
                            folder_name = (f"{download_path}/{product_folder}"
                                           f"/{version_folder}"
                                           f"/{bay_folder}"
                                           f"/{model_folder}")
                            os.makedirs(folder_name, exist_ok=True)
                            file_name = download_url.split('/')[-1]
                            local_file_path = os.path.join(folder_name, file_name)

                            if not file_name_exists(file_name, download_path):
                                download_file(download_url, local_file_path)
                                save_file_name(file_name, download_path)
                            else:
                                print(f"文件名 {file_name} 已存在，跳过下载。")

                        else:
                            print("Download link not found.")
                        click_close_button()

    driver.quit()
