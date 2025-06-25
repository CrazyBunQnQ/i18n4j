#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除多语言配置文件中包含占位符的键值对

该脚本读取主配置文件(messages.properties)中包含占位符的键名，
然后在其他多语言配置文件中删除这些键值对。
"""

import os
import re
from typing import List, Set

def find_placeholder_keys(properties_file: str) -> Set[str]:
    """
    从properties文件中找出包含占位符的键名
    
    Args:
        properties_file: properties文件路径
        
    Returns:
        包含占位符的键名集合
    """
    placeholder_keys = set()
    
    try:
        with open(properties_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                    
                # 查找键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 检查值中是否包含占位符 {数字} 或 {变量名}
                    if re.search(r'\{\w*\d*\w*\}', value):
                        placeholder_keys.add(key)
                        print(f"找到包含占位符的键: {key} = {value}")
                        
    except FileNotFoundError:
        print(f"错误: 文件 {properties_file} 不存在")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        
    return placeholder_keys

def remove_keys_from_file(properties_file: str, keys_to_remove: Set[str]) -> bool:
    """
    从properties文件中删除指定的键值对
    
    Args:
        properties_file: properties文件路径
        keys_to_remove: 要删除的键名集合
        
    Returns:
        是否成功删除
    """
    if not os.path.exists(properties_file):
        print(f"警告: 文件 {properties_file} 不存在，跳过")
        return False
        
    try:
        # 读取原文件内容
        with open(properties_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 过滤掉要删除的键值对
        filtered_lines = []
        removed_count = 0
        
        for line in lines:
            original_line = line
            line_stripped = line.strip()
            
            # 跳过空行和注释行
            if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('!'):
                filtered_lines.append(original_line)
                continue
                
            # 检查是否是要删除的键
            if '=' in line_stripped:
                key = line_stripped.split('=', 1)[0].strip()
                if key in keys_to_remove:
                    print(f"从 {properties_file} 中删除键: {key}")
                    removed_count += 1
                    continue
                    
            filtered_lines.append(original_line)
            
        # 写回文件
        with open(properties_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_lines)
            
        print(f"从 {properties_file} 中删除了 {removed_count} 个键值对")
        return True
        
    except Exception as e:
        print(f"处理文件 {properties_file} 时出错: {e}")
        return False

def main():
    """
    主函数
    """
    # 主配置文件路径
    main_properties = "d:/Documents/MEGA/Scripts/python/i18n4j/messages.properties"
    
    # 其他语言配置文件
    other_properties_files = [
        "d:/Documents/MEGA/Scripts/python/i18n4j/messages_en.properties",
        "d:/Documents/MEGA/Scripts/python/i18n4j/messages_ja.properties"
    ]
    
    print("开始处理多语言配置文件...")
    print(f"主配置文件: {main_properties}")
    
    # 1. 从主配置文件中找出包含占位符的键名
    placeholder_keys = find_placeholder_keys(main_properties)
    
    if not placeholder_keys:
        print("未找到包含占位符的键，无需处理")
        return
        
    print(f"\n找到 {len(placeholder_keys)} 个包含占位符的键:")
    for key in sorted(placeholder_keys):
        print(f"  - {key}")
        
    # 2. 从其他语言配置文件中删除这些键值对
    print("\n开始从其他语言配置文件中删除这些键值对...")
    
    success_count = 0
    for properties_file in other_properties_files:
        print(f"\n处理文件: {properties_file}")
        if remove_keys_from_file(properties_file, placeholder_keys):
            success_count += 1
            
    print(f"\n处理完成！成功处理了 {success_count}/{len(other_properties_files)} 个文件")

if __name__ == "__main__":
    main()