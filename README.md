# Java Spring Boot 国际化字符串提取工具

这是一个用于从Java Spring Boot项目中提取硬编码字符串并生成国际化配置文件的Python工具。

## 功能特性

1. **智能字符串提取**：扫描Java源码文件，提取所有硬编码字符串
2. **注释过滤**：自动排除单行注释、多行注释和注解中的字符串
3. **智能过滤**：排除变量名、常量名、数字等非用户可见字符串
4. **非英文字符检测**：只提取包含非英文字符的字符串（中文、日文、韩文等以及非英文标点符号）
5. **字符编码检测**：自动检测文件编码，支持UTF-8、GBK、GB2312等多种编码
6. **去重处理**：自动去除重复的字符串
7. **键名生成**：为每个字符串生成合适的键名
8. **配置文件合并**：支持与现有配置文件合并，避免覆盖已有配置
9. **多种格式支持**：支持.properties和.ini格式的配置文件
10. **字符串拼接检测**：智能识别字符串拼接模式，生成带 `{}` 占位符的完整句子

## 安装要求

- Python 3.6+
- chardet>=4.0.0（字符编码检测库）

### 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装：

```bash
pip install chardet>=4.0.0
```

## 使用方法

### 基本用法

```bash
python i18n_extractor.py <项目目录> <配置文件路径>
```

### 参数说明

- `项目目录`：Java Spring Boot项目的根目录路径（包含pom.xml的目录）
- `配置文件路径`：输出的多语言配置文件路径（支持.properties或.ini格式）
- `--encoding`：可选，指定文件编码（默认utf-8）

### 使用示例

```bash
# 扫描项目并生成properties文件
python i18n_extractor.py /path/to/spring-boot-project /path/to/messages.properties

# 扫描项目并生成ini文件
python i18n_extractor.py /path/to/spring-boot-project /path/to/i18n.ini

# 指定编码
python i18n_extractor.py /path/to/spring-boot-project /path/to/messages.properties --encoding gbk
```

## 输出格式

### Properties格式示例

```properties
# 自动生成的国际化配置文件
# Auto-generated i18n configuration file

user_login_success=用户登录成功
user_not_found=用户不存在
password_incorrect=密码错误
```

### INI格式示例

```ini
[DEFAULT]
user_login_success = 用户登录成功
user_not_found = 用户不存在
password_incorrect = 密码错误
```

## 字符串过滤规则

工具只会提取包含非英文字符（包括中文、日文、韩文、阿拉伯文等）的硬编码字符串，自动过滤以下内容：

- 纯英文字符串（如 "This is English only text"）
- 注释中的字符串
- 包名和导入语句
- 类名、方法名、变量名
- 注解内容
- SQL语句和正则表达式
- 日志级别和异常类名
- 文件路径和URL
- 数字和布尔值

### 字符串拼接处理

工具能够智能识别以下字符串拼接模式，并将其转换为带 `{}` 占位符的完整句子：

#### 基本拼接模式
- `"字符串" + 变量 + "字符串"` → `"字符串{}字符串"`
- `"字符串" + 变量` → `"字符串{}"`
- `变量 + "字符串"` → `"{}字符串"`

#### 格式化方法
- `String.format("模板字符串", 参数...)` → `"模板字符串"`
- `MessageFormat.format("模板字符串", 参数...)` → `"模板字符串"`

#### StringBuilder/StringBuffer 链式调用
- `new StringBuilder().append("字符串").append(变量).append("字符串")` → `"字符串{}字符串"`
- `builder.append("字符串").append(变量).append("字符串")` → `"字符串{}字符串"`
- `new StringBuffer().append("字符串").append(变量)` → `"字符串{}"`

#### 多行字符串拼接
- 跨多行的字符串拼接模式：
```java
String message = "处理开始: " +
                processId +
                " 状态更新";
```
→ `"处理开始: {}状态更新"`

这确保了完整的i18n配置条目不会被拆分，保持了句子的完整性。

### 非英文字符检测规则

只有包含以下字符的字符串才会被提取：
- 中文字符（\u4e00-\u9fff）
- 日文字符
- 韩文字符
- 其他非ASCII字符（\x80-\xFF）
- 非英文标点符号（如中文标点、全角符号等）

**示例：**
- `"Hello World"` - 被过滤（纯英文）
- `"你好世界"` - 被提取（包含中文）
- `"Welcome 欢迎"` - 被提取（包含中文）
- `"Error: 用户不存在"` - 被提取（包含中文）

## 键名生成规则

1. 移除特殊字符，用下划线替换
2. 合并连续的下划线
3. 转换为小写
4. 如果清理后的字符串太短，使用MD5哈希值
5. 限制长度在50个字符以内
6. 避免键名冲突，自动添加数字后缀

## 注意事项

1. 确保项目目录包含pom.xml文件（Maven项目标识）
2. 工具会递归扫描所有.java文件
3. 如果配置文件已存在，新提取的字符串会与现有配置合并
4. 相同的字符串不会重复添加
5. 建议在使用前备份现有的配置文件
6. **只有包含非英文字符的字符串才会被提取**，纯英文字符串将被自动过滤
7. 工具会自动检测文件编码，但建议使用UTF-8编码保存Java文件

## 错误处理

- 如果无法读取某个Java文件，工具会显示警告并继续处理其他文件
- 支持多种编码的自动检测（UTF-8、GBK、GB2312、Latin-1等）
- 使用chardet库进行智能编码检测，置信度低于70%时使用UTF-8作为默认编码
- 配置文件保存失败时会显示详细错误信息

## 扩展功能

如需更高级的功能，可以考虑安装以下依赖：

```bash
pip install javalang  # 更精确的Java代码解析
pip install click     # 更友好的命令行界面
```

注意：chardet库已经是必需依赖，用于字符编码检测。

## 许可证

本项目采用MIT许可证。