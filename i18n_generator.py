#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java i18n 多语言配置文件生成器
根据中文配置文件生成对应的英文配置文件，保持顺序一致
使用OpenAI格式的API调用gemma3:12b模型进行翻译
"""

import os
import re
import json
import requests
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取API配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE_URL = os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com')
MODEL_NAME = 'gemma3:12b'



def parse_properties_file(file_path: str) -> List[Tuple[str, str]]:
    """
    解析properties文件，返回键值对列表，保持原始顺序
    
    Args:
        file_path: properties文件路径
        
    Returns:
        List[Tuple[str, str]]: 键值对列表
    """
    properties = []
    
    if not os.path.exists(file_path):
        return properties
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # 跳过空行和注释行
            if not line or line.startswith('#') or line.startswith('!'):
                continue
                
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                properties.append((key.strip(), value.strip()))
            else:
                print(f"警告: 第{line_num}行格式不正确: {line}")
                
    return properties

def translate_text(chinese_text: str) -> str:
    """
    使用AI模型翻译中文文本为英文
    
    Args:
        chinese_text: 中文文本
        
    Returns:
        str: 英文翻译
    """
    if not OPENAI_API_KEY:
        print("错误: 未设置OPENAI_API_KEY，无法进行翻译")
        return chinese_text
    
    try:
        # 构建API请求
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 构建提示词
        prompt = f"""请将以下中文文本翻译成英文，要求：
1. 翻译要准确、自然
2. 适合用于软件界面的国际化
3. 只返回翻译结果，不要其他内容

中文文本：{chinese_text}
英文翻译："""
        
        data = {
            'model': MODEL_NAME,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 100
        }
        
        # 发送API请求
        api_url = f"{OPENAI_API_BASE_URL.rstrip('/')}/v1/chat/completions"
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            translation = result['choices'][0]['message']['content'].strip()
            
            # 清理翻译结果，移除可能的前缀
            if translation.startswith('英文翻译：'):
                translation = translation[5:].strip()
            elif translation.startswith('Translation:'):
                translation = translation[12:].strip()
            
            print(f"AI翻译: {chinese_text} -> {translation}")
            return translation
        else:
            print(f"API请求失败: {response.status_code} - {response.text}")
            return chinese_text
            
    except Exception as e:
        print(f"翻译API调用出错: {e}")
        return chinese_text

def generate_english_properties(chinese_file: str, english_file: str) -> None:
    """
    根据中文配置文件生成英文配置文件
    
    Args:
        chinese_file: 中文配置文件路径
        english_file: 英文配置文件路径
    """
    print(f"正在处理中文配置文件: {chinese_file}")
    
    # 解析中文配置文件
    chinese_properties = parse_properties_file(chinese_file)
    if not chinese_properties:
        print("错误: 中文配置文件为空或不存在")
        return
        
    print(f"找到 {len(chinese_properties)} 个中文配置项")
    
    # 解析现有的英文配置文件
    existing_english_properties = {}
    if os.path.exists(english_file):
        print(f"发现现有英文配置文件: {english_file}")
        english_props = parse_properties_file(english_file)
        existing_english_properties = {key: value for key, value in english_props}
        print(f"现有英文配置项: {len(existing_english_properties)} 个")
    
    # 生成新的英文配置文件内容
    new_english_properties = []
    added_count = 0
    
    for key, chinese_value in chinese_properties:
        if key in existing_english_properties:
            # 使用现有的英文翻译
            english_value = existing_english_properties[key]
            print(f"保留现有翻译: {key} = {english_value}")
        else:
            # 生成新的英文翻译
            english_value = translate_text(chinese_value)
            print(f"新增翻译: {key} = {english_value}")
            added_count += 1
            
        new_english_properties.append((key, english_value))
    
    # 写入英文配置文件
    with open(english_file, 'w', encoding='utf-8') as f:
        for key, value in new_english_properties:
            f.write(f"{key}={value}\n")
    
    print(f"\n生成完成!")
    print(f"总配置项: {len(new_english_properties)}")
    print(f"新增配置项: {added_count}")
    print(f"英文配置文件已保存到: {english_file}")

def main():
    """
    主函数
    """
    # 配置文件路径
    chinese_file = "d:/Documents/MEGA/Scripts/python/i18n4j/test_messages.properties"
    english_file = "d:/Documents/MEGA/Scripts/python/i18n4j/test_messages_en.properties"
    
    print("Java i18n 多语言配置文件生成器")
    print("=" * 50)
    
    try:
        generate_english_properties(chinese_file, english_file)
    except Exception as e:
        print(f"错误: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())