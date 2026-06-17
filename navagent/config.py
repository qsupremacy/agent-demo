"""
环境变量配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM 配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 高德地图
AMAP_API_KEY = os.environ.get("AMAP_API_KEY")

# 华为云 Memory SDK
MEMORY_SPACE_ID = os.getenv("AGENTARTS_MEMORY_SPACE_ID")
MEMORY_API_KEY = os.getenv("HUAWEICLOUD_SDK_MEMORY_API_KEY")
