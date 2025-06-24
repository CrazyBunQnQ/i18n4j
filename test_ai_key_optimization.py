#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI键名生成的优化功能
- 最多3次重试机制
- 键名唯一性检查
- 自动添加后缀避免冲突
"""

import os
import tempfile
import shutil
from pathlib import Path
from i18n_extractor import JavaStringExtractor

def create_test_env():
    """创建测试环境文件"""
    env_file = Path('.env')
    if not env_file.exists():
        print("创建测试 .env 文件...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("OPENAI_API_KEY=test_key\n")
            f.write("OPENAI_API_BASE_URL=https://api.openai.com\n")
        print("请在 .env 文件中配置正确的 API 密钥和端点")
        return False
    return True

def create_test_project():
    """创建测试项目结构"""
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp(prefix='ai_key_test_'))
    print(f"创建测试项目: {temp_dir}")
    
    # 创建Maven项目结构
    project_dir = temp_dir / "test-project"
    src_dir = project_dir / "src" / "main" / "java" / "com" / "example"
    src_dir.mkdir(parents=True)
    
    # 创建pom.xml
    pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
</project>'''
    
    with open(project_dir / "pom.xml", 'w', encoding='utf-8') as f:
        f.write(pom_content)
    
    # 创建包含重复字符串的Java文件，测试唯一性
    java_content1 = '''package com.example;

public class TestService1 {
    public void method1() {
        System.out.println("用户登录成功");
        System.out.println("操作完成");
        System.out.println("数据保存成功");
    }
}'''
    
    java_content2 = '''package com.example;

public class TestService2 {
    public void method2() {
        System.out.println("用户登录成功");  // 重复字符串
        System.out.println("系统错误");
        System.out.println("网络连接失败");
    }
}'''
    
    java_content3 = '''package com.example;

public class TestService3 {
    public void method3() {
        System.out.println("操作完成");  // 重复字符串
        System.out.println("文件上传成功");
        System.out.println("邮件发送完成");
    }
}'''
    
    with open(src_dir / "TestService1.java", 'w', encoding='utf-8') as f:
        f.write(java_content1)
    
    with open(src_dir / "TestService2.java", 'w', encoding='utf-8') as f:
        f.write(java_content2)
        
    with open(src_dir / "TestService3.java", 'w', encoding='utf-8') as f:
        f.write(java_content3)
    
    return project_dir

def test_ai_key_generation():
    """测试AI键名生成功能"""
    print("=== 测试AI键名生成优化功能 ===")
    
    # 检查环境配置
    if not create_test_env():
        return
    
    # 创建测试项目
    project_dir = create_test_project()
    
    try:
        # 初始化提取器
        extractor = JavaStringExtractor()
        
        print(f"\n扫描项目: {project_dir}")
        print(f"AI键名生成: {'启用' if extractor.use_ai_key_generation else '禁用'}")
        
        # 扫描项目
        extracted_strings = extractor.scan_project(project_dir)
        print(f"\n提取到 {len(extracted_strings)} 个字符串")
        
        # 测试键名生成和唯一性
        existing_keys = set()
        generated_keys = {}
        
        print("\n=== 键名生成测试 ===")
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path, existing_keys)
            existing_keys.add(key)
            
            if string_value in generated_keys:
                print(f"重复字符串 '{string_value}':")
                print(f"  第一次生成: {generated_keys[string_value]}")
                print(f"  第二次生成: {key}")
                print(f"  唯一性检查: {'通过' if key != generated_keys[string_value] else '失败'}")
            else:
                generated_keys[string_value] = key
                print(f"{key} = {string_value}")
        
        # 保存配置文件
        config_path = Path("test_messages.properties")
        config = {}
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path, set(config.keys()))
            config[key] = string_value
        
        extractor.save_config(config_path, config)
        print(f"\n配置文件已保存到: {config_path}")
        
        # 验证唯一性
        unique_keys = set(config.keys())
        print(f"\n=== 唯一性验证 ===")
        print(f"生成的键名总数: {len(config)}")
        print(f"唯一键名数量: {len(unique_keys)}")
        print(f"唯一性检查: {'通过' if len(config) == len(unique_keys) else '失败'}")
        
        # 显示生成的配置
        print(f"\n=== 生成的配置 ===")
        for key, value in config.items():
            print(f"{key} = {value}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        if project_dir.exists():
            shutil.rmtree(project_dir.parent)
            print(f"\n已清理临时目录: {project_dir.parent}")

if __name__ == '__main__':
    test_ai_key_generation()