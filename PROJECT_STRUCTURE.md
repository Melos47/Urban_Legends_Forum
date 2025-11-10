# 📁 项目文件说明

## 核心应用文件

| 文件 | 说明 | 作用 |
|------|------|------|
| `app.py` | 主应用程序 | Flask 服务器，路由处理，用户认证 |
| `ai_engine.py` | AI 生成引擎 | 调用 LM Studio 生成故事和回复 |
| `story_engine.py` | 故事状态引擎 | 管理故事状态转换和证据生成 |
| `scheduler_tasks.py` | 定时任务 | 自动生成故事、更新状态 |
| `manual_generate_story.py` | 手动测试工具 | 手动触发故事生成（测试用） |

## 配置文件

| 文件 | 说明 |
|------|------|
| `.env` | 环境配置（包含密钥，不提交到 Git） |
| `.env.example` | 环境配置模板 |
| `requirements.txt` | Python 依赖包列表 |

## 文档文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目说明和使用指南 |
| `LM_STUDIO_503_FIX.md` | LM Studio 503 错误解决方案 |

## 前端文件

| 文件 | 说明 |
|------|------|
| `index.html` | 主页面模板 |
| `static/` | 静态资源（CSS, JS, 图片） |

## 数据文件

| 文件/目录 | 说明 |
|-----------|------|
| `instance/` | SQLite 数据库存储目录 |
| `generated/` | AI 生成的图片和音频文件 |

## 快速启动

```bash
# 1. 启动 LM Studio
# 在 LM Studio 中加载模型并启动本地服务器

# 2. 启动应用
.venv/bin/python app.py

# 3. 访问
# http://127.0.0.1:5001
```

## 测试工具

```bash
# 手动生成一个故事
.venv/bin/python manual_generate_story.py
```

## 文件清理记录

**已删除的测试文件**（2024-11-10）:
- ~~check_lm_studio.py~~ - LM Studio 检查工具
- ~~debug_openai_client.py~~ - OpenAI 客户端调试
- ~~debug_test.py~~ - 调试测试
- ~~diagnose_lm_studio.py~~ - LM Studio 诊断
- ~~setup_lm_studio.py~~ - LM Studio 设置
- ~~switch_to_local.py~~ - 切换到本地模型
- ~~test_features.py~~ - 功能测试
- ~~test_headers.py~~ - HTTP 请求头测试
- ~~test_lm_studio.py~~ - LM Studio 测试
- ~~test_requests.py~~ - requests 库测试
- ~~test_subprocess_curl.py~~ - subprocess curl 测试

**已删除的冗余文档**:
- ~~FIXES_SUMMARY.md~~ - 修复总结（内容已整合）
- ~~LM_STUDIO_FIXES.md~~ - LM Studio 修复（已过时）
- ~~LM_STUDIO_SETUP.md~~ - LM Studio 设置（已过时）
- ~~MODEL_SOLUTION.md~~ - 模型解决方案（已过时）
- ~~TESTING_GUIDE.md~~ - 测试指南（已过时）

**保留原因**:
- 只保留最新、最完整的文档
- 移除所有临时测试脚本
- 保持项目结构清晰简洁
