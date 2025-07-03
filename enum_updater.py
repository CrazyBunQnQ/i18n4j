#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java枚举类国际化更新脚本
根据枚举类中的构造方法，识别指定字段在每个枚举项中的位置，
读取每个枚举项中该字段的值，在多语言配置文件中查找是否存在该值的key，
若存在，则将该key添加到java枚举项的最后。
"""

import re
import os
import argparse
from typing import Dict, List, Tuple, Optional


class EnumUpdater:
    def __init__(self, properties_file: str):
        self.properties_file = properties_file
        self.properties_map = self._load_properties()
    
    def _load_properties(self) -> Dict[str, str]:
        """加载properties文件，构建value到key的映射"""
        properties_map = {}
        try:
            with open(self.properties_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 将value作为key，properties的key作为value存储
                        properties_map[value.strip()] = key.strip()
        except FileNotFoundError:
            print(f"警告: 找不到properties文件: {self.properties_file}")
        except Exception as e:
            print(f"读取properties文件时出错: {e}")
        return properties_map
    
    def _parse_constructor_parameters(self, java_content: str) -> List[str]:
        """解析构造函数参数，返回参数类型列表"""
        # 查找构造函数定义
        constructor_pattern = r'(\w+)\s*\([^)]*\)\s*\{[^}]*this\.\w+\s*=\s*\w+;'
        constructors = re.findall(constructor_pattern, java_content, re.MULTILINE | re.DOTALL)
        
        if not constructors:
            return []
        
        # 查找最完整的构造函数（参数最多的）
        full_constructor_pattern = r'(\w+)\s*\(([^)]*)\)\s*\{'
        matches = re.findall(full_constructor_pattern, java_content)
        
        if not matches:
            return []
        
        # 找到参数最多的构造函数
        max_params = 0
        target_params = ""
        for constructor_name, params in matches:
            param_count = len([p for p in params.split(',') if p.strip()])
            if param_count > max_params:
                max_params = param_count
                target_params = params
        
        # 解析参数类型
        param_types = []
        if target_params.strip():
            for param in target_params.split(','):
                param = param.strip()
                if param:
                    # 提取参数类型
                    parts = param.split()
                    if len(parts) >= 2:
                        param_types.append(parts[0])
        
        return param_types
    
    def _find_target_field_position(self, java_content: str, target_field: str) -> int:
        """查找目标字段在构造函数中的位置"""
        # 查找字段声明
        field_pattern = rf'private\s+\w+\s+{target_field}\s*;'
        if not re.search(field_pattern, java_content):
            print(f"警告: 找不到字段 '{target_field}' 的声明")
            return -1
        
        # 查找构造函数中的赋值语句
        assignment_pattern = rf'this\.{target_field}\s*=\s*(\w+)\s*;'
        match = re.search(assignment_pattern, java_content)
        
        if not match:
            print(f"警告: 找不到字段 '{target_field}' 的赋值语句")
            return -1
        
        param_name = match.group(1)
        
        # 查找最完整的构造函数
        full_constructor_pattern = r'(\w+)\s*\(([^)]*)\)\s*\{'
        matches = re.findall(full_constructor_pattern, java_content)
        
        if not matches:
            return -1
        
        # 找到参数最多的构造函数
        max_params = 0
        target_params = ""
        for constructor_name, params in matches:
            param_count = len([p for p in params.split(',') if p.strip()])
            if param_count > max_params:
                max_params = param_count
                target_params = params
        
        # 查找参数位置
        if target_params.strip():
            params = [p.strip() for p in target_params.split(',') if p.strip()]
            for i, param in enumerate(params):
                parts = param.split()
                if len(parts) >= 2 and parts[1] == param_name:
                    return i
        
        return -1
    
    def _extract_enum_items(self, java_content: str) -> List[Tuple[str, str, List[str]]]:
        """提取枚举项及其参数"""
        enum_items = []
        
        # 更精确的枚举项匹配模式，避免重复匹配
        # 匹配从枚举名开始到下一个枚举名或类体结束
        enum_section_pattern = r'enum\s+\w+\s*\{([^}]+)\}'
        enum_section_match = re.search(enum_section_pattern, java_content, re.DOTALL)
        
        if not enum_section_match:
            return enum_items
        
        enum_body = enum_section_match.group(1)
        
        # 匹配每个枚举项
        enum_pattern = r'(\w+)\s*\(([^)]*)\)\s*([,;])'
        matches = re.findall(enum_pattern, enum_body)
        
        for enum_name, params_str, separator in matches:
            # 解析参数
            params = []
            if params_str.strip():
                # 简单的参数分割（处理字符串中的逗号）
                in_quotes = False
                current_param = ""
                quote_char = None
                
                for char in params_str:
                    if char in ['"', "'"] and not in_quotes:
                        in_quotes = True
                        quote_char = char
                        current_param += char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                        current_param += char
                    elif char == ',' and not in_quotes:
                        params.append(current_param.strip())
                        current_param = ""
                    else:
                        current_param += char
                
                if current_param.strip():
                    params.append(current_param.strip())
            
            # 构造原始文本
            original_text = f"{enum_name}({params_str}){separator}"
            enum_items.append((enum_name, original_text, params))
        
        return enum_items
    
    def _clean_string_value(self, value: str) -> str:
        """清理字符串值，去除引号"""
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value
    
    def update_enum_file(self, java_file: str, target_field: str = "name", output_file: str = None) -> bool:
        """更新Java枚举文件"""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                java_content = f.read()
        except FileNotFoundError:
            print(f"错误: 找不到Java文件: {java_file}")
            return False
        except Exception as e:
            print(f"读取Java文件时出错: {e}")
            return False
        
        # 查找目标字段在构造函数中的位置
        field_position = self._find_target_field_position(java_content, target_field)
        if field_position == -1:
            print(f"无法确定字段 '{target_field}' 在构造函数中的位置")
            return False
        
        print(f"字段 '{target_field}' 在构造函数中的位置: {field_position}")
        
        # 提取枚举项
        enum_items = self._extract_enum_items(java_content)
        if not enum_items:
            print("未找到枚举项")
            return False
        
        print(f"找到 {len(enum_items)} 个枚举项")
        
        # 更新枚举项
        updated_content = java_content
        updates_made = 0
        
        for enum_name, original_text, params in enum_items:
            if field_position < len(params):
                field_value = self._clean_string_value(params[field_position])
                print(f"处理枚举项 {enum_name}: 字段值 = '{field_value}'")
                
                # 在properties中查找对应的key
                if field_value in self.properties_map:
                    properties_key = self.properties_map[field_value]
                    print(f"  找到对应的key: {properties_key}")
                    
                    # 检查是否已经包含了这个key
                    if properties_key not in original_text:
                        # 构造新的枚举项文本
                        # 移除末尾的逗号或分号
                        new_text = original_text.rstrip(',;')
                        # 在最后一个参数后添加新的key参数
                        if new_text.endswith(')'):
                            new_text = new_text[:-1] + f',"{properties_key}")'
                        
                        # 保持原来的结尾符号
                        if original_text.endswith(','):
                            new_text += ','
                        elif original_text.endswith(';'):
                            new_text += ';'
                        
                        # 替换原文本
                        updated_content = updated_content.replace(original_text, new_text)
                        updates_made += 1
                        print(f"  已更新: {original_text} -> {new_text}")
                    else:
                        print(f"  枚举项已包含key: {properties_key}")
                else:
                    print(f"  未找到对应的key")
            else:
                print(f"枚举项 {enum_name} 的参数数量不足，无法获取字段值")
        
        # 保存更新后的文件
        output_path = output_file if output_file else java_file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"\n成功更新文件: {output_path}")
            print(f"总共更新了 {updates_made} 个枚举项")
            return True
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Java枚举类国际化更新工具')
    parser.add_argument('java_files', nargs='+', help='要处理的Java枚举文件路径')
    parser.add_argument('-p', '--properties', required=True, help='多语言配置文件路径')
    parser.add_argument('-f', '--field', default='name', help='要处理的字段名（默认: name）')
    parser.add_argument('-o', '--output-dir', help='输出目录（可选，默认覆盖原文件）')
    
    args = parser.parse_args()
    
    # 创建更新器
    updater = EnumUpdater(args.properties)
    
    print(f"加载了 {len(updater.properties_map)} 个properties映射")
    
    # 处理每个Java文件
    for java_file in args.java_files:
        print(f"\n处理文件: {java_file}")
        
        output_file = None
        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            filename = os.path.basename(java_file)
            output_file = os.path.join(args.output_dir, filename)
        
        success = updater.update_enum_file(java_file, args.field, output_file)
        if success:
            print(f"✓ 成功处理: {java_file}")
        else:
            print(f"✗ 处理失败: {java_file}")


if __name__ == '__main__':
    main()