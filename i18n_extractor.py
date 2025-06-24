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
import json
from pathlib import Path
from typing import Set, Dict, List, Optional
from collections import OrderedDict
import configparser
import chardet
import requests
from dotenv import load_dotenv

class JavaStringExtractor:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 匹配Java字符串的正则表达式
        # 匹配双引号字符串，排除转义字符
        self.string_pattern = re.compile(r'"([^"\\]*(\\.[^"\\]*)*)"')
        # 匹配单行注释
        self.single_comment_pattern = re.compile(r'//.*$', re.MULTILINE)
        # 匹配多行注释
        self.multi_comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
        # 匹配注解
        self.annotation_pattern = re.compile(r'@\w+\s*\([^)]*\)', re.MULTILINE)
        
        # API配置
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base_url = os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com')
        self.use_ai_key_generation = bool(self.api_key and self.api_base_url)
        
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
    
    def contains_non_english(self, string_value: str) -> bool:
        """检查字符串是否包含非英文字符(包括中文、日文、韩文等以及非英文标点符号)"""
        # 匹配非ASCII字符或非英文标点符号
        non_english_pattern = re.compile(r'[^\x00-\x7F]|[\u2000-\u206F\u2E00-\u2E7F\u3000-\u303F\uFF00-\uFFEF]')
        return bool(non_english_pattern.search(string_value))
    
    def is_valid_string(self, string_value: str) -> bool:
        """判断字符串是否应该被提取"""
        if not string_value or len(string_value.strip()) < 2:
            return False
            
        # 检查排除模式
        for pattern in self.exclude_patterns:
            if re.match(pattern, string_value.strip()):
                return False
        
        # 只提取包含非英文字符的字符串
        if not self.contains_non_english(string_value):
            return False
                
        return True
    
    def detect_encoding(self, file_path: Path) -> str:
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # 如果置信度太低，使用默认编码
                if confidence < 0.7:
                    encoding = 'utf-8'
                    
                return encoding
        except Exception:
            return 'utf-8'
    
    def detect_string_concatenation(self, content: str) -> Dict[str, str]:
        """检测字符串拼接模式并生成带占位符的完整句子"""
        detected_strings = {}
        
        # 处理多行字符串拼接
        self._detect_multiline_concatenation(content, detected_strings)
        
        # 简化的单行拼接模式检测
        concatenation_patterns = [
            # "字符串" + 变量 + "字符串" 模式
            (r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*\+\s*([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))?)\s*\+\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 
             lambda m: f"{m.group(1)}{{}}{m.group(3)}"),
            
            # "字符串" + 变量 模式
            (r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*\+\s*([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))?)', 
             lambda m: f"{m.group(1)}{{}}"),
            
            # 变量 + "字符串" 模式
            (r'([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))?)\s*\+\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 
             lambda m: f"{{}}{m.group(2)}"),
        ]
        
        # 按行处理字符串拼接
        lines = content.split('\n')
        for line in lines:
            # 跳过不包含拼接的行
            if '"' not in line or '+' not in line:
                continue
            
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # 尝试匹配各种拼接模式
            for pattern, formatter in concatenation_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    try:
                        formatted = formatter(match)
                        # 只保留包含非英文字符的拼接
                        if self.contains_non_english(formatted):
                            detected_strings[match.group(0)] = formatted
                    except:
                        continue
        
        # 处理 StringBuilder 和 StringBuffer 拼接
        self._detect_string_builder_patterns(content, detected_strings)
        
        # 处理 String.format 和 MessageFormat.format
        format_patterns = {
            r'String\.format\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"[^)]*\)': r'\1',
            r'MessageFormat\.format\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"[^)]*\)': r'\1',
        }
        
        for pattern, replacement in format_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                original = match.group(0)
                try:
                    formatted = re.sub(pattern, replacement, original)
                    if self.contains_non_english(formatted):
                        detected_strings[original] = formatted
                except:
                    continue
        
        return detected_strings
    
    def _detect_multiline_concatenation(self, content: str, detected_strings: Dict[str, str]):
        """检测跨多行的字符串拼接模式"""
        # 匹配多行字符串拼接模式
        # 例如: "字符串1" +
        #       变量 +
        #       "字符串2"
        multiline_pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*\+\s*(?:\n\s*([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))?)\s*\+\s*)*(?:\n\s*)*"([^"\\]*(?:\\.[^"\\]*)*)"'
        
        # 更复杂的多行拼接检测
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找以字符串开始且以 + 结尾的行
            if '"' in line and line.endswith('+'):
                concatenation_parts = []
                original_lines = []
                
                # 提取第一行的字符串
                string_match = re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
                if string_match:
                    concatenation_parts.append(string_match.group(1))
                    original_lines.append(line)
                    
                    # 继续查找后续行
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                            
                        original_lines.append(next_line)
                        
                        # 检查是否为变量 + 
                        var_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_.]*(?:\([^)]*\))?)\s*\+\s*$', next_line)
                        if var_match:
                            concatenation_parts.append('{}')
                            j += 1
                            continue
                        
                        # 检查是否为字符串（可能是最后一行）
                        string_match = re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', next_line)
                        if string_match:
                            concatenation_parts.append(string_match.group(1))
                            # 检查是否还有 + 继续
                            if not next_line.endswith('+'):
                                # 拼接结束
                                break
                            j += 1
                            continue
                        
                        # 如果不匹配任何模式，结束当前拼接检测
                        break
                    
                    # 如果找到了有效的拼接模式
                    if len(concatenation_parts) > 1:
                        # 合并连续的字符串字面量
                        merged_string = self._merge_concatenation_parts(concatenation_parts)
                        if merged_string and self.contains_non_english(merged_string):
                            original_code = '\n'.join(original_lines)
                            detected_strings[original_code] = merged_string
                    
                    i = j
                else:
                    i += 1
            else:
                i += 1
    
    def _merge_concatenation_parts(self, parts: List[str]) -> str:
        """合并拼接的字符串部分，处理连续的字符串字面量"""
        if not parts:
            return ""
        
        merged_parts = []
        i = 0
        while i < len(parts):
            if parts[i] == '{}':
                merged_parts.append('{}')
                i += 1
            else:
                # 收集连续的字符串字面量
                literal_part = parts[i]
                i += 1
                while i < len(parts) and parts[i] != '{}':
                    literal_part += parts[i]
                    i += 1
                merged_parts.append(literal_part)
        
        return ''.join(merged_parts)
    
    def _detect_string_builder_patterns(self, content: str, detected_strings: Dict[str, str]):
        """检测 StringBuilder 和 StringBuffer 的字符串拼接模式"""
        # 匹配 StringBuilder/StringBuffer 的 append 链式调用
        builder_patterns = [
            # new StringBuilder().append("字符串").append(变量).append("字符串")
            r'new\s+(?:StringBuilder|StringBuffer)\s*\(\s*\)(?:\.append\s*\([^)]+\))+',
            # builder.append("字符串").append(变量).append("字符串")
            r'[a-zA-Z_][a-zA-Z0-9_]*\.append\s*\([^)]+\)(?:\.append\s*\([^)]+\))+',
        ]
        
        for pattern in builder_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                builder_code = match.group(0)
                # 提取所有 append 调用中的字符串
                append_strings = self._extract_append_strings(builder_code)
                if append_strings:
                    # 合并为完整字符串，变量用 {} 替代
                    merged_string = self._merge_append_strings(append_strings)
                    if merged_string and self.contains_non_english(merged_string):
                        detected_strings[builder_code] = merged_string
    
    def _extract_append_strings(self, builder_code: str) -> List[str]:
        """从 StringBuilder/StringBuffer 代码中提取字符串和变量"""
        append_parts = []
        # 匹配 .append(参数) 调用
        append_pattern = r'\.append\s*\(([^)]+)\)'
        matches = re.finditer(append_pattern, builder_code)
        
        for match in matches:
            param = match.group(1).strip()
            # 检查是否为字符串字面量
            if param.startswith('"') and param.endswith('"'):
                # 提取字符串内容（去掉引号）
                string_content = param[1:-1]
                append_parts.append(string_content)
            else:
                # 变量或表达式，用占位符表示
                append_parts.append('{}')
        
        return append_parts
    
    def _merge_append_strings(self, append_parts: List[str]) -> str:
        """合并 append 的字符串部分，生成完整的模板字符串"""
        if not append_parts:
            return ""
        
        # 合并连续的字符串字面量
        merged_parts = []
        i = 0
        while i < len(append_parts):
            if append_parts[i] == '{}':
                merged_parts.append('{}')
                i += 1
            else:
                # 收集连续的字符串字面量
                literal_part = append_parts[i]
                i += 1
                while i < len(append_parts) and append_parts[i] != '{}':
                    literal_part += append_parts[i]
                    i += 1
                merged_parts.append(literal_part)
        
        return ''.join(merged_parts)
    
    def extract_strings_from_file(self, file_path: Path) -> Set[str]:
        """从单个Java文件中提取字符串"""
        # 检测文件编码
        detected_encoding = self.detect_encoding(file_path)
        
        # 尝试多种编码读取文件
        encodings_to_try = [detected_encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                print(f"错误: 读取文件 {file_path} 时出错: {e}")
                return set()
        
        if content is None:
            print(f"警告: 无法读取文件 {file_path}，尝试了多种编码")
            return set()
        
        # 移除注释
        cleaned_content = self.remove_comments(content)
        
        # 检测字符串拼接模式
        concatenated_strings = self.detect_string_concatenation(cleaned_content)
        
        # 从原内容中移除已检测到的拼接模式，避免重复提取
        for original_pattern in concatenated_strings.keys():
            cleaned_content = cleaned_content.replace(original_pattern, '')
        
        # 提取普通字符串
        strings = set()
        matches = self.string_pattern.findall(cleaned_content)
        
        for match in matches:
            # match[0] 是完整的字符串内容
            string_value = match[0]
            if self.is_valid_string(string_value):
                strings.add(string_value)
        
        # 添加检测到的拼接字符串
        for formatted_string in concatenated_strings.values():
            if self.is_valid_string(formatted_string):
                strings.add(formatted_string)
                
        return strings
    
    def scan_project(self, project_path: Path) -> OrderedDict[str, Path]:
        """扫描整个Java项目，返回字符串到文件路径的有序映射"""
        all_strings = OrderedDict()  # 字符串 -> 文件路径的映射
        java_files = list(project_path.rglob('*.java'))
        
        print(f"找到 {len(java_files)} 个Java文件")
        
        for java_file in java_files:
            # print(f"正在处理: {java_file}")
            file_strings = self.extract_strings_from_file(java_file)
            # 按扫描顺序添加字符串，自动去重，保留首次出现的文件路径
            for string_value in file_strings:
                if string_value not in all_strings:
                    all_strings[string_value] = java_file
            
        return all_strings
    
    def find_module_path(self, file_path: Path) -> List[str]:
        """查找文件所属的模块路径，返回模块名列表"""
        modules = []
        current_path = file_path.parent
        
        # 向上查找包含pom.xml的目录
        while current_path.parent != current_path:  # 避免到达根目录
            pom_file = current_path / 'pom.xml'
            if pom_file.exists():
                module_name = current_path.name.lower()
                # 过滤掉临时目录名（通常以tmp开头）和其他无意义的目录名
                if not (module_name.startswith('tmp') or module_name.startswith('temp') or len(module_name) > 20):
                    modules.insert(0, module_name)
            current_path = current_path.parent
            
        return modules
    
    def _generate_ai_key(self, string_value: str) -> str:
        """使用AI生成简短的键名"""
        if not self.use_ai_key_generation:
            return None
            
        try:
            # 构建API请求
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 构建提示词 qwen3 模型需要关闭思考
            # prompt = f"""请为以下中文字符串生成一个简短的英文键名，要求：
            prompt = f"""/no_think 请为以下中文字符串生成一个简短的英文键名，要求：
1. 使用小写字母和下划线
2. 长度不超过30个字符
3. 能够准确表达字符串的含义
4. 只返回键名，不要其他内容

字符串：{string_value}"""
            
            data = {
                'model': 'qwen3:14b',
                'stream': False,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.3
            }
            
            # 发送请求
            response = requests.post(
                f'{self.api_base_url}/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_key = result['choices'][0]['message']['content'].strip()
                # 如果结果中包含 <think> 标签
                # 则使用正则移除 <think>...</think> 标签及其中的内容
                if "<think>" in ai_key:
                    # print(f"原始AI键名: {ai_key}")
                    # 正则移除 <think>...</think> 标签及其中的内容
                    ai_key = re.sub(r'<think>[.\s]*?</think>', '', ai_key).strip()
                    # print(f"移除标签后的AI键名: {ai_key}")
                # 清理AI生成的键名
                ai_key = re.sub(r'[^a-zA-Z0-9_]', '_', ai_key)
                ai_key = re.sub(r'_+', '_', ai_key).strip('_').lower()
                
                # if ai_key and len(ai_key) <= 50:
                if ai_key:
                    return ai_key
                else:
                    print(f"警告: 生成的AI键名 {ai_key} 不符合要求，已被截断。")
                    
        except Exception as e:
            print(f"AI键名生成失败: {e}")
            
        return None
    
    def generate_key(self, string_value: str, file_path: Path = None) -> str:
        """为字符串生成键，包含模块前缀"""
        # 生成模块前缀
        module_prefix = ""
        if file_path:
            modules = self.find_module_path(file_path)
            if modules:
                module_prefix = ".".join(modules) + "."
        
        # 尝试使用AI生成键名
        ai_key = self._generate_ai_key(string_value)
        if self.use_ai_key_generation:
            while not ai_key:
                print(f"警告: AI键名生成失败，正在重新生成...")
                ai_key = self._generate_ai_key(string_value)
                print(f"生成的AI键名: {ai_key}")

            return module_prefix + ai_key
        
        # 回退到传统方法
        # 清理字符串，移除特殊字符
        cleaned = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '_', string_value)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        
        # 如果清理后的字符串太短，使用哈希值
        if len(cleaned) < 2:
            hash_value = hashlib.md5(string_value.encode('utf-8')).hexdigest()[:8]
            base_key = f"str_{hash_value}"
        else:
            # 限制长度
            if len(cleaned) > 50:
                cleaned = cleaned[:47] + "_" + hashlib.md5(string_value.encode('utf-8')).hexdigest()[:3]
            base_key = cleaned.lower()
            
        return module_prefix + base_key
    
    def load_existing_config(self, config_path: Path) -> OrderedDict[str, str]:
        """加载现有的配置文件"""
        config = OrderedDict()
        
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
    
    def save_config(self, config_path: Path, config: OrderedDict[str, str]):
        """保存配置文件"""
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if config_path.suffix.lower() == '.properties':
                # Java properties文件格式
                with open(config_path, 'w', encoding='utf-8') as f:
                    # 保持原有顺序，不进行排序
                    for key, value in config.items():
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
    for string_value, file_path in extracted_strings.items():
        key = extractor.generate_key(string_value, file_path)
        print(f"{key} = {string_value}")
        
        # 避免键冲突
        original_key = key
        counter = 1
        while key in existing_config and existing_config[key] != string_value:
            key = f"{original_key}_{counter}"
            counter += 1
        
        if key not in existing_config:
            existing_config[key] = string_value
            new_entries += 1
            # print(f"新增: {key} = {string_value}")
    
    # 保存配置文件
    extractor.save_config(config_path, existing_config)
    
    print(f"\n完成! 新增了 {new_entries} 个条目")
    print(f"配置文件已保存到: {config_path}")
    print(f"总计 {len(existing_config)} 个配置项")
    
    return 0

if __name__ == '__main__':
    exit(main())