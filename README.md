# Java Spring Boot 国际化工具集

这是一个用于Java Spring Boot项目国际化的Python工具集，包含字符串提取和多语言配置文件生成两个核心工具。

## 工具概览

1. **`i18n_extractor.py`** - 从Java源码中提取硬编码字符串并生成国际化配置文件
2. **`i18n_generator.py`** - 基于源配置文件生成多语言翻译配置文件

## 功能特性

1. **智能字符串提取**：扫描Java源码文件，提取所有硬编码字符串
2. **注释过滤**：自动排除单行注释、多行注释和注解中的字符串
3. **智能过滤**：排除变量名、常量名、数字等非用户可见字符串
4. **非英文字符检测**：只提取包含非英文字符的字符串（中文、日文、韩文等以及非英文标点符号）
5. **字符编码检测**：自动检测文件编码，支持UTF-8、GBK、GB2312等多种编码
6. **去重处理**：自动去除重复的字符串，保持首次扫描到的顺序
7. **智能键名生成**：支持AI生成简短英文键名，回退到传统方法，包含模块前缀
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

## 顺序保持机制

工具在处理字符串时严格按照以下顺序：

1. **文件扫描顺序**: 按照文件系统的自然顺序扫描 Java 文件
2. **字符串发现顺序**: 在每个文件中按照从上到下的顺序提取字符串
3. **去重保持首次**: 当遇到重复字符串时，保留首次扫描到的位置
4. **配置文件追加**: 新发现的字符串总是追加到配置文件的末尾

这确保了配置文件中的键值对顺序与代码中字符串的出现顺序保持一致，便于开发者理解和维护。

## 模块前缀功能

工具支持为多模块Maven项目自动生成带模块前缀的键名：

### 模块检测规则

1. **模块识别**: 以包含 `pom.xml` 的目录作为模块
2. **模块嵌套**: 支持多层模块嵌套，如 `parent-project/user-service/auth-module`
3. **前缀生成**: 将模块目录名转为小写，用 `.` 连接
4. **过滤规则**: 自动过滤临时目录名（如 `tmp*`、`temp*`）和过长的目录名

### 示例

**项目结构:**
```
parent-project/
├── pom.xml
├── user-service/
│   ├── pom.xml
│   └── src/main/java/.../UserController.java
└── order-service/
    ├── pom.xml
    ├── payment-module/
    │   ├── pom.xml
    │   └── src/main/java/.../PaymentService.java
    └── src/main/java/.../OrderController.java
```

**生成的键名:**
```properties
# 来自 user-service 模块
parent-project.user-service.用户创建成功=用户创建成功
parent-project.user-service.用户id_已创建=用户ID: {} 已创建

# 来自 order-service 模块
parent-project.order-service.订单创建成功=订单创建成功
parent-project.order-service.订单号_已生成=订单号: {} 已生成

# 来自 payment-module 嵌套模块
parent-project.order-service.payment-module.支付处理中=支付处理中
parent-project.order-service.payment-module.支付金额_元=支付金额: {} 元
```

### 兼容性

- **单模块项目**: 如果项目根目录直接包含 `pom.xml`，不会添加模块前缀
- **非Maven项目**: 如果没有找到 `pom.xml`，按普通项目处理，不添加前缀

## AI智能键名生成

工具支持使用AI模型生成更加语义化的英文键名，提升配置文件的可读性：

### 配置方法

1. **环境变量配置**: 复制 `.env.example` 为 `.env` 并填入API配置
   ```bash
   cp .env.example .env
   ```

2. **编辑 .env 文件**:
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_API_BASE_URL=https://your-api-endpoint.com
   ```

3. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

### 功能特性

- **智能生成**: 使用 `qwen2.5:14b` 模型分析中文字符串含义，生成简短的英文键名
- **自动回退**: 当API不可用时，自动回退到传统的键名生成方法
- **长度限制**: AI生成的键名限制在30个字符以内
- **格式规范**: 自动清理和格式化，确保键名符合规范（小写字母和下划线）

### 示例对比

**传统方法**:
```properties
user-service.用户登录成功=用户登录成功
user-service.数据保存失败=数据保存失败
user-service.权限验证失败=权限验证失败
```

**AI生成**:
```properties
user-service.user_login_success=用户登录成功
user-service.data_save_failed=数据保存失败
user-service.permission_verify_failed=权限验证失败
```

### 测试功能

运行测试脚本验证AI键名生成功能：
```bash
python test_ai_key_generation.py
```

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

---

# 多语言配置文件生成工具 (i18n_generator.py)

`i18n_generator.py` 是一个智能的多语言配置文件生成工具，能够根据源配置文件自动生成多种语言的翻译配置文件。

## 功能特性

1. **AI智能翻译**：使用OpenAI格式的API调用AI模型进行翻译
2. **多语言支持**：支持生成英文、法文、德文、日文、韩文等多种语言配置
3. **命令行参数**：灵活的命令行参数支持，可指定源文件和目标语言
4. **批量处理**：一次命令可生成多个语言的配置文件
5. **增量更新**：保留现有翻译，只生成缺失的配置项
6. **顺序保持**：生成的配置文件与源文件保持相同的键值对顺序
7. **错误处理**：完善的错误处理和状态报告机制

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `requests>=2.28.0` - HTTP请求库
- `python-dotenv>=1.0.0` - 环境变量管理

### 2. 配置API密钥

复制 `.env.example` 为 `.env` 并配置API信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE_URL=https://your-api-endpoint.com
```

**注意**：工具使用 `gemma3:12b` 模型进行翻译，确保您的API端点支持该模型。

## 使用方法

### 基本语法

```bash
python i18n_generator.py [选项]
```

### 命令行参数

- **`-s, --source`**: 源配置文件路径（默认：`messages.properties`）
- **`-l, --languages`**: 目标语言列表（默认：`['en']`）

### 支持的语言代码

| 语言代码 | 语言名称 | 语言代码 | 语言名称 |
|---------|---------|---------|----------|
| `en` | 英文 | `fr` | 法文 |
| `de` | 德文 | `ja` | 日文 |
| `ko` | 韩文 | `es` | 西班牙文 |
| `it` | 意大利文 | `pt` | 葡萄牙文 |
| `ru` | 俄文 | `ar` | 阿拉伯文 |

### 使用示例

#### 1. 使用默认参数
```bash
# 从 messages.properties 生成 messages_en.properties
python i18n_generator.py
```

#### 2. 指定源文件
```bash
# 从指定文件生成英文配置
python i18n_generator.py -s config.properties
```

#### 3. 生成多种语言配置
```bash
# 生成英文、法文、德文配置文件
python i18n_generator.py -l en fr de
```

#### 4. 指定源文件并生成多语言配置
```bash
# 从 app.properties 生成英文、日文、韩文配置
python i18n_generator.py -s app.properties -l en ja ko
```

#### 5. 生成所有支持的语言
```bash
# 生成所有支持的语言配置文件
python i18n_generator.py -l en fr de ja ko es it pt ru ar
```

## 工作流程

1. **解析源文件**：读取源配置文件中的所有键值对
2. **检查现有翻译**：扫描目标语言配置文件，识别已存在的翻译
3. **AI翻译**：对缺失的配置项调用AI模型进行翻译
4. **生成配置文件**：按照源文件顺序生成目标语言配置文件
5. **状态报告**：显示处理进度和成功率统计

## 输出格式

### 源文件示例 (messages.properties)
```properties
user.login.success=用户登录成功
user.login.failed=用户登录失败
data.save.success=数据保存成功
network.connection.failed=网络连接失败
```

### 生成的英文配置 (messages_en.properties)
```properties
user.login.success=User login successful
user.login.failed=User login failed
data.save.success=Data saved successfully
network.connection.failed=Network connection failed
```

### 生成的日文配置 (messages_ja.properties)
```properties
user.login.success=ユーザーログイン成功
user.login.failed=ユーザーログイン失敗
data.save.success=データ保存成功
network.connection.failed=ネットワーク接続失敗
```

## 高级功能

### 增量更新

如果目标语言配置文件已存在，工具会：
- 保留现有的翻译内容
- 只翻译新增的配置项
- 保持与源文件相同的键值对顺序

### 错误处理

- **API不可用**：当API密钥未配置或API调用失败时，返回原文并显示错误信息
- **文件不存在**：自动检查源文件是否存在，提供清晰的错误提示
- **网络超时**：设置30秒超时，避免长时间等待
- **翻译清理**：自动清理AI返回结果中的前缀文本

### 批量处理统计

工具会显示详细的处理统计信息：
```
任务完成! 成功生成 3/3 个语言配置文件
```

## 注意事项

1. **API配置**：确保 `.env` 文件中的API配置正确
2. **模型支持**：确认API端点支持 `gemma3:12b` 模型
3. **文件编码**：建议使用UTF-8编码保存配置文件
4. **备份建议**：在批量生成前建议备份现有配置文件
5. **网络连接**：确保网络连接稳定，避免翻译中断

## 故障排除

### 常见问题

**Q: 提示"未设置OPENAI_API_KEY"**
A: 检查 `.env` 文件是否存在且包含正确的API密钥

**Q: API请求失败**
A: 检查API端点URL是否正确，网络连接是否正常

**Q: 翻译质量不佳**
A: 可以调整提示词或尝试不同的AI模型

**Q: 生成的文件编码问题**
A: 确保系统支持UTF-8编码，或使用支持Unicode的文本编辑器

## 与 i18n_extractor.py 的配合使用

推荐的工作流程：

1. **提取字符串**：使用 `i18n_extractor.py` 从Java代码中提取硬编码字符串
   ```bash
   python i18n_extractor.py /path/to/project messages.properties
   ```

2. **生成翻译**：使用 `i18n_generator.py` 生成多语言配置文件
   ```bash
   python i18n_generator.py -s messages.properties -l en ja ko
   ```

3. **集成到项目**：将生成的配置文件集成到Spring Boot项目的资源目录中

## 许可证

本项目采用MIT许可证。