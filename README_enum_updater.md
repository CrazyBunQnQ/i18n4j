# Java枚举国际化Key添加工具（优化版）

这个工具用于自动为Java枚举类添加国际化key，从properties文件中查找对应的翻译key并添加到枚举项中。

## 🆕 优化功能

### 智能字段识别
- **自动检测name字段位置**：支持不同枚举类中name字段在不同位置
- **中文字段优先**：优先识别包含中文的字段作为name字段
- **灵活参数解析**：支持复杂的参数结构和嵌套引号

### 支持多种枚举格式

**格式1：name字段在第1位**
```java
ONLINE("在线", 1, true)
// 更新为
ONLINE("在线", "common.status.online", 1, true)
```

**格式2：name字段在第4位**
```java
URL(1, "url", "url", "访问数")
// 更新为
URL(1, "url", "url", "访问数", "http.statistic.url")
```

**格式3：复杂参数结构**
```java
STATUS("ACTIVE", StatusType.NORMAL, "激活状态", true)
// 自动识别"激活状态"为name字段
```

## 文件说明

### 1. `java_enum_i18n_updater.py` - 完整版本
- 功能最全面的版本
- 需要在脚本中配置文件路径
- 包含详细的日志输出和错误处理
- 自动创建备份文件

### 2. `enum_updater_simple.py` - 简化版本
- 命令行参数版本，使用更灵活
- 轻量级实现
- 适合快速处理

## 使用方法

### 方法一：使用完整版本

1. 编辑 `java_enum_i18n_updater.py` 文件，修改以下路径：
```python
JAVA_ENUM_FILE = r"你的Java枚举文件路径"
MESSAGES_PROPERTIES_FILE = r"你的properties文件路径"
```

2. 运行脚本：
```bash
python java_enum_i18n_updater.py
```

### 方法二：使用简化版本

直接通过命令行参数运行：
```bash
python enum_updater_simple.py <java文件路径> <properties文件路径>
```

示例：
```bash
python enum_updater_simple.py Dictionary.java messages.properties
```

## 转换示例

**原始枚举项：**
```java
ONLINE("在线", 1),
OFFLINE("离线", 0),
HOST(7, "host", "host", "host"),
```

**转换后：**
```java
ONLINE("在线", 1, "common.common-facade.online"),
OFFLINE("离线", 0, "common.common-facade.offline"),
HOST(7, "host", "host", "host", "http.statistic.host"),
```

## 处理逻辑

1. **读取properties文件**：解析所有key-value对
2. **解析Java枚举**：提取每个枚举项的name值
3. **匹配查找**：在properties中查找value等于枚举name的key
4. **更新枚举**：将找到的key作为新字段添加到枚举项的最后
5. **备份原文件**：自动创建.backup备份文件
6. **写入更新**：保存修改后的Java文件

## 支持的枚举格式

脚本可以处理以下格式的Java枚举：

```java
// 单参数
ONLINE("在线")

// 多参数
ONLINE("在线", 1, true)

// 带注释
ONLINE("在线", // 在线状态
       1, 
       true)
```

## 注意事项

1. **备份**：脚本会自动创建备份文件，原文件安全
2. **编码**：确保Java和properties文件都是UTF-8编码
3. **格式**：枚举项必须符合标准Java枚举格式
4. **权限**：确保脚本有读写目标文件的权限

## 示例输出

```
Java枚举类国际化key添加工具
==================================================
读取properties文件: messages.properties
✓ 加载了 150 个properties条目

读取Java枚举文件: Dictionary.java
✓ 找到 5 个枚举项

找到的枚举项:
  - ONLINE: '在线'
  - OFFLINE: '离线'
  - PENDING: '待处理'
  - COMPLETED: '已完成'
  - FAILED: '失败'

开始处理枚举项...
✓ 更新枚举项 ONLINE: 添加key 'common.status.online'
✓ 更新枚举项 OFFLINE: 添加key 'common.status.offline'
- 枚举项 PENDING ('待处理'): 未找到匹配的key
✓ 更新枚举项 COMPLETED: 添加key 'common.status.completed'
- 枚举项 FAILED ('失败'): 未找到匹配的key

✓ 已创建备份文件: Dictionary.java.backup
✓ 成功更新Java文件
✓ 共更新了 3 个枚举项

处理完成!
```

## 故障排除

### 常见问题

1. **找不到文件**
   - 检查文件路径是否正确
   - 确保文件存在且可访问

2. **没有找到枚举项**
   - 检查Java文件格式是否标准
   - 确保枚举项使用双引号包围字符串

3. **没有匹配的key**
   - 检查properties文件中是否存在对应的value
   - 确保value完全匹配（区分大小写）

4. **编码问题**
   - 确保所有文件都是UTF-8编码
   - 检查中文字符是否正确显示

### 调试建议

1. 先用小的测试文件验证功能
2. 检查备份文件确认原文件安全
3. 逐步处理，避免一次性处理大量文件

## 新功能特性（v2.1）

### 新字段添加模式

从v2.1版本开始，脚本采用**新字段添加模式**，具有以下特点：

- **非侵入式添加**：在枚举项最后添加新字段，不修改现有参数
- **保持原有结构**：完全保留原始枚举项的参数顺序和格式
- **扩展性友好**：添加的国际化key作为独立字段，便于后续使用

### 对比说明

**旧版本（替换模式）**：
```java
// 原始
HOST(7, "host", "host", "host")
// 修改后（在name字段后插入）
HOST(7, "host", "http.statistic.host", "host", "host")
```

**新版本（追加模式）**：
```java
// 原始
HOST(7, "host", "host", "host")
// 修改后（在最后添加新字段）
HOST(7, "host", "host", "host", "http.statistic.host")
```

### 优势

1. **向后兼容**：不破坏现有的枚举结构
2. **易于理解**：新字段明确表示国际化key
3. **便于维护**：原有逻辑不受影响
4. **灵活扩展**：可以继续添加更多字段