# 翻译功能配置说明

代码生成器支持自动将中文分类名和字段名翻译为英文，以生成符合规范的 Kotlin 代码。

## 支持的翻译方式

按优先级顺序：

1. **翻译结果缓存** - 避免重复翻译相同文本
2. **微软翻译 API** - 推荐，更稳定、准确
3. **Google 翻译** - 免费，无需 API 密钥
4. **最小映射表** - 最后兜底方案

## 配置方式

### 方式一：微软翻译 API（推荐）

微软翻译 API 每月提供 **200 万字符的免费额度**，适合代码生成场景。

#### 获取 API 密钥

1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建新资源，选择"翻译器"服务
3. 选择合适的定价层（免费层即可）
4. 创建后，在"密钥和终结点"中获取：
   - **密钥（Key）** - 用于 `MICROSOFT_TRANSLATOR_KEY`
   - **区域（Location）** - 用于 `MICROSOFT_TRANSLATOR_REGION`（如 `eastasia`, `global` 等）

#### 配置环境变量

**Windows (PowerShell):**
```powershell
$env:MICROSOFT_TRANSLATOR_KEY = "你的密钥"
$env:MICROSOFT_TRANSLATOR_REGION = "eastasia"  # 可选，默认 global
```

**Windows (CMD):**
```cmd
set MICROSOFT_TRANSLATOR_KEY=你的密钥
set MICROSOFT_TRANSLATOR_REGION=eastasia
```

**Linux/macOS:**
```bash
export MICROSOFT_TRANSLATOR_KEY="你的密钥"
export MICROSOFT_TRANSLATOR_REGION="eastasia"
```

#### 永久配置（推荐）

**Windows:**
1. 打开"系统属性" > "环境变量"
2. 在"用户变量"中添加：
   - `MICROSOFT_TRANSLATOR_KEY` = `你的密钥`
   - `MICROSOFT_TRANSLATOR_REGION` = `eastasia`（可选）

**Linux/macOS:**
在 `~/.bashrc` 或 `~/.zshrc` 中添加：
```bash
export MICROSOFT_TRANSLATOR_KEY="你的密钥"
export MICROSOFT_TRANSLATOR_REGION="eastasia"
```

### 方式二：Google 翻译（无需配置）

Google 翻译无需 API 密钥，安装依赖后即可使用：

```bash
pip install googletrans==4.0.0rc1
```

**注意：**
- Google 翻译可能不稳定，受网络环境影响
- 如果无法访问 Google 服务，会自动回退到映射表

### 方式三：仅使用映射表

如果不想使用翻译 API，可以：

```python
from android_codegen.utils import translate_chinese_to_english

# 禁用翻译 API，仅使用映射表
result = translate_chinese_to_english("新接口", use_translation_api=False)
```

## 翻译结果示例

| 中文 | 英文翻译（API） | 映射表兜底 |
|------|----------------|------------|
| 新接口 | new_api | newapi |
| 用户信息 | user_info | item |
| 订单详情 | order_details | item |
| 应用配置 | app_config | app |

## 翻译缓存

为了提高效率，翻译结果会自动缓存到内存中。同一会话中重复翻译相同文本时，直接使用缓存结果，无需再次调用 API。

## 故障排查

### 微软翻译 API 不工作

1. 检查环境变量是否正确设置：
   ```bash
   echo $MICROSOFT_TRANSLATOR_KEY  # Linux/macOS
   echo %MICROSOFT_TRANSLATOR_KEY%  # Windows CMD
   $env:MICROSOFT_TRANSLATOR_KEY   # Windows PowerShell
   ```

2. 确认 API 密钥有效（未过期、未禁用）

3. 检查网络连接，确认可以访问 `api.cognitive.microsofttranslator.com`

4. 如果使用自定义端点，检查 `MICROSOFT_TRANSLATOR_ENDPOINT` 是否正确

### Google 翻译不工作

1. 确认已安装 `googletrans`：
   ```bash
   pip list | grep googletrans
   ```

2. 检查网络连接，确认可以访问 Google 服务

3. 如果网络受限，建议使用微软翻译 API

### 翻译结果不理想

1. 翻译结果会自动清理（移除特殊字符、转为小写等）
2. 如果翻译失败，会使用最小映射表作为兜底
3. 映射表只包含最常用的几个词汇，大多数翻译依赖 API

## 免费额度说明

### 微软翻译 API
- **免费层**：每月 200 万字符
- **超出后**：按使用量计费（非常便宜，约 $10/100万字符）
- **适合场景**：代码生成、批量翻译

### Google 翻译
- 完全免费
- 无官方限制说明
- 可能受网络环境限制

## 最佳实践

1. **优先使用微软翻译 API**：更稳定、准确，免费额度充足
2. **配置环境变量**：避免在代码中硬编码密钥
3. **依赖缓存**：相同文本只翻译一次，提高效率
4. **测试翻译结果**：首次使用前，建议测试几个关键词的翻译结果
