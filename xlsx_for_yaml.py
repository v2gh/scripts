# 一个监测脚本，用于yaml和excel互转，当不存在与yaml文件同名的excel文件时自动生成，并将excel的时间改为与yaml一致，当excel的时间比yaml更新，自动刷回
import os
import yaml
import pandas as pd
from datetime import datetime
import time

def yaml_to_excel(yaml_path, excel_path):
    """将 YAML 文件转换为 Excel 文件"""
    with open(yaml_path, 'r', encoding='utf-8') as yaml_file:
        data = yaml.safe_load(yaml_file)

    # 如果数据是列表形式，直接转为 DataFrame
    if isinstance(data, list):
        df = pd.DataFrame(data)
    # 如果是字典，且有多层嵌套，可能需要特殊处理
    elif isinstance(data, dict):
        # 简单处理：将字典转换为列表形式
        df = pd.DataFrame([data])
    else:
        raise ValueError("Unsupported YAML structure")

    df.to_excel(excel_path, index=False)

    # 保持与 YAML 文件相同的时间戳
    yaml_mtime = os.path.getmtime(yaml_path)
    os.utime(excel_path, (yaml_mtime, yaml_mtime))
    print(f"已将 {yaml_path} 转换为 {excel_path}")

def excel_to_yaml(excel_path, yaml_path):
    """将 Excel 文件转换为 YAML 文件"""
    df = pd.read_excel(excel_path)
    data = df.to_dict('records')

    with open(yaml_path, 'w', encoding='utf-8') as yaml_file:
        yaml.dump(data, yaml_file, allow_unicode=True, sort_keys=False)

    # 保持与 Excel 文件相同的时间戳
    excel_mtime = os.path.getmtime(excel_path)
    os.utime(yaml_path, (excel_mtime, excel_mtime))
    print(f"已将 {excel_path} 转换为 {yaml_path}")

def monitor_directory(directory, interval=5):
    """监测目录中的 YAML 和 Excel 文件"""
    while True:
        for filename in os.listdir(directory):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                yaml_path = os.path.join(directory, filename)
                excel_path = os.path.join(directory, os.path.splitext(filename)[0] + '.xlsx')

                # 检查对应的 Excel 文件是否存在
                if not os.path.exists(excel_path):
                    yaml_to_excel(yaml_path, excel_path)
                else:
                    # 比较时间戳
                    yaml_mtime = os.path.getmtime(yaml_path)
                    excel_mtime = os.path.getmtime(excel_path)

                    if yaml_mtime > excel_mtime:
                        # YAML 文件更新，重新生成 Excel
                        yaml_to_excel(yaml_path, excel_path)
                    elif excel_mtime > yaml_mtime:
                        # Excel 文件更新，重新生成 YAML
                        excel_to_yaml(excel_path, yaml_path)

            elif filename.endswith('.xlsx') and not filename.startswith('.~'):
                excel_path = os.path.join(directory, filename)
                yaml_path = os.path.join(directory, os.path.splitext(filename)[0] + '.yaml')

                # 检查对应的 YAML 文件是否存在
                if not os.path.exists(yaml_path):
                    excel_to_yaml(excel_path, yaml_path)

        # 等待指定间隔后再次检查
        time.sleep(interval)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YAML 和 Excel 文件同步监测工具")
    parser.add_argument("directory", help="要监测的目录路径")
    parser.add_argument("--interval", type=int, default=5,
                       help="检查间隔时间（秒），默认为5秒")

    args = parser.parse_args()

    print(f"开始监测目录: {args.directory}，检查间隔: {args.interval}秒")
    try:
        monitor_directory(args.directory, args.interval)
    except KeyboardInterrupt:
        print("\n监测已停止")
