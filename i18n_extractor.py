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
import shutil
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
        
        # 配置选项：是否忽略日志中的字符串，默认为True
        self.ignore_log_strings = True
        
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
    
    def is_log_string(self, string_value: str, context: str = "") -> bool:
        """检测字符串是否来自日志语句"""
        if not self.ignore_log_strings:
            return False
            
        # 检查字符串内容是否包含典型的日志关键词
        log_keywords = []
        
        # 检查是否包含日志关键词
        for keyword in log_keywords:
            if keyword in string_value:
                return True
        
        # 检查上下文是否包含日志相关的方法调用
        if context:
            log_method_patterns = [
                r'log\.',  # log.info(), log.error() 等
                r'Log\.',  # log.info(), log.error() 等
                r'logger\.',  # logger.info(), logger.error() 等
                r'Logger\.',  # Logger.getLogger() 等
                r'LoggerFactory\.',  # LoggerFactory.getLogger() 等
                r'\.info\s*\(',  # .info()
                r'\.debug\s*\(',  # .debug()
                r'\.warn\s*\(',  # .warn()
                r'\.error\s*\(',  # .error()
                r'\.trace\s*\(',  # .trace()
                r'\.logProcessorLog\(',
                r'System\.out\.print',  # System.out.print/println
                r'System\.err\.print',  # System.err.print/println
                r'printStackTrace',  # printStackTrace()
            ]
            
            for pattern in log_method_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    return True
        
        return False
    
    def is_valid_string(self, string_value: str, context: str = "") -> bool:
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
        
        # 检查是否为日志字符串（如果启用了忽略日志字符串选项）
        if self.is_log_string(string_value, context):
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
        
        # 按行分析，获取每个字符串的上下文
        lines = cleaned_content.split('\n')
        for line_num, line in enumerate(lines):
            line_matches = self.string_pattern.findall(line)
            for match in line_matches:
                string_value = match[0]
                # 传递当前行作为上下文
                if self.is_valid_string(string_value, line):
                    strings.add(string_value)
        
        # 添加检测到的拼接字符串
        for original_pattern, formatted_string in concatenated_strings.items():
            # 对于拼接字符串，传递原始模式作为上下文
            if self.is_valid_string(formatted_string, original_pattern):
                strings.add(formatted_string)
                
        return strings
    
    def scan_project(self, project_path: Path) -> OrderedDict[str, Path]:
        """扫描整个Java项目，返回字符串到文件路径的有序映射"""
        all_strings = OrderedDict()  # 字符串 -> 文件路径的映射
        java_files = list(project_path.rglob('*.java'))
        
        # 过滤掉测试目录中的文件
        filtered_java_files = []
        excluded_count = 0
        for java_file in java_files:
            # 检查文件路径是否包含测试目录
            if 'src\\test' in str(java_file) or 'src/test' in str(java_file):
                excluded_count += 1
                continue
            # 检查文件名是否包含 `Test`
            if 'Test' in java_file.name:
                excluded_count += 1
                continue
            filtered_java_files.append(java_file)
        
        print(f"找到 {len(java_files)} 个Java文件，排除 {excluded_count} 个测试文件，处理 {len(filtered_java_files)} 个文件")
        
        for java_file in filtered_java_files:
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

        if "-openservice" in current_path.name:
            print("test")
        
        # 向上查找包含pom.xml的目录
        while current_path.parent != current_path:  # 避免到达根目录
            pom_file = current_path / 'pom.xml'
            if pom_file.exists():
                module_name = current_path.name.lower()
                # 过滤掉临时目录名（通常以tmp开头）和其他无意义的目录名
                if not (module_name.startswith('tmp') or module_name.startswith('temp')):
                    modules.insert(0, module_name)
            current_path = current_path.parent
            
        return modules
    
    def _generate_ai_key(self, string_value: str, invalid_keys: set = None) -> str:
        """使用AI生成简短的键名"""
        if not self.use_ai_key_generation:
            return None, None
            
        if invalid_keys is None:
            invalid_keys = set()
            
        try:
            # 构建API请求
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 构建提示词 qwen3 模型需要关闭思考
            # prompt = f"""/no_think 请为以下代码块中的字符串
            prompt = f"""请为以下代码块中的字符串

```
{string_value}
```

生成一个简短的英文键名，要求：

1. 只能使用小写字母、数字和下划线, 不能包含其他字符
2. 长度不超过50个字符
3. 只返回最终键名，不要其他内容"""
            
            # 如果有无效键名，添加到提示词中
            if invalid_keys:
                invalid_keys_str = ", ".join(sorted(invalid_keys))
                print(f"当前无效键名: {invalid_keys_str}")
                prompt += f"""
4. 不要返回以下结果 `{invalid_keys_str}`, 请尝试使用简写或拼音或添加数字"""
            
            data = {
                # 'model': 'qwen3:14b',
                'model': 'gemma3:12b',
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
                # 原始结果
                original_key = ai_key
                # 清理AI生成的键名
                ai_key = re.sub(r'[^a-zA-Z0-9_]', '_', ai_key)
                ai_key = re.sub(r'_+', '_', ai_key).strip('_').lower()
                
                # if ai_key and len(ai_key) <= 50:
                if ai_key and len(ai_key) > 0:
                    return ai_key, original_key
                else:
                    print(f"警告: 【{string_value}】生成的AI键名 `{ai_key}` 不符合要求，已被截断。")
                    print(f"AI 返回的原始信息: {result['choices'][0]['message']['content']}")
                    return None, original_key
                    
        except Exception as e:
            print(f"AI键名生成失败: {e}")
            
        return None, None
    
    def generate_key(self, string_value: str, file_path: Path = None, existing_keys: set = None, existing_config: dict = None) -> str:
        """为字符串生成键，包含模块前缀"""
        if existing_keys is None:
            existing_keys = set()
        if existing_config is None:
            existing_config = {}
        
        string_value = string_value.strip()
        # 检查键值是否已存在，如果存在则返回现有的键名
        for existing_key, existing_value in existing_config.items():
            if existing_value == string_value:
                print(f"跳过重复键值: {existing_key} = {string_value}")
                return existing_key
            
        # 生成模块前缀
        module_prefix = ""
        if file_path:
            modules = self.find_module_path(file_path)
            if modules:
                module_prefix = ".".join(modules) + "."
        
        # 尝试使用AI生成键名
        if self.use_ai_key_generation:
            invalid_keys = set()  # 记录无效的键名
            attempt = 0
            
            while True:
                attempt += 1
                ai_key, original_key = self._generate_ai_key(string_value, invalid_keys)
                
                if ai_key:
                    full_key = module_prefix + ai_key
                    # 检查键名是否已存在
                    if full_key not in existing_keys:
                        if attempt > 1:
                            print(f"AI键名生成成功: '{ai_key}' (尝试第 {attempt} 次)")
                        return full_key
                    else:
                        # 记录无效键名
                        invalid_keys.add(original_key)
                        print(f"警告: AI生成的键名 `{ai_key}` 已存在，尝试第 {attempt} 次重新生成【{string_value}】的键值...")
                else:
                    # 记录无效键名
                    if original_key:
                        invalid_keys.add(original_key)
                    print(f"警告: 【{string_value}】的AI键名生成失败，尝试第 {attempt} 次... {original_key}")
                    # 如果连续失败多次，可以考虑退出
                    # if attempt >= 100:
                        # print(f"AI键名生成连续失败 {attempt} 次，退出AI生成模式")
                        # break
        
        # 等待用户输入 y/n 决定是否回退到传统方法
        choice = input("是否回退到传统方法生成键名？(y/n)：").lower()
        if choice != 'y':
            # 停止脚本结束程序
            print("已停止脚本运行。")
            # 在退出前保存当前已处理的配置
            if hasattr(self, '_current_config') and hasattr(self, '_current_config_path'):
                print("正在保存当前已处理的配置...")
                self.save_config(self._current_config_path, self._current_config)
                print("配置已保存。")
            exit(0)
        
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
        
        # 确保传统方法生成的键名也是唯一的
        full_key = module_prefix + base_key
        if full_key not in existing_keys:
            return full_key
        
        # 添加后缀确保唯一性
        counter = 1
        while f"{full_key}_{counter}" in existing_keys:
            counter += 1
        return f"{full_key}_{counter}"
    
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
        """保存配置文件，包含备份机制"""
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建临时文件路径
        temp_path = config_path.with_suffix(f"{config_path.suffix}.tmp")
        # 创建备份文件路径
        backup_path = config_path.with_suffix(f"{config_path.suffix}.bak")
        
        try:
            # 先写入临时文件
            if config_path.suffix.lower() == '.properties':
                # Java properties文件格式
                with open(temp_path, 'w', encoding='utf-8') as f:
                    # 保持原有顺序，不进行排序
                    for key, value in config.items():
                        f.write(f"{key}={value}\n")
            else:
                # INI文件格式
                parser = configparser.ConfigParser()
                parser['DEFAULT'] = config
                with open(temp_path, 'w', encoding='utf-8') as f:
                    parser.write(f)
            
            # 如果原文件存在，创建备份
            if config_path.exists():
                try:
                    shutil.copy2(config_path, backup_path)
                except Exception as e:
                    print(f"警告: 创建备份文件失败: {e}")
            
            # 将临时文件重命名为目标文件
            try:
                # 在Windows上，如果目标文件存在，需要先删除
                if config_path.exists():
                    config_path.unlink()
                shutil.move(temp_path, config_path)
            except Exception as e:
                print(f"错误: 重命名临时文件失败: {e}")
                # 尝试恢复备份
                if backup_path.exists():
                    try:
                        shutil.copy2(backup_path, config_path)
                        print("已从备份恢复配置文件")
                    except Exception:
                        print("警告: 无法从备份恢复配置文件")
                raise
                
        except Exception as e:
            print(f"错误: 保存配置文件时出错: {e}")
            # 清理临时文件
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise

def main():
    parser = argparse.ArgumentParser(description='Java Spring Boot项目国际化字符串提取工具')
    parser.add_argument('--project_dir', default='E:\\LaProjects\\2.15\\Singularity\\Common', help='Java项目目录路径')
    # parser.add_argument('--project_dir', default='E:\\LaProjects\\2.15\\Singularity\\DataCenter\\dev\\datacenter\\datacenter-openservice', help='Java项目目录路径')
    parser.add_argument('--config_file', default='D:\\Downloads\\messages_no_log.properties', help='多语言配置文件路径')
    parser.add_argument('--encoding', default='utf-8', help='文件编码 (默认: utf-8)')
    parser.add_argument('--ignore-log-strings', action='store_true', default=True, help='是否忽略日志中的字符串 (默认: True)')
    parser.add_argument('--include-log-strings', action='store_true', help='包含日志中的字符串 (覆盖 --ignore-log-strings)')
    
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
    existing_keys = set(existing_config.keys())
    processed_count = 0
    
    # 设置当前配置和路径，用于异常退出时保存
    extractor._current_config = existing_config
    extractor._current_config_path = config_path
    
    try:
        for string_value, file_path in extracted_strings.items():
            # 传递已存在的键名集合和配置，确保生成唯一键名和键值
            key = extractor.generate_key(string_value, file_path, existing_keys, existing_config)
            
            # 如果返回的是已存在的键名（重复键值），则跳过处理
            if key in existing_config and existing_config[key] == string_value:
                processed_count += 1
                continue
            
            print(f"{key} = {string_value}")
            
            # 添加新的键值对
            if key not in existing_config:
                existing_config[key] = string_value
                existing_keys.add(key)  # 更新已存在键名集合
                new_entries += 1
                # print(f"新增: {key} = {string_value}")
            
            processed_count += 1
            
            # 每100个配置保存一次
            if processed_count % 100 == 0:
                print(f"\n已处理 {processed_count} 个字符串，正在保存配置...")
                extractor.save_config(config_path, existing_config)
                print(f"配置已保存，继续处理...")
    
    except KeyboardInterrupt:
        print("\n检测到用户中断，正在保存当前进度...")
        extractor.save_config(config_path, existing_config)
        print(f"已保存 {processed_count} 个处理结果到配置文件。")
        return 1
    except Exception as e:
        print(f"\n处理过程中发生错误: {e}")
        print("正在保存当前进度...")
        extractor.save_config(config_path, existing_config)
        print(f"已保存 {processed_count} 个处理结果到配置文件。")
        raise
    
    # 最终保存配置文件
    extractor.save_config(config_path, existing_config)
    
    print(f"\n完成! 新增了 {new_entries} 个条目")
    print(f"配置文件已保存到: {config_path}")
    print(f"总计 {len(existing_config)} 个配置项")
    
    return 0

if __name__ == '__main__':
    exit(main())