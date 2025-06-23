#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试示例脚本
演示如何使用i18n_extractor工具
"""

import os
import tempfile
from pathlib import Path
from i18n_extractor import JavaStringExtractor

def create_test_java_files():
    """创建测试用的Java文件"""
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    # 创建Maven项目结构
    src_dir = temp_dir / "src" / "main" / "java" / "com" / "example"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建pom.xml
    pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
</project>
'''
    
    with open(temp_dir / "pom.xml", "w", encoding="utf-8") as f:
        f.write(pom_content)
    
    # 创建测试Java文件1
    java_content1 = '''
package com.example;

import org.springframework.web.bind.annotation.*;

/**
 * 用户控制器
 * This is a comment with "string in comment"
 */
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    // 单行注释中的 "字符串" 应该被忽略
    private static final String SUCCESS_MESSAGE = "用户操作成功";
    private static final String ERROR_MESSAGE = "操作失败，请重试";
    private static final String ENGLISH_ONLY = "This is English only text";
    private static final String MIXED_TEXT = "Welcome 欢迎";
    
    @GetMapping("/login")
    public String login() {
        System.out.println("用户尝试登录");
        System.out.println("Debug message in English");
        return "登录页面";
    }
    
    @PostMapping("/register")
    public ResponseEntity<String> register(@RequestBody User user) {
        if (user.getName().isEmpty()) {
            return ResponseEntity.badRequest().body("用户名不能为空");
        }
        
        /* 多行注释
         * 包含 "注释中的字符串"
         * 应该被忽略
         */
        
        logger.info("新用户注册: " + user.getName());
        logger.debug("Registration attempt for user");
        return ResponseEntity.ok("注册成功");
    }
    
    private void validateUser(String username, String password) {
        if (username == null || username.trim().equals("")) {
            throw new IllegalArgumentException("用户名无效");
        }
        
        if (password.length() < 6) {
            throw new IllegalArgumentException("密码长度至少6位");
        }
        
        // 这些英文字符串应该被过滤掉
        String debugMsg = "Password validation failed";
        String logMsg = "User validation completed";
    }
}
'''
    
    with open(src_dir / "UserController.java", "w", encoding="utf-8") as f:
        f.write(java_content1)
    
    # 创建测试Java文件2
    java_content2 = '''
package com.example;

import org.springframework.stereotype.Service;

@Service
public class UserService {
    
    public boolean authenticateUser(String username, String password) {
        // 这里有一些业务逻辑
        if ("admin".equals(username)) {
            return true;
        }
        
        System.out.println("认证失败");
        System.out.println("Authentication failed");  // 纯英文，应该被过滤
        return false;
    }
    
    public String getUserStatus(int userId) {
        switch (userId) {
            case 1:
                return "活跃用户";
            case 2:
                return "已禁用";
            case 3:
                return "Suspended";  // 纯英文，应该被过滤
            default:
                return "未知状态";
        }
    }
    
    public void logMessage() {
        System.out.println("Processing user data...");  // 纯英文，应该被过滤
        System.out.println("处理用户数据中...");  // 包含中文，应该被提取
        System.out.println("Error: 用户不存在");  // 混合文本，应该被提取
    }
    
    @Override
    public String toString() {
        return "UserService{version=1.0}";  // 纯英文，应该被过滤
    }
}
'''
    
    with open(src_dir / "UserService.java", "w", encoding="utf-8") as f:
        f.write(java_content2)
    
    return temp_dir

def test_extraction():
    """测试字符串提取功能"""
    print("=== Java Spring Boot 国际化字符串提取工具测试 ===")
    
    # 创建测试项目
    print("\n1. 创建测试Java项目...")
    test_project = create_test_java_files()
    print(f"测试项目创建在: {test_project}")
    
    # 创建提取器
    extractor = JavaStringExtractor()
    
    # 扫描项目
    print("\n2. 扫描Java项目，提取字符串...")
    extracted_strings = extractor.scan_project(test_project)
    
    print(f"\n提取到的字符串 ({len(extracted_strings)} 个):")
    for i, string in enumerate(sorted(extracted_strings), 1):
        print(f"  {i:2d}. {string}")
    
    # 生成配置文件
    print("\n3. 生成配置文件...")
    config_file = test_project / "messages.properties"
    
    config = {}
    for string_value in extracted_strings:
        key = extractor.generate_key(string_value)
        config[key] = string_value
    
    extractor.save_config(config_file, config)
    
    print(f"\n配置文件已生成: {config_file}")
    print("\n配置文件内容:")
    with open(config_file, 'r', encoding='utf-8') as f:
        print(f.read())
    
    # 清理
    print(f"\n测试完成！测试文件位于: {test_project}")
    print("可以手动删除测试目录，或者保留用于进一步测试。")
    
    return test_project, config_file

if __name__ == "__main__":
    test_extraction()