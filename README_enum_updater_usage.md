# Java枚举类国际化更新工具使用说明

## 功能描述

这个Python脚本可以自动分析Java枚举类，识别指定字段在构造函数中的位置，读取每个枚举项中该字段的值，在多语言配置文件中查找对应的key，并将找到的key添加到枚举项的最后。

## 使用方法

### 基本语法

```bash
python enum_updater.py <java_files> -p <properties_file> -f <field_name> [-o <output_dir>]
```

### 参数说明

- `java_files`: 要处理的Java枚举文件路径（可以指定多个文件）
- `-p, --properties`: 多语言配置文件路径（必需）
- `-f, --field`: 要处理的字段名（默认: name）
- `-o, --output-dir`: 输出目录（可选，默认覆盖原文件）

### 使用示例

1. **处理单个文件**：
```bash
python enum_updater.py test_enum_example_2.java -p messages.properties -f name
```

2. **处理多个文件**：
```bash
python enum_updater.py test_enum_example_1.java test_enum_example_2.java -p messages.properties -f name
```

3. **指定输出目录**：
```bash
python enum_updater.py test_enum_example_2.java -p messages.properties -f name -o output/
```

## 工作原理

1. **解析构造函数**：脚本会分析Java枚举类的构造函数，找到参数最多的构造函数作为标准
2. **定位字段位置**：通过分析字段声明和构造函数中的赋值语句，确定指定字段在构造函数参数中的位置
3. **提取枚举项值**：从每个枚举项的参数中提取指定位置的字段值
4. **查找properties映射**：在properties文件中查找该值对应的key
5. **更新枚举项**：如果找到对应的key，将其添加到枚举项的最后一个参数位置

## 支持的Java枚举格式

### 示例1：简单枚举
```java
public enum TestDictionary {
    ONLINE("在线", 1),
    OFFLINE("离线", 0);
    
    private final String name;
    private final int code;
    
    TestDictionary(String name, int code) {
        this.name = name;
        this.code = code;
    }
}
```

### 示例2：复杂枚举
```java
public enum HttpStatisticColumEnum {
    URL(1,"url","url","访问数"),
    REQ_METHOD(2,"req_method","reqMethod","请求方式");
    
    private Integer typeIndex;
    private String colum;
    private String filedName;
    private String name;
    
    HttpStatisticColumEnum(Integer typeIndex, String colum, String filedName, String name) {
        this.typeIndex = typeIndex;
        this.colum = colum;
        this.filedName = filedName;
        this.name = name;
    }
}
```

## Properties文件格式

properties文件应该采用标准的key=value格式：

```properties
common.common-facade.operating_system=操作系统
operationcenter.operation-model.browser=浏览器
operationcenter.operation-model.access_count=访问数
```

## 更新结果示例

**更新前**：
```java
URL(1,"url","url","访问数"),
```

**更新后**：
```java
URL(1,"url","url","访问数","operationcenter.operation-model.access_count"),
```

## 注意事项

1. **字段名匹配**：确保指定的字段名在Java类中存在对应的私有字段声明
2. **构造函数分析**：脚本会自动选择参数最多的构造函数进行分析
3. **文件备份**：建议在运行脚本前备份原始文件
4. **编码格式**：确保Java文件和properties文件都使用UTF-8编码
5. **路径问题**：可以使用相对路径或绝对路径

## 错误处理

- 如果找不到指定字段，脚本会输出警告信息
- 如果properties文件不存在，脚本会继续运行但不会进行更新
- 如果枚举项已经包含了对应的key，脚本会跳过该项

## 输出信息

脚本运行时会输出详细的处理信息：
- 加载的properties映射数量
- 每个文件的处理状态
- 字段在构造函数中的位置
- 找到的枚举项数量
- 每个枚举项的处理结果
- 总共更新的枚举项数量