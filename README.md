# 🌍 AI智能旅行规划助手

基于 LangChain + MCP 协议构建的智能旅行规划助手，集成高德地图服务，通过多智能体协作生成个性化旅行计划。

## ✨ 功能特点

- 🤖 **多智能体协作**: 景点搜索、天气查询、酒店推荐三个Agent并行工作，大幅提升响应速度
- 🗺️ **高德地图集成**: 通过MCP协议接入高德地图服务，实时获取POI、天气信息
- 🧠 **LangChain驱动**: 基于LangChain框架的Agent实现，支持Function Calling
- 🎨 **现代化前端**: Vue3 + TypeScript + Ant Design Vue，响应式设计
- 📱 **完整功能**: 包含住宿推荐、交通规划、餐饮建议和景点游览时间

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI + LangChain
- **Agent**: LangChain create_agent
- **MCP协议**: langchain-mcp-adapters
- **地图服务**: amap-mcp-server (高德地图)
- **LLM**: 支持OpenAI、通义千问等（OpenAI兼容接口）

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design Vue
- **地图服务**: 高德地图 JavaScript API
- **HTTP客户端**: Axios

## 📁 项目结构

```
helloagents-trip-planner/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── agents/            # Agent实现
│   │   │   └── trip_planner_agent.py  # 多智能体核心
│   │   ├── api/               # FastAPI路由
│   │   │   ├── main.py        # 应用入口
│   │   │   └── routes/
│   │   │       ├── trip.py    # 旅行规划API
│   │   │       └── poi.py     # POI图片API
│   │   ├── services/          # 服务层
│   │   │   ├── llm_service.py # LLM服务
│   │   │   └── unsplash_service.py  # 图片服务
│   │   ├── models/            # 数据模型
│   │   │   └── schemas.py
│   │   └── config.py          # 配置管理
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── services/          # API服务
│   │   ├── types/             # TypeScript类型
│   │   └── views/             # 页面视图
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 前提条件

- Python 3.10+
- Node.js 16+
- 高德地图API密钥（Web服务API + Web端JS API）
- LLM API密钥（通义千问/OpenAI等）

### 后端安装

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
conda create -n your_env_name python=3.10
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入你的API密钥
```

5. 启动后端服务
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端安装

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 配置环境变量
```bash
# 创建.env文件，填入高德地图Web端JS API Key
cp .env.example .env
```

4. 启动开发服务器
```bash
npm run dev
```

5. 打开浏览器访问 `http://localhost:5173`

## 📝 使用指南

1. **填写旅行信息**
   - 目的地城市
   - 旅行日期和天数
   - 交通方式偏好
   - 住宿类型偏好
   - 旅行风格标签

2. **生成计划**
   - 点击"生成旅行计划"按钮
   - 系统并行执行景点搜索、天气查询、酒店推荐
   - 整合信息生成完整行程

3. **查看结果**
   - 每日详细行程
   - 景点信息与地图标记
   - 天气预报
   - 餐饮推荐
   - 预算估算


## 🧠 智能体设计

| Agent | 职责 | 工具 |
|-------|------|------|
| 景点搜索Agent | 搜索城市景点 | amap_maps_text_search |
| 天气查询Agent | 查询天气信息 | maps_weather |
| 酒店推荐Agent | 搜索酒店 | amap_maps_text_search |
| 行程规划Agent | 整合生成计划 | 无（纯LLM） |

## 📊 性能优化

- **并行执行**: 三个独立Agent并发调用，节省50-70%时间
- **异步处理**: 全异步架构，支持高并发
- **MCP协议**: 标准化工具调用，易于扩展
