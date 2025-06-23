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

工具会自动排除以下类型的字符串：

- 空字符串或只包含空白字符
- 变量名、类名等标识符
- 纯数字
- 文件名或包名
- 常量名（全大写）
- 只包含符号的字符串
- Java关键字（true、false、null）
- 操作符
- **纯英文字符串**（只包含ASCII字符的字符串将被过滤）

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