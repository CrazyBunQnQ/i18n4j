#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块前缀功能的示例
"""

import tempfile
import os
from pathlib import Path
from i18n_extractor import JavaStringExtractor

def create_test_project():
    """创建测试用的多模块Maven项目"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    print(f"创建测试项目: {project_root}")
    
    # 创建根模块的pom.xml
    root_pom = project_root / "pom.xml"
    root_pom.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>parent-project</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>
</project>
""", encoding='utf-8')
    
    # 创建子模块1: user-service
    user_service_dir = project_root / "user-service"
    user_service_dir.mkdir()
    
    user_service_pom = user_service_dir / "pom.xml"
    user_service_pom.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>user-service</artifactId>
    <version>1.0.0</version>
</project>
""", encoding='utf-8')
    
    # 创建user-service的Java文件
    user_java_dir = user_service_dir / "src" / "main" / "java" / "com" / "example" / "user"
    user_java_dir.mkdir(parents=True)
    
    user_controller = user_java_dir / "UserController.java"
    user_controller.write_text("""
package com.example.user;

public class UserController {
    public void createUser() {
        System.out.println("用户创建成功");
        log.info("用户ID: " + userId + " 已创建");
    }
    
    public void deleteUser() {
        System.out.println("用户删除失败");
    }
}
""", encoding='utf-8')
    
    # 创建子模块2: order-service
    order_service_dir = project_root / "order-service"
    order_service_dir.mkdir()
    
    order_service_pom = order_service_dir / "pom.xml"
    order_service_pom.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>order-service</artifactId>
    <version>1.0.0</version>
</project>
""", encoding='utf-8')
    
    # 创建order-service的Java文件
    order_java_dir = order_service_dir / "src" / "main" / "java" / "com" / "example" / "order"
    order_java_dir.mkdir(parents=True)
    
    order_controller = order_java_dir / "OrderController.java"
    order_controller.write_text("""
package com.example.order;

public class OrderController {
    public void createOrder() {
        System.out.println("订单创建成功");
        log.info("订单号: " + orderId + " 已生成");
    }
    
    public void cancelOrder() {
        System.out.println("订单取消成功");
    }
}
""", encoding='utf-8')
    
    # 创建嵌套模块: order-service/payment-module
    payment_module_dir = order_service_dir / "payment-module"
    payment_module_dir.mkdir()
    
    payment_module_pom = payment_module_dir / "pom.xml"
    payment_module_pom.write_text("""
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>payment-module</artifactId>
    <version>1.0.0</version>
</project>
""", encoding='utf-8')
    
    # 创建payment-module的Java文件
    payment_java_dir = payment_module_dir / "src" / "main" / "java" / "com" / "example" / "payment"
    payment_java_dir.mkdir(parents=True)
    
    payment_service = payment_java_dir / "PaymentService.java"
    payment_service.write_text("""
package com.example.payment;

public class PaymentService {
    public void processPayment() {
        System.out.println("支付处理中");
        log.info("支付金额: " + amount + " 元");
    }
    
    public void refund() {
        System.out.println("退款成功");
    }
}
""", encoding='utf-8')
    
    return project_root

def test_module_prefix():
    """测试模块前缀功能"""
    # 创建测试项目
    project_root = create_test_project()
    
    try:
        # 创建提取器
        extractor = JavaStringExtractor()
        
        # 扫描项目
        print("\n开始扫描多模块项目...")
        extracted_strings = extractor.scan_project(project_root)
        
        print(f"\n提取到 {len(extracted_strings)} 个唯一字符串:")
        
        # 生成键值对并显示
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path)
            print(f"{key} = {string_value}")
            print(f"  文件: {file_path.relative_to(project_root)}")
            print()
        
        # 生成配置文件
        config_path = project_root / "messages.properties"
        existing_config = extractor.load_existing_config(config_path)
        
        for string_value, file_path in extracted_strings.items():
            key = extractor.generate_key(string_value, file_path)
            if key not in existing_config:
                existing_config[key] = string_value
        
        extractor.save_config(config_path, existing_config)
        
        print(f"配置文件已保存到: {config_path}")
        print("\n配置文件内容:")
        print(config_path.read_text(encoding='utf-8'))
        
    finally:
        print(f"\n测试完成！测试文件位于: {project_root}")
        print("可以手动删除测试目录，或者保留用于进一步测试。")

if __name__ == '__main__':
    test_module_prefix()