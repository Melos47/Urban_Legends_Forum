# LM Studio 配置指南

## 问题诊断

当前状态：
- ❌ LM Studio 连接超时（http://192.168.10.145:1234/v1）
- ⚠️  AI 回复使用模板（placeholder）而不是真实 AI 生成

## 解决方案

### 方案1: 本地运行 LM Studio（推荐）

如果你在本机运行 LM Studio：

1. **启动 LM Studio**
   - 打开 LM Studio 应用程序
   - 下载并加载一个模型（推荐 Qwen-7B 或 Llama-3.1-8B）

2. **启动服务器**
   - 在 LM Studio 中点击 "Local Server" 标签
   - 点击 "Start Server"
   - 确认端口是 `1234`（默认）

3. **修改配置**
   编辑 `.env` 文件：
   ```bash
   LM_STUDIO_URL=http://localhost:1234/v1
   ```

4. **测试连接**
   ```bash
   curl http://localhost:1234/v1/models
   ```
   应该返回已加载的模型列表

5. **重启服务**
   ```bash
   # 停止当前服务器（Ctrl+C）
   python app.py
   ```

### 方案2: 远程 LM Studio 服务器

如果 LM Studio 运行在远程机器（192.168.10.145）：

1. **确认远程服务器状态**
   - 登录到 192.168.10.145
   - 确认 LM Studio 正在运行
   - 确认服务器已启动（Start Server）

2. **检查防火墙**
   ```bash
   # 在远程机器上，确保端口 1234 开放
   # macOS
   sudo pfctl -s all | grep 1234
   
   # Linux
   sudo ufw allow 1234
   ```

3. **测试网络连接**
   ```bash
   # 在本机测试
   curl http://192.168.10.145:1234/v1/models
   
   # 如果超时，检查网络连通性
   ping 192.168.10.145
   ```

4. **LM Studio 配置**
   - 在 LM Studio 的 Server 设置中
   - 确保 "Bind to 0.0.0.0" 或 "Allow external connections"
   - 不要绑定到 127.0.0.1（仅本地）

### 方案3: 使用在线 API（备选）

如果无法使用 LM Studio，可以使用在线 API：

1. **OpenAI API**
   编辑 `.env`：
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   USE_ONLINE_API=true
   ```

2. **其他兼容 API**
   - DeepSeek
   - Anthropic Claude
   - 本地 Ollama（http://localhost:11434）

## 测试 AI 回复

修复后，测试是否正常工作：

```bash
# 方法1: 使用测试脚本
python -c "
from ai_engine import test_lm_studio_connection
test_lm_studio_connection()
"

# 方法2: 手动测试
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

## 预期结果

✅ 正常工作：
- LM Studio 响应时间 < 5 秒
- AI 回复不包含 "【楼主回复】" 模板格式
- 回复内容根据评论动态生成
- 回复长度 50-200 字

❌ 使用模板（需修复）：
- 回复格式："【楼主回复】刚去现场拍了照..."
- 内容与评论无关
- 固定的 8 个模板随机选择

## 当前代码逻辑

在 `ai_engine.py` 的 `generate_ai_response()` 函数中：

```python
try:
    # 尝试调用 LM Studio
    local_client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")
    response = local_client.chat.completions.create(
        model="local-model",  # LM Studio 自动使用已加载的模型
        messages=[...],
        temperature=0.8,
        max_tokens=200
    )
    # ✅ 返回 AI 生成的回复
    
except Exception as e:
    # ❌ LM Studio 失败，返回模板
    return random.choice(template_responses)
```

## 故障排除

### 问题1: "Connection refused"
- LM Studio 未启动 → 启动应用
- 服务器未开启 → 点击 "Start Server"

### 问题2: "Connection timeout"
- 远程服务器无响应 → 检查服务器状态
- 网络问题 → 测试 ping 和 curl
- 防火墙阻止 → 开放端口 1234

### 问题3: "Model not found"
- LM Studio 中未加载模型 → 下载并加载模型
- 模型加载中 → 等待加载完成（可能需要几分钟）

### 问题4: 响应很慢
- 模型太大 → 使用更小的模型（7B 或 8B）
- CPU 运行 → 建议使用 GPU
- 其他应用占用资源 → 关闭不必要的应用

## 推荐模型

适合都市传说生成的模型：

1. **Qwen2.5-7B-Instruct** （推荐）
   - 中文表现优秀
   - 创意性好
   - 速度快

2. **Llama-3.1-8B**
   - 平衡性能和质量
   - 支持中文
   - Meta 官方

3. **Mistral-7B**
   - 速度快
   - 资源占用低
   - 英文为主但支持中文

## 验证配置

运行完整诊断：

```bash
python debug_test.py
```

查看输出：
- ✅ LM Studio 服务器在线
- ✅ 可用模型数量: 1
- ✅ 生成的回复不是模板

## 需要帮助？

如果按照上述步骤仍无法解决：

1. 检查 LM Studio 控制台日志
2. 查看 Flask 应用日志（终端输出）
3. 运行 `python debug_test.py` 并发送完整输出
