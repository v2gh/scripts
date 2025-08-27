#!/usr/bin/env python
"""
json_excel_sync.py
当只有JSON文件存在时，自动创建对应的Excel文件
当只有Excel文件存在时，自动创建对应的JSON文件
可选的同步方向控制（双向/单向）
自动保持文件时间戳同步
"""

import os
import json
import time
import argparse
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class JsonExcelSyncHandler(FileSystemEventHandler):
    def __init__(self, directory, sync_direction="both"):
        self.directory = directory
        self.sync_direction = sync_direction
        self.last_modified = time.time()

    def on_modified(self, event):
        # 防止重复触发
        if time.time() - self.last_modified < 1:
            return

        # 获取文件扩展名
        file_ext = os.path.splitext(event.src_path)[1].lower()

        if file_ext not in ['.json', '.xlsx']:
            return

        self.last_modified = time.time()

        try:
            if file_ext == '.json':
                json_path = event.src_path
                excel_path = os.path.splitext(json_path)[0] + '.xlsx'

                if self.sync_direction in ["both", "json2excel"]:
                    print(f"\n检测到 {json_path} 被修改，正在同步到Excel...")
                    json_to_excel(json_path, excel_path)
                    json_mtime = os.path.getmtime(json_path)
                    os.utime(excel_path, (json_mtime, json_mtime))
                    print("同步完成!")

            elif file_ext == '.xlsx':
                excel_path = event.src_path
                json_path = os.path.splitext(excel_path)[0] + '.json'

                if self.sync_direction in ["both", "excel2json"]:
                    print(f"\n检测到 {excel_path} 被修改，正在同步到JSON...")
                    excel_to_json(excel_path, json_path)
                    excel_mtime = os.path.getmtime(excel_path)
                    os.utime(json_path, (excel_mtime, excel_mtime))
                    print("同步完成!")

        except Exception as e:
            print(f"同步过程中出错: {str(e)}")

def json_to_excel(json_file_path, excel_file_path=None, sheet_name='Sheet1'):
    """
    将 JSON 文件转换为 Excel 文件。

    参数:
    json_file_path (str): 输入的 JSON 文件路径。
    excel_file_path (str, optional): 输出的 Excel 文件路径。如果为 None，则使用 JSON 文件名并替换扩展名为 .xlsx。
    sheet_name (str): Excel 工作表的名称。
    """
    # 检查输入文件是否存在
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON 文件未找到: {json_file_path}")

    try:
        # 读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功读取 JSON 文件: {json_file_path}")

        # 将 JSON 数据转换为 pandas DataFrame
        # 假设 JSON 结构是列表 of 字典 (对应 orient='records')
        df = pd.json_normalize(data) # json_normalize 可以处理嵌套结构
        # 或者直接: df = pd.DataFrame(data) # 如果结构简单

        # 确定输出文件路径
        if excel_file_path is None:
            base_name = os.path.splitext(json_file_path)[0]
            excel_file_path = base_name + '.xlsx'

        # 写入 Excel 文件
        df.to_excel(excel_file_path, sheet_name=sheet_name, index=False, engine='openpyxl')
        print(f"成功将 JSON 转换为 Excel: {excel_file_path}")
        return excel_file_path

    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        return None

def excel_to_json(excel_file_path, json_file_path=None, sheet_name=0, orient='records', indent=4):
    """
    将 Excel 文件转换为 JSON 文件。

    参数:
    excel_file_path (str): 输入的 Excel 文件路径。
    json_file_path (str, optional): 输出的 JSON 文件路径。如果为 None，则使用 Excel 文件名并替换扩展名为 .json。
    sheet_name (str, int, list, optional): 要读取的工作表名称或索引。默认为 0 (第一个工作表)。
    orient (str): JSON 输出格式。常用 'records' (列表 of 字典), 'split', 'index', 'columns', 'values', 'table'。
    indent (int): JSON 缩进空格数，用于美化输出。
    """
    # 检查输入文件是否存在
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"Excel 文件未找到: {excel_file_path}")

    try:
        # 读取 Excel 文件
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"成功读取 Excel 文件: {excel_file_path}")

        # 如果 sheet_name 是列表，df 会是一个字典，这里我们只处理单个 sheet 的情况
        if isinstance(df, dict):
            # 如果指定了多个 sheet，可以选择处理第一个或合并
            # 这里简单处理：取第一个 sheet 的数据
            sheet_names = list(df.keys())
            df = df[sheet_names[0]]
            print(f"注意: 指定了多个工作表，将使用第一个工作表 '{sheet_names[0]}' 的数据进行转换。")

        # 处理 NaN 值 (将 NaN 转换为 None，以便 JSON 序列化)
        df = df.where(pd.notnull(df), None)

        # 转换为 JSON 字符串
        json_str = df.to_json(orient=orient, indent=indent, force_ascii=False, date_format='iso')

        # 确定输出文件路径
        if json_file_path is None:
            base_name = os.path.splitext(excel_file_path)[0]
            json_file_path = base_name + '.json'

        # 写入 JSON 文件
        with open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

        print(f"成功将 Excel 转换为 JSON: {json_file_path}")
        return json_file_path

    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        return None

def ensure_file_pairs(directory):
    """确保每个JSON/Excel文件都有对应的配对文件"""
    created_files = []

    # 扫描目录下的所有文件
    for filename in os.listdir(directory):
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()
        full_path = os.path.join(directory, filename)

        if ext == '.json':
            excel_path = os.path.join(directory, base_name + '.xlsx')
            if not os.path.exists(excel_path):
                print(f"创建Excel文件: {excel_path}")
                json_to_excel(full_path, excel_path)
                json_mtime = os.path.getmtime(full_path)
                os.utime(excel_path, (json_mtime, json_mtime))
                created_files.append(excel_path)

        elif ext == '.xlsx':
            json_path = os.path.join(directory, base_name + '.json')
            if not os.path.exists(json_path):
                print(f"创建JSON文件: {json_path}")
                excel_to_json(full_path, json_path)
                excel_mtime = os.path.getmtime(full_path)
                os.utime(json_path, (excel_mtime, excel_mtime))
                created_files.append(json_path)

    return len(created_files)

def initial_sync(directory, sync_direction):
    """初始同步检查"""
    file_pairs = []

    # 首先确保所有文件都有对应的配对文件
    created_count = ensure_file_pairs(directory)
    if created_count > 0:
        print(f"已创建 {created_count} 个配对文件")

    # 收集所有有效的文件对
    for filename in os.listdir(directory):
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext == '.json':
            json_path = os.path.join(directory, filename)
            excel_path = os.path.join(directory, base_name + '.xlsx')

            if os.path.exists(excel_path):
                file_pairs.append((json_path, excel_path))

        elif ext == '.xlsx':
            excel_path = os.path.join(directory, filename)
            json_path = os.path.join(directory, base_name + '.json')

            if os.path.exists(json_path):
                file_pairs.append((json_path, excel_path))

    # 执行初始同步
    for json_path, excel_path in file_pairs:
        json_mtime = os.path.getmtime(json_path)
        excel_mtime = os.path.getmtime(excel_path)

        if sync_direction == "both":
            if excel_mtime > json_mtime:
                print(f"Excel文件比JSON新，从Excel更新 {json_path}")
                excel_to_json(excel_path, json_path)
                os.utime(json_path, (excel_mtime, excel_mtime))
            elif json_mtime > excel_mtime:
                print(f"JSON文件比Excel新，从JSON更新 {excel_path}")
                json_to_excel(json_path, excel_path)
                os.utime(excel_path, (json_mtime, json_mtime))
        elif sync_direction == "excel2json" and excel_mtime > json_mtime:
            print(f"Excel文件比JSON新，从Excel更新 {json_path}")
            excel_to_json(excel_path, json_path)
            os.utime(json_path, (excel_mtime, excel_mtime))
        elif sync_direction == "json2excel" and json_mtime > excel_mtime:
            print(f"JSON文件比Excel新，从JSON更新 {excel_path}")
            json_to_excel(json_path, excel_path)
            os.utime(excel_path, (json_mtime, json_mtime))

        print(f"文件已同步: {json_path} <-> {excel_path}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="JSON和Excel双向同步工具")
    parser.add_argument("--dir", default=".", help="监控的目录路径（默认当前目录）")
    parser.add_argument("--sync", choices=["both", "excel2json", "json2excel"],
                       default="both", help="同步方向：both(双向), excel2json, json2excel")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    print(f"正在初始化目录 {args.dir}...")
    initial_sync(args.dir, args.sync)

    # 设置监控
    event_handler = JsonExcelSyncHandler(args.dir, args.sync)
    observer = Observer()
    observer.schedule(event_handler, path=args.dir, recursive=False)
    observer.start()

    try:
        print(f"\n开始监控目录: {args.dir}")
        print(f"同步模式: {args.sync}")
        print("按 Ctrl+C 停止监控")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
