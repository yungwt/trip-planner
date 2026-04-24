"""LLM服务模块"""

from ..config import get_settings
from langchain_openai import ChatOpenAI
# 全局LLM实例
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """
    获取LLM实例(单例模式)
    
    Returns:
        LLM实例
    """
    global _llm_instance
    
    if _llm_instance is None:
        settings = get_settings()
        
        _llm_instance = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            temperature=0.7
        )
        
        print(f"✅ LLM服务初始化成功")
    
    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None

