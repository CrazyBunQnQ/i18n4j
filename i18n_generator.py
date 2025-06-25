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
import argparse
import signal
import sys
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

def translate_text(source_text: str, target_language: str = 'en') -> str:
    """
    使用AI模型翻译文本到目标语言
    
    Args:
        source_text: 源文本
        target_language: 目标语言代码 (如: en, fr, de, ja, ko 等)
        
    Returns:
        str: 翻译结果
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
        
        # 语言映射
        language_names = {
            'en': '英文',
            'fr': '法文', 
            'de': '德文',
            'ja': '日文',
            'ko': '韩文',
            'es': '西班牙文',
            'it': '意大利文',
            'pt': '葡萄牙文',
            'ru': '俄文',
            'ar': '阿拉伯文'
        }
        
        target_lang_name = language_names.get(target_language, f'{target_language}语')
        
        # 构建提示词
        prompt = f"""请将以下文本翻译成{target_lang_name}，要求：
1. 翻译要准确、自然
2. 适合用于软件界面的国际化
3. 只返回翻译结果，不要其他内容

原文：{source_text}
{target_lang_name}翻译："""
        
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
            
            print(f"AI翻译: {source_text} -> {translation}")
            return translation
        else:
            print(f"API请求失败: {response.status_code} - {response.text}")
            return source_text
            
    except Exception as e:
        print(f"翻译API调用出错: {e}")
        return source_text

# 全局变量用于保存状态
current_target_file = None
current_properties = []
save_batch_size = 100

def save_properties_to_file(target_file: str, properties: List[Tuple[str, str]]) -> None:
    """
    保存配置项到文件
    
    Args:
        target_file: 目标文件路径
        properties: 配置项列表
    """
    if not properties:
        return
        
    with open(target_file, 'w', encoding='utf-8') as f:
        for key, value in properties:
            f.write(f"{key}={value}\n")
    
    print(f"已保存 {len(properties)} 个配置项到: {target_file}")

def signal_handler(signum, frame):
    """
    信号处理函数，用于处理用户中断
    """
    print("\n检测到用户中断，正在保存当前进度...")
    if current_target_file and current_properties:
        save_properties_to_file(current_target_file, current_properties)
        print("进度已保存，程序退出")
    sys.exit(0)

def generate_language_properties(source_file: str, target_file: str, target_language: str) -> None:
    """
    根据源配置文件生成目标语言配置文件
    
    Args:
        source_file: 源配置文件路径
        target_file: 目标配置文件路径
        target_language: 目标语言代码
    """
    global current_target_file, current_properties
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"正在处理源配置文件: {source_file}")
    
    # 解析源配置文件
    source_properties = parse_properties_file(source_file)
    if not source_properties:
        print("错误: 源配置文件为空或不存在")
        return
        
    print(f"找到 {len(source_properties)} 个配置项")
    
    # 解析现有的目标语言配置文件
    existing_target_properties = {}
    if os.path.exists(target_file):
        print(f"发现现有目标配置文件: {target_file}")
        target_props = parse_properties_file(target_file)
        existing_target_properties = {key: value for key, value in target_props}
        print(f"现有目标配置项: {len(existing_target_properties)} 个")
    
    # 设置全局变量
    current_target_file = target_file
    current_properties = []
    
    # 生成新的目标语言配置文件内容
    new_target_properties = []
    added_count = 0
    processed_count = 0
    
    try:
        for key, source_value in source_properties:
            if key in existing_target_properties:
                # 使用现有的翻译
                target_value = existing_target_properties[key]
                print(f"保留现有翻译: {key} = {target_value}")
            else:
                # 生成新的翻译
                target_value = translate_text(source_value, target_language)
                print(f"新增翻译: {key} = {target_value}")
                added_count += 1
                
            new_target_properties.append((key, target_value))
            current_properties = new_target_properties.copy()
            processed_count += 1
            
            # 每100条保存一次
            if processed_count % save_batch_size == 0:
                save_properties_to_file(target_file, new_target_properties)
                print(f"批量保存完成，已处理 {processed_count}/{len(source_properties)} 个配置项")
        
        # 最终保存
        save_properties_to_file(target_file, new_target_properties)
        
        print(f"\n生成完成!")
        print(f"总配置项: {len(new_target_properties)}")
        print(f"新增配置项: {added_count}")
        print(f"目标配置文件已保存到: {target_file}")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        # 出错时也保存当前进度
        if current_properties:
            print("正在保存当前进度...")
            save_properties_to_file(target_file, current_properties)
        raise
    finally:
        # 清理全局变量
        current_target_file = None
        current_properties = []

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description='Java i18n 多语言配置文件生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例用法:
  %(prog)s                                    # 使用默认参数
  %(prog)s -s config.properties               # 指定源文件
  %(prog)s -l en fr de                        # 生成英文、法文、德文配置
  %(prog)s -s app.properties -l en ja ko      # 指定源文件并生成多语言配置
        """
    )
    
    parser.add_argument(
        '-s', '--source',
        default='messages.properties',
        help='源配置文件路径 (默认: messages.properties)'
    )
    
    parser.add_argument(
        '-l', '--languages',
        nargs='+',
        default=['en', 'ja'],
        help='目标语言列表 (默认: en)，支持: en, fr, de, ja, ko, es, it, pt, ru, ar 等'
    )
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    args = parse_arguments()
    
    print("Java i18n 多语言配置文件生成器")
    print("=" * 50)
    print(f"源文件: {args.source}")
    print(f"目标语言: {', '.join(args.languages)}")
    print("=" * 50)
    
    # 检查源文件是否存在
    if not os.path.exists(args.source):
        print(f"错误: 源文件 '{args.source}' 不存在")
        return 1
    
    # 获取源文件的目录和基础名称
    source_dir = os.path.dirname(args.source)
    source_name = os.path.basename(args.source)
    
    # 移除扩展名
    if source_name.endswith('.properties'):
        base_name = source_name[:-11]  # 移除 '.properties'
    else:
        base_name = source_name
    
    success_count = 0
    total_count = len(args.languages)
    
    try:
        for language in args.languages:
            print(f"\n正在生成 {language} 语言配置...")
            
            # 构建目标文件路径
            target_filename = f"{base_name}_{language}.properties"
            if source_dir:
                target_file = os.path.join(source_dir, target_filename)
            else:
                target_file = target_filename
            
            try:
                generate_language_properties(args.source, target_file, language)
                success_count += 1
            except Exception as e:
                print(f"生成 {language} 配置时出错: {e}")
                
        print(f"\n=" * 50)
        print(f"任务完成! 成功生成 {success_count}/{total_count} 个语言配置文件")
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        return 1
        
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    exit(main())