"""多智能体旅行规划系统"""

import asyncio
import json
from typing import Dict, Any, List
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from ..services.llm_service import get_llm
from ..models.schemas import TripRequest, TripPlan, DayPlan, Attraction, Meal, Location
from ..config import get_settings

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
你必须使用工具来搜索景点!不要自己编造景点信息!

"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
你必须使用工具来查询天气!不要自己编造天气信息!

"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。

**重要提示:**
你必须使用工具来搜索酒店!不要自己编造酒店信息!

"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息和天气信息,生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info数组必须包含每一天的天气信息
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**:
   - 景点门票价格(ticket_price)
   - 餐饮预估费用(estimated_cost)
   - 酒店预估费用(estimated_cost)
   - 预算汇总(budget)包含各项总费用
"""


class MultiAgentTripPlanner:
    """多智能体旅行规划系统"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统...")

        try:
            settings = get_settings()
            self.llm = get_llm()

            # 保存配置，供异步初始化使用
            self.amap_api_key = settings.amap_api_key
            # 异步初始化标志
            self._initialized = False
            self.tools = None
            self.attraction_agent = None
            self.weather_agent = None
            self.hotel_agent = None
            self.planner_agent = None
            
            # 创建行程规划Agent(不需要工具，可以同步创建)
            print("  - 创建行程规划Agent...")
            self.planner_agent = create_agent(
                self.llm, # 使用全局LLM实例
                [], #工具列表
                system_prompt=PLANNER_AGENT_PROMPT # 系统提示词
            )
            
            print(f"✅ 多智能体系统初始化成功（待异步加载工具）")
            
        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def ainitialize(self):
        """异步初始化工具和其他Agent"""
        if self._initialized:
            return
        
        print("  - 异步加载MCP工具...")
        
        # 配置 MCP 客户端
        self.mcp_client = MultiServerMCPClient({
            "amap": { # 服务器名称
                "command": "uvx", # 启动命令
                "args": ["amap-mcp-server"], # 命令参数
                "transport": "stdio", # 通信方式
                "env": {"AMAP_MAPS_API_KEY": self.amap_api_key}
            }
        })
        
        # 获取所有工具
        self.tools = await self.mcp_client.get_tools()
        
        # 创建景点搜索Agent
        print("  - 创建景点搜索Agent...")
        self.attraction_agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=ATTRACTION_AGENT_PROMPT
        )
        
        # 创建天气查询Agent
        print("  - 创建天气查询Agent...")
        self.weather_agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=WEATHER_AGENT_PROMPT
        )
        
        # 创建酒店推荐Agent
        print("  - 创建酒店推荐Agent...")
        self.hotel_agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=HOTEL_AGENT_PROMPT
        )
        
        self._initialized = True
        print(f"✅ MCP工具加载完成，共 {len(self.tools)} 个工具")
    
    async def plan_trip(self, request: TripRequest) -> TripPlan:
        """异步生成旅行计划"""
        await self.ainitialize()
        
        print(f"\n{'='*60}")
        print(f"🚀 开始多智能体协作规划旅行...")
        print(f"目的地: {request.city}")
        print(f"日期: {request.start_date} 至 {request.end_date}")
        print(f"天数: {request.travel_days}天")
        print(f"偏好: {', '.join(request.preferences) if request.preferences else '无'}")
        print(f"{'='*60}\n")

        attraction_query = self._build_attraction_query(request)
        weather_query = f"请查询{request.city}的天气信息"
        hotel_query = f"请搜索{request.city}的{request.accommodation}酒店"

        # 1.创建任务（注意：这里只是创建，还没有真正执行）
        attraction_task = self.attraction_agent.ainvoke({
            "messages": [("user", attraction_query)]
        })
        weather_task = self.weather_agent.ainvoke({
            "messages": [("user", weather_query)]
        })
        hotel_task = self.hotel_agent.ainvoke({
            "messages": [("user", hotel_query)]
        })
        
        # 2.并发执行所有任务，等待全部完成
        # asyncio.gather 会同时执行这三个任务，总耗时约等于最慢的那个
        results = await asyncio.gather(
            attraction_task,
            weather_task, 
            hotel_task,
            return_exceptions=True  # 即使某个失败，也不影响其他的
        )
        
        # 3. 处理结果
        attraction_result, weather_result, hotel_result = results
        
        # 检查是否有任务失败
        if isinstance(attraction_result, Exception):
            print(f"❌ 景点搜索失败: {attraction_result}")
            attraction_response = "无法获取景点信息"
        else:
            attraction_response = attraction_result["messages"][-1].content
            print(f"✅ 景点搜索完成 ({len(attraction_response)} 字符)")
        
        if isinstance(weather_result, Exception):
            print(f"❌ 天气查询失败: {weather_result}")
            weather_response = "无法获取天气信息"
        else:
            weather_response = weather_result["messages"][-1].content
            print(f"✅ 天气查询完成 ({len(weather_response)} 字符)")
        
        if isinstance(hotel_result, Exception):
            print(f"❌ 酒店搜索失败: {hotel_result}")
            hotel_response = "无法获取酒店信息"
        else:
            hotel_response = hotel_result["messages"][-1].content
            print(f"✅ 酒店搜索完成 ({len(hotel_response)} 字符)")
        
        print(f"\n✅ 所有并行任务完成，开始生成最终计划...\n")

        # 步骤4: 行程规划Agent整合信息生成计划
        print("📋 步骤4: 生成行程计划...")
        planner_query = self._build_planner_query(request, attraction_response, weather_response, hotel_response)
        result = await self.planner_agent.ainvoke({"messages": [("user", planner_query)]})
        planner_response = result["messages"][-1].content
        print(f"行程规划结果: {planner_response[:300]}...\n")

        # 解析最终计划
        trip_plan = self._parse_response(planner_response, request)

        print(f"{'='*60}")
        print(f"✅ 旅行计划生成完成!")
        print(f"{'='*60}\n")

        return trip_plan
    
    def _build_attraction_query(self, request: TripRequest) -> str:
        """构建景点搜索查询 - 直接包含工具调用"""
        keywords = []
        if request.preferences:
            # 只取第一个偏好作为关键词
            keywords = request.preferences[0]
        else:
            keywords = "景点"

        # 直接返回工具调用格式
        query = f"请使用工具搜索{request.city}的{keywords}相关景点"
        return query

    def _build_planner_query(self, request: TripRequest, attractions: str, weather: str, hotels: str = "") -> str:
        """构建行程规划查询"""
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

                    **基本信息:**
                    - 城市: {request.city}
                    - 日期: {request.start_date} 至 {request.end_date}
                    - 天数: {request.travel_days}天
                    - 交通方式: {request.transportation}
                    - 住宿: {request.accommodation}
                    - 偏好: {', '.join(request.preferences) if request.preferences else '无'}

                    **景点信息:**
                    {attractions}

                    **天气信息:**
                    {weather}

                    **酒店信息:**
                    {hotels}

                    **要求:**
                    1. 每天安排2-3个景点
                    2. 每天必须包含早中晚三餐
                    3. 每天推荐一个具体的酒店(从酒店信息中选择)
                    4. 考虑景点之间的距离和交通方式
                    5. 返回完整的JSON格式数据
                    6. 景点的经纬度坐标要真实准确
                """
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"

        return query
    
    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """
        解析Agent响应
        
        Args:
            response: Agent响应文本
            request: 原始请求
            
        Returns:
            旅行计划
        """
        try:
            # 尝试从响应中提取JSON
            # 查找JSON代码块
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                # 直接查找JSON对象
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("响应中未找到JSON数据")
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 转换为TripPlan对象
            trip_plan = TripPlan(**data)
            
            return trip_plan
            
        except Exception as e:
            print(f"⚠️  解析响应失败: {str(e)}")
            print(f"   将使用备用方案生成计划")
            return self._create_fallback_plan(request)
    
    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划(当Agent失败时)"""
        from datetime import datetime, timedelta
        
        # 解析日期
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        
        # 创建每日行程
        days = []
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)
            
            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(longitude=116.4 + i*0.01 + j*0.005, latitude=39.9 + i*0.01 + j*0.005),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            days.append(day_plan)
        
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程,建议提前查看各景点的开放时间。"
        )


# 全局多智能体系统实例
_multi_agent_planner = None


async def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例(单例模式)"""
    global _multi_agent_planner

    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()
        await _multi_agent_planner.ainitialize()
    return _multi_agent_planner
