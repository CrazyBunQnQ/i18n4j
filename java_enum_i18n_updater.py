#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java枚举类国际化key添加工具

该脚本用于读取Java枚举类文件，提取每个枚举项的name值，
从messages.properties文件中查找对应的key，
并将找到的key添加到Java枚举项中。

使用方法:
1. 修改下面的文件路径
2. 运行脚本
"""

import re
import os
from typing import Dict, List, Tuple, Optional

# 配置文件路径 - 请根据实际情况修改
JAVA_ENUM_FILE = r"E:\LaProjects\2.15\Singularity\Common\dev\common\common-facade\src\main\java\com\icssla\cloud\facade\log\base\Dictionary.java"
MESSAGES_PROPERTIES_FILE = r"E:\LaProjects\2.15\Singularity\Common\dev\common\common-base\src\main\resources\messages.properties"

def read_properties_file(file_path: str) -> Dict[str, str]:
    """
    读取properties文件，返回key-value字典
    """
    properties = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                
                # 查找等号分隔符
                if '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
                    
    except FileNotFoundError:
        print(f"错误: 找不到properties文件: {file_path}")
        return {}
    except Exception as e:
        print(f"读取properties文件时出错: {e}")
        return {}
    
    return properties

def extract_enum_items(java_content: str) -> List[Tuple[str, str, int, int]]:
    """
    从Java枚举类内容中提取枚举项信息
    返回: [(枚举名, name值, 开始位置, 结束位置), ...]
    """
    enum_items = []
    
    # 匹配枚举项的正则表达式
    # 匹配格式: ENUM_NAME("name_value", ...)
    pattern = r'(\w+)\s*\(\s*"([^"]+)"[^)]*\)'
    
    for match in re.finditer(pattern, java_content):
        enum_name = match.group(1)
        name_value = match.group(2)
        start_pos = match.start()
        end_pos = match.end()
        
        # 过滤掉可能的方法调用等非枚举项
        if enum_name.isupper() or enum_name[0].isupper():
            enum_items.append((enum_name, name_value, start_pos, end_pos))
    
    return enum_items

def find_matching_keys(name_value: str, properties: Dict[str, str]) -> List[str]:
    """
    在properties中查找与name值匹配的key
    """
    matching_keys = []
    
    # 直接匹配value
    for key, value in properties.items():
        if value == name_value:
            matching_keys.append(key)
    
    return matching_keys

def update_java_enum_content(java_content: str, enum_items: List[Tuple[str, str, int, int]], 
                           properties: Dict[str, str]) -> Tuple[str, int]:
    """
    更新Java枚举类内容，添加国际化key
    返回: (更新后的内容, 更新数量)
    """
    updated_content = java_content
    update_count = 0
    offset = 0  # 用于跟踪由于插入内容导致的位置偏移
    
    for enum_name, name_value, start_pos, end_pos in enum_items:
        matching_keys = find_matching_keys(name_value, properties)
        
        if matching_keys:
            # 使用第一个匹配的key
            key_to_add = matching_keys[0]
            
            # 调整位置（考虑之前的插入导致的偏移）
            adjusted_start = start_pos + offset
            adjusted_end = end_pos + offset
            
            # 获取原始枚举项内容
            original_enum_item = updated_content[adjusted_start:adjusted_end]
            
            # 查找第一个引号后的位置来插入key
            first_quote_end = original_enum_item.find('"') + 1
            second_quote_start = original_enum_item.find('"', first_quote_end)
            
            if first_quote_end > 0 and second_quote_start > first_quote_end:
                # 构建新的枚举项内容
                new_enum_item = (
                    original_enum_item[:second_quote_start] + 
                    '", "' + key_to_add + 
                    original_enum_item[second_quote_start:]
                )
                
                # 替换内容
                updated_content = (
                    updated_content[:adjusted_start] + 
                    new_enum_item + 
                    updated_content[adjusted_end:]
                )
                
                # 更新偏移量
                offset += len(new_enum_item) - len(original_enum_item)
                update_count += 1
                
                print(f"✓ 更新枚举项 {enum_name}: 添加key '{key_to_add}'")
            else:
                print(f"⚠ 跳过枚举项 {enum_name}: 无法解析引号结构")
        else:
            print(f"- 枚举项 {enum_name} ('{name_value}'): 未找到匹配的key")
    
    return updated_content, update_count

def backup_file(file_path: str) -> str:
    """
    创建文件备份
    """
    backup_path = file_path + '.backup'
    counter = 1
    
    # 如果备份文件已存在，添加数字后缀
    while os.path.exists(backup_path):
        backup_path = f"{file_path}.backup.{counter}"
        counter += 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"✓ 已创建备份文件: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"创建备份文件失败: {e}")
        return ""

def main():
    """
    主函数
    """
    print("Java枚举类国际化key添加工具")
    print("=" * 50)
    
    # 检查文件是否存在
    if not os.path.exists(JAVA_ENUM_FILE):
        print(f"错误: Java枚举文件不存在: {JAVA_ENUM_FILE}")
        print("请修改脚本中的 JAVA_ENUM_FILE 路径")
        return
    
    if not os.path.exists(MESSAGES_PROPERTIES_FILE):
        print(f"错误: Properties文件不存在: {MESSAGES_PROPERTIES_FILE}")
        print("请修改脚本中的 MESSAGES_PROPERTIES_FILE 路径")
        return
    
    # 读取properties文件
    print(f"读取properties文件: {MESSAGES_PROPERTIES_FILE}")
    properties = read_properties_file(MESSAGES_PROPERTIES_FILE)
    print(f"✓ 加载了 {len(properties)} 个properties条目")
    
    # 读取Java枚举文件
    print(f"\n读取Java枚举文件: {JAVA_ENUM_FILE}")
    try:
        with open(JAVA_ENUM_FILE, 'r', encoding='utf-8') as f:
            java_content = f.read()
    except Exception as e:
        print(f"读取Java文件失败: {e}")
        return
    
    # 提取枚举项
    enum_items = extract_enum_items(java_content)
    print(f"✓ 找到 {len(enum_items)} 个枚举项")
    
    if not enum_items:
        print("未找到任何枚举项，请检查Java文件格式")
        return
    
    # 显示找到的枚举项
    print("\n找到的枚举项:")
    for enum_name, name_value, _, _ in enum_items:
        print(f"  - {enum_name}: '{name_value}'")
    
    # 更新Java内容
    print("\n开始处理枚举项...")
    updated_content, update_count = update_java_enum_content(java_content, enum_items, properties)
    
    if update_count > 0:
        # 创建备份
        backup_path = backup_file(JAVA_ENUM_FILE)
        
        if backup_path:
            # 写入更新后的内容
            try:
                with open(JAVA_ENUM_FILE, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"\n✓ 成功更新Java文件")
                print(f"✓ 共更新了 {update_count} 个枚举项")
                print(f"✓ 原文件已备份为: {backup_path}")
            except Exception as e:
                print(f"\n写入文件失败: {e}")
        else:
            print("\n由于备份失败，跳过文件更新")
    else:
        print("\n没有需要更新的枚举项")
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()