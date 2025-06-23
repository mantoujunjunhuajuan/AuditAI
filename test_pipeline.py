#!/usr/bin/env python3
"""
Simple test script to validate the complete AuditAI pipeline.
Usage: python test_pipeline.py [path_to_pdf_file]
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import create_pipeline

def test_pipeline_with_file(file_path: str):
    """Test the complete pipeline with a real PDF file."""
    
    print("🧪 AuditAI Pipeline 测试")
    print("=" * 50)
    
    # Validate file exists
    if not Path(file_path).exists():
        print(f"❌ 错误：文件 '{file_path}' 不存在")
        return False
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 错误：请设置 GEMINI_API_KEY 环境变量")
        print("💡 提示：在项目根目录创建 .env 文件，添加：")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    try:
        # Create pipeline
        print("🔧 初始化处理管道...")
        pipeline = create_pipeline()
        print("✅ 管道初始化成功")
        
        # Upload file to storage
        print(f"📤 上传文件: {Path(file_path).name}")
        file_name = Path(file_path).name
        destination = f"test_claims/{file_name}"
        file_uri = pipeline.storage_service.upload_file(file_path=file_path, destination=destination)
        print(f"✅ 文件已上传到: {file_uri}")
        
        # Run the pipeline
        print("\n🚀 开始执行完整的AI处理流程...")
        print("-" * 40)
        
        final_report = pipeline.run(file_uri)
        
        # Display results
        print("\n" + "="*50)
        print("📋 最终处理结果")
        print("="*50)
        print(final_report.report_content)
        
        print("\n✅ 管道执行完成！")
        return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function for the test script."""
    
    if len(sys.argv) > 1:
        # Use provided file path
        file_path = sys.argv[1]
    else:
        # Interactive mode
        print("📁 请输入要测试的PDF文件路径：")
        file_path = input("文件路径: ").strip()
        
        if not file_path:
            print("❌ 未提供文件路径")
            return
    
    # Run the test
    success = test_pipeline_with_file(file_path)
    
    if success:
        print("\n🎉 所有测试通过！")
        print("💡 您现在可以运行以下命令启动Web界面：")
        print("   streamlit run app/main.py")
    else:
        print("\n💥 测试失败，请检查错误信息并修复问题")
        sys.exit(1)

if __name__ == "__main__":
    main() 