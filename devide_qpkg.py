import re
import sys
import os
import subprocess


def extract_header_script(qpkg_file, target_folder):
    # 确保目标文件夹存在
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 读取qpkg文件内容
    with open(qpkg_file, 'r', errors='ignore') as file:
        content = file.read()

    # 从后往前寻找‘exit 1’，提取header_script.sh
    exit_index = content.rfind('exit 1')
    if exit_index != -1:
        # 包括 'exit 1' 在内的所有内容都是 header_script.sh
        header_script_content = content[:exit_index + 7]
        with open(os.path.join(target_folder, 'header_script.sh'), 'w') as header_script_file:
            header_script_file.write(header_script_content)
    else:
        print("Error: 'exit 1' not found in the qpkg file.")
        sys.exit(1)


def process_and_execute_header_script(qpkg_file, target_folder):
    # 读取header_script.sh
    with open(os.path.join(target_folder, 'header_script.sh'), 'r') as header_script_file:
        header_script_content = header_script_file.read()

    # 获取‘script_len’的开始索引
    script_len_end_index = header_script_content.find('script_len')

    # 获取最后一个‘offset=’的开始索引
    last_offset_start_index = header_script_content.rfind('offset=')

    # 截取‘script_len’及其之后，最后一个‘offset=’之前的内容
    script_content_to_process = header_script_content[script_len_end_index:last_offset_start_index - 1]

    # 替换‘“{0}”‘为qpkg文件路径，$_EXTRACT_DIR为目标文件夹
    processed_content = script_content_to_process.replace('\"${0}\"', qpkg_file).replace('$_EXTRACT_DIR', target_folder)

    # 执行处理后的脚本内容
    execute_script(processed_content)


def execute_script(processed_content):
    # 使用bash执行处理后的脚本内容
    process = subprocess.Popen(['bash', '-c', processed_content], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Error executing script:", stderr.decode())
    else:
        print("Script executed successfully.")
        print(stdout.decode())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_header_script.py <qpkg_file> <target_folder>")
        sys.exit(1)

    qpkg_file = sys.argv[1]
    target_folder = sys.argv[2]

    extract_header_script(qpkg_file, target_folder)
    process_and_execute_header_script(qpkg_file, target_folder)
