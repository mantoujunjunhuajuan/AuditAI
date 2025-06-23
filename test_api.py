#!/usr/bin/env python3
"""
Simple API test script to verify Gemini API connection.
"""

import os
from dotenv import load_dotenv
from services.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test basic Gemini API functionality."""
    
    print("🧪 测试 Gemini API 连接")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误：未找到 GEMINI_API_KEY 环境变量")
        print("💡 请在项目根目录创建 .env 文件，添加：")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"✅ API Key 已配置 (长度: {len(api_key)} 字符)")
    
    try:
        # Initialize client
        print("\n🔧 初始化 Gemini 客户端...")
        client = GeminiClient()
        
        # Test simple prompt
        print("\n🤖 测试简单的AI调用...")
        test_prompt = "请用中文回答：什么是人工智能？请用一句话简单解释。"
        
        response = client.generate_content(prompt=test_prompt)
        
        print(f"✅ API 调用成功！")
        print(f"📝 响应内容: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ API 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    
    if success:
        print("\n🎉 API 测试通过！")
        print("💡 现在可以运行完整的pipeline测试")
    else:
        print("\n�� API 测试失败，请检查配置") 