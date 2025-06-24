#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI键名生成功能的示例
"""

import tempfile
import os
from pathlib import Path
from i18n_extractor import JavaStringExtractor

def create_test_env():
    """创建测试环境变量文件"""
    env_content = """# 测试用的API配置
# 请替换为实际的API密钥和地址
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_API_BASE_URL=https://your-api-endpoint.com
"""
    
    env_path = Path('.env')
    if not env_path.exists():
        env_path.write_text(env_content, encoding='utf-8')
        print(f"已创建 .env 文件: {env_path.absolute()}")
        print("请编辑 .env 文件，填入正确的API配置")
        return False
    return True

def create_test_project():
    """创建测试用的Java项目"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    print(f"创建测试项目: {project_root}")
    
    # 创建pom.xml
    pom_file = project_root / "pom.xml"
    pom_file.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
</project>
""", encoding='utf-8')
    
    # 创建Java文件
    java_dir = project_root / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    
    test_controller = java_dir / "TestController.java"
    test_controller.write_text("""
package com.example;

public class TestController {
    public void testMethod() {
        System.out.println("用户登录成功");
        log.info("数据保存失败");
        throw new Exception("权限验证失败");
        System.out.println("订单创建完成");
        log.warn("系统资源不足");
        System.out.println("文件上传成功");
        log.error("网络连接超时");
        System.out.println("邮件发送完成");
    }
}
""", encoding='utf-8')
    
    return project_root

def test_ai_key_generation():
    """测试AI键名生成功能"""
    # 检查环境配置
    if not create_test_env():
        return
    
    # 创建测试项目
    project_root = create_test_project()
    
    try:
        # 创建提取器
        extractor = JavaStringExtractor()
        
        # 检查API配置
        if extractor.use_ai_key_generation:
            print("✓ AI键名生成功能已启用")
            print(f"API Base URL: {extractor.api_base_url}")
        else:
            print("⚠ AI键名生成功能未启用，请检查 .env 文件中的API配置")
            print("将使用传统键名生成方法")
        
        # 扫描项目
        print("\n开始扫描项目...")
        extracted_strings = extractor.scan_project(project_root)
        
        print(f"\n提取到 {len(extracted_strings)} 个唯一字符串:")
        
        # 生成键值对并显示
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path)
            print(f"{key} = {string_value}")
        
        # 生成配置文件
        config_path = project_root / "messages.properties"
        existing_config = extractor.load_existing_config(config_path)
        
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path)
            if key not in existing_config:
                existing_config[key] = string_value
        
        extractor.save_config(config_path, existing_config)
        
        print(f"\n配置文件已保存到: {config_path}")
        print("\n配置文件内容:")
        print(config_path.read_text(encoding='utf-8'))
        
    finally:
        print(f"\n测试完成！测试文件位于: {project_root}")
        print("可以手动删除测试目录，或者保留用于进一步测试。")

if __name__ == '__main__':
    test_ai_key_generation()