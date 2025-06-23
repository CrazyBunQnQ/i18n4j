#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java Spring Boot项目国际化字符串提取工具
功能：
1. 扫描Java项目源码，提取硬编码字符串
2. 去重并生成键值对
3. 合并到指定的多语言配置文件中
"""

import os
import re
import argparse
import hashlib
from pathlib import Path
from typing import Set, Dict, List
import configparser

class JavaStringExtractor:
    def __init__(self):
        # 匹配Java字符串的正则表达式
        # 匹配双引号字符串，排除转义字符
        self.string_pattern = re.compile(r'"([^"\\]*(\\.[^"\\]*)*)"')
        # 匹配单行注释
        self.single_comment_pattern = re.compile(r'//.*$', re.MULTILINE)
        # 匹配多行注释
        self.multi_comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
        # 匹配注解
        self.annotation_pattern = re.compile(r'@\w+\s*\([^)]*\)', re.MULTILINE)
        
        # 需要排除的字符串模式
        self.exclude_patterns = [
            r'^\s*$',  # 空字符串或只有空白字符
            r'^[a-zA-Z_][a-zA-Z0-9_.]*$',  # 变量名、类名等标识符
            r'^\d+$',  # 纯数字
            r'^[\w.]+\.[a-zA-Z]+$',  # 文件名或包名
            r'^[A-Z_]+$',  # 常量名
            r'^\s*[{}\[\](),;]+\s*$',  # 只包含符号
            r'^(true|false|null)$',  # Java关键字
            r'^\s*[+\-*/=<>!&|]+\s*$',  # 操作符
        ]
        
    def remove_comments(self, content: str) -> str:
        """移除Java代码中的注释"""
        # 移除多行注释
        content = self.multi_comment_pattern.sub('', content)
        # 移除单行注释
        content = self.single_comment_pattern.sub('', content)
        # 移除注解
        content = self.annotation_pattern.sub('', content)
        return content
    
    def is_valid_string(self, string_value: str) -> bool:
        """判断字符串是否应该被提取"""
        if not string_value or len(string_value.strip()) < 2:
            return False
            
        # 检查排除模式
        for pattern in self.exclude_patterns:
            if re.match(pattern, string_value.strip()):
                return False
                
        return True
    
    def extract_strings_from_file(self, file_path: Path) -> Set[str]:
        """从单个Java文件中提取字符串"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                print(f"警告: 无法读取文件 {file_path}")
                return set()
        except Exception as e:
            print(f"错误: 读取文件 {file_path} 时出错: {e}")
            return set()
        
        # 移除注释
        content = self.remove_comments(content)
        
        # 提取字符串
        strings = set()
        matches = self.string_pattern.findall(content)
        
        for match in matches:
            # match[0] 是完整的字符串内容
            string_value = match[0]
            if self.is_valid_string(string_value):
                strings.add(string_value)
                
        return strings
    
    def scan_project(self, project_path: Path) -> Set[str]:
        """扫描整个Java项目"""
        all_strings = set()
        java_files = list(project_path.rglob('*.java'))
        
        print(f"找到 {len(java_files)} 个Java文件")
        
        for java_file in java_files:
            print(f"正在处理: {java_file}")
            file_strings = self.extract_strings_from_file(java_file)
            all_strings.update(file_strings)
            
        return all_strings
    
    def generate_key(self, string_value: str) -> str:
        """为字符串生成键"""
        # 清理字符串，移除特殊字符
        cleaned = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '_', string_value)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        
        # 如果清理后的字符串太短，使用哈希值
        if len(cleaned) < 3:
            hash_value = hashlib.md5(string_value.encode('utf-8')).hexdigest()[:8]
            return f"str_{hash_value}"
        
        # 限制长度
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "_" + hashlib.md5(string_value.encode('utf-8')).hexdigest()[:3]
            
        return cleaned.lower()
    
    def load_existing_config(self, config_path: Path) -> Dict[str, str]:
        """加载现有的配置文件"""
        config = {}
        
        if not config_path.exists():
            return config
            
        try:
            if config_path.suffix.lower() == '.properties':
                # Java properties文件格式
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            else:
                # 尝试作为INI文件处理
                parser = configparser.ConfigParser()
                parser.read(config_path, encoding='utf-8')
                for section in parser.sections():
                    for key, value in parser.items(section):
                        config[f"{section}.{key}"] = value
        except Exception as e:
            print(f"警告: 读取配置文件时出错: {e}")
            
        return config
    
    def save_config(self, config_path: Path, config: Dict[str, str]):
        """保存配置文件"""
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if config_path.suffix.lower() == '.properties':
                # Java properties文件格式
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write("# 自动生成的国际化配置文件\n")
                    f.write("# Auto-generated i18n configuration file\n\n")
                    for key, value in sorted(config.items()):
                        f.write(f"{key}={value}\n")
            else:
                # INI文件格式
                parser = configparser.ConfigParser()
                parser['DEFAULT'] = config
                with open(config_path, 'w', encoding='utf-8') as f:
                    parser.write(f)
        except Exception as e:
            print(f"错误: 保存配置文件时出错: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Java Spring Boot项目国际化字符串提取工具')
    parser.add_argument('project_dir', help='Java项目目录路径')
    parser.add_argument('config_file', help='多语言配置文件路径')
    parser.add_argument('--encoding', default='utf-8', help='文件编码 (默认: utf-8)')
    
    args = parser.parse_args()
    
    project_path = Path(args.project_dir)
    config_path = Path(args.config_file)
    
    if not project_path.exists():
        print(f"错误: 项目目录不存在: {project_path}")
        return 1
        
    if not project_path.is_dir():
        print(f"错误: 指定的路径不是目录: {project_path}")
        return 1
    
    # 检查是否是Maven项目
    pom_file = project_path / 'pom.xml'
    if not pom_file.exists():
        print(f"警告: 在项目目录中未找到pom.xml文件，可能不是Maven项目")
    
    extractor = JavaStringExtractor()
    
    print("开始扫描Java项目...")
    extracted_strings = extractor.scan_project(project_path)
    
    print(f"\n提取到 {len(extracted_strings)} 个唯一字符串")
    
    # 加载现有配置
    existing_config = extractor.load_existing_config(config_path)
    print(f"现有配置文件包含 {len(existing_config)} 个条目")
    
    # 生成新的键值对
    new_entries = 0
    for string_value in extracted_strings:
        key = extractor.generate_key(string_value)
        
        # 避免键冲突
        original_key = key
        counter = 1
        while key in existing_config and existing_config[key] != string_value:
            key = f"{original_key}_{counter}"
            counter += 1
        
        if key not in existing_config:
            existing_config[key] = string_value
            new_entries += 1
            print(f"新增: {key} = {string_value}")
    
    # 保存配置文件
    extractor.save_config(config_path, existing_config)
    
    print(f"\n完成! 新增了 {new_entries} 个条目")
    print(f"配置文件已保存到: {config_path}")
    print(f"总计 {len(existing_config)} 个配置项")
    
    return 0

if __name__ == '__main__':
    exit(main())