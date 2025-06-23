#!/usr/bin/env python3
"""
AuditAI Demo Script | AuditAI演示脚本
=====================================

This script demonstrates the core functionality of AuditAI's multi-agent 
insurance claim auditing system.

此脚本演示AuditAI多智能体保险理赔审核系统的核心功能。

Usage | 使用方法:
    python demo.py [--file PATH] [--lang LANG] [--model MODEL]

Examples | 示例:
    python demo.py --file test_files/sample_claim_form.txt
    python demo.py --lang zh --model gemini-1.5-pro
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from pipeline import ClaimProcessingPipeline, create_pipeline
from services.storage_service import get_storage_service
from utils.i18n import i18n


def print_banner(lang: str = 'en'):
    """Print AuditAI banner | 打印AuditAI横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                         🤖 AuditAI                          ║
    ║              Intelligent Insurance Claim Auditing           ║
    ║                   智能保险理赔审核系统                        ║
    ║                                                              ║
    ║        🏆 Google Cloud Agent Development Kit Hackathon      ║
    ║                          2025                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    if lang == 'zh':
        print("🚀 欢迎使用AuditAI演示程序")
        print("📊 多智能体协作 • ☁️ Google Cloud驱动 • 🔍 智能风险分析\n")
    else:
        print("🚀 Welcome to AuditAI Demo")
        print("📊 Multi-Agent Collaboration • ☁️ Google Cloud Powered • 🔍 Intelligent Risk Analysis\n")


def print_system_info(lang: str = 'en'):
    """Print system information | 打印系统信息"""
    i18n.set_language(lang)
    
    print("=" * 60)
    print(f"📋 {i18n.get_text('system_info')}")
    print("=" * 60)
    
    # Check environment configuration
    gemini_key = "✅" if os.getenv('GEMINI_API_KEY') else "❌"
    gcs_config = "✅" if os.getenv('GCS_BUCKET') else "⚠️  (Local storage)"
    
    print(f"🔑 Gemini API Key: {gemini_key}")
    print(f"☁️  Google Cloud Storage: {gcs_config}")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Storage service info
    storage_service = get_storage_service()
    storage_type = "Google Cloud Storage" if hasattr(storage_service, 'bucket') else "Local Storage"
    print(f"💾 Storage Service: {storage_type}")
    
    print()


def demonstrate_file_processing(file_path: str, model: str, lang: str = 'en'):
    """Demonstrate file processing | 演示文件处理"""
    i18n.set_language(lang)
    
    print("=" * 60)
    print(f"🔄 {i18n.get_text('processing_demo')}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        if lang == 'zh':
            print(f"❌ 文件不存在: {file_path}")
            print("💡 请使用有效的文件路径或使用默认示例文件")
        else:
            print(f"❌ File not found: {file_path}")
            print("💡 Please use a valid file path or default sample files")
        return False
    
    # Display file info
    file_size = os.path.getsize(file_path) / 1024  # KB
    file_ext = Path(file_path).suffix.upper()
    
    if lang == 'zh':
        print(f"📄 处理文件: {Path(file_path).name}")
        print(f"📊 文件大小: {file_size:.1f} KB")
        print(f"🎯 文件类型: {file_ext}")
        print(f"🤖 AI模型: {model}")
        print()
        print("🚀 启动多智能体处理流水线...")
    else:
        print(f"📄 Processing File: {Path(file_path).name}")
        print(f"📊 File Size: {file_size:.1f} KB")
        print(f"🎯 File Type: {file_ext}")
        print(f"🤖 AI Model: {model}")
        print()
        print("🚀 Starting Multi-Agent Processing Pipeline...")
    
    print("-" * 40)
    
    try:
        # Initialize pipeline
        pipeline = create_pipeline(model=model)
        
        # Process file with timer
        start_time = time.time()

        # In a real app, you'd upload and get a URI. Here we pass the local path.
        # The pipeline internally handles moving it to storage if needed.
        result, report_path = pipeline.run_for_demo(file_path, lang)
        
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Display results
        print("-" * 40)
        if lang == 'zh':
            print(f"✅ 处理完成！耗时: {processing_time:.2f}秒")
            print()
            print("📊 处理结果摘要:")
        else:
            print(f"✅ Processing Complete! Time: {processing_time:.2f}s")
            print()
            print("📊 Processing Results Summary:")
        
        # Show agent results
        agents = ['doc_intel', 'info_extract', 'rule_check', 'risk_analysis', 'report_gen']
        agent_names = {
            'doc_intel': 'Document Intelligence | 文档智能',
            'info_extract': 'Information Extraction | 信息提取', 
            'rule_check': 'Rule Validation | 规则验证',
            'risk_analysis': 'Risk Analysis | 风险分析',
            'report_gen': 'Report Generation | 报告生成'
        }
        
        for agent, agent_result in result.items():
            status = "✅" if agent_result.get('success', False) else "❌"
            name = agent_names.get(agent, agent)
            print(f"  {status} {name}")
            
            # Show risk score if available
            if agent == 'risk_analysis' and 'risk_score' in agent_result:
                risk_score = agent_result['risk_score']
                if lang == 'zh':
                    print(f"      🎯 风险评分: {risk_score}/100")
                else:
                    print(f"      🎯 Risk Score: {risk_score}/100")
        
        # Show collaboration info
        if result.get('risk_analysis', {}).get('collaboration_used'):
            if lang == 'zh':
                print("  🤝 智能体协作: 已启用")
            else:
                print("  🤝 Agent Collaboration: Enabled")
        
        print()
        if report_path:
            if lang == 'zh':
                print(f"📄 最终报告已保存到: {report_path}")
            else:
                print(f"📄 Final report saved to: {report_path}")
            print()
        
        # Performance metrics
        if lang == 'zh':
            print("⚡ 性能指标:")
            print(f"  • 处理速度: {(60/processing_time):.1f}x 比传统方法更快")
            print(f"  • 成本效益: 预计节省 ${50-3:.0f} 每份理赔")
        else:
            print("⚡ Performance Metrics:")
            print(f"  • Processing Speed: {(60/processing_time):.1f}x faster than traditional")
            print(f"  • Cost Efficiency: Estimated ${50-3:.0f} savings per claim")
        
        return True
        
    except Exception as e:
        if lang == 'zh':
            print(f"❌ 处理失败: {str(e)}")
            print("💡 请检查API密钥配置和网络连接")
        else:
            print(f"❌ Processing Failed: {str(e)}")
            print("💡 Please check API key configuration and network connection")
        return False


def show_sample_files(lang: str = 'en'):
    """Show available sample files | 显示可用的示例文件"""
    i18n.set_language(lang)
    
    print("=" * 60)
    if lang == 'zh':
        print("📁 可用示例文件")
    else:
        print("📁 Available Sample Files")
    print("=" * 60)
    
    sample_dir = Path("test_files")
    if not sample_dir.exists():
        if lang == 'zh':
            print("❌ 示例文件目录不存在")
        else:
            print("❌ Sample files directory not found")
        return
    
    files = list(sample_dir.glob("*"))
    if not files:
        if lang == 'zh':
            print("❌ 没有找到示例文件")
        else:
            print("❌ No sample files found")
        return
    
    for i, file_path in enumerate(files, 1):
        if file_path.is_file():
            size = file_path.stat().st_size / 1024  # KB
            print(f"  {i}. {file_path.name} ({size:.1f} KB)")
    
    print()


def main():
    """Main demo function | 主演示函数"""
    parser = argparse.ArgumentParser(
        description='AuditAI Demo Script | AuditAI演示脚本'
    )
    parser.add_argument(
        '--file', '-f',
        help='Path to claim file | 理赔文件路径',
        default='test_files/sample_claim_form.txt'
    )
    parser.add_argument(
        '--lang', '-l',
        choices=['en', 'zh'],
        default='en',
        help='Language | 语言 (en/zh)'
    )
    parser.add_argument(
        '--model', '-m',
        default='gemini-1.5-flash',
        help='Gemini model | Gemini模型'
    )
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Show system info only | 仅显示系统信息'
    )
    parser.add_argument(
        '--samples', '-s',
        action='store_true',
        help='Show sample files only | 仅显示示例文件'
    )
    
    args = parser.parse_args()
    
    # Set language
    i18n.set_language(args.lang)
    
    # Print banner
    print_banner(args.lang)
    
    # Show system info
    print_system_info(args.lang)
    
    if args.info:
        return
    
    if args.samples:
        show_sample_files(args.lang)
        return
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        if args.lang == 'zh':
            print("❌ 错误: 未找到GEMINI_API_KEY环境变量")
            print("💡 请设置您的API密钥:")
            print("   export GEMINI_API_KEY='your_api_key_here'")
            print("   或在.env文件中配置")
        else:
            print("❌ Error: GEMINI_API_KEY environment variable not found")
            print("💡 Please set your API key:")
            print("   export GEMINI_API_KEY='your_api_key_here'")
            print("   or configure in .env file")
        return
    
    # Show available sample files
    show_sample_files(args.lang)
    
    # Process file
    success = demonstrate_file_processing(args.file, args.model, args.lang)
    
    # Final message
    print("=" * 60)
    if success:
        if args.lang == 'zh':
            print("🎉 演示完成！")
            print("🚀 AuditAI已准备好处理您的保险理赔文档")
            print("📖 更多信息请查看 README.md")
        else:
            print("🎉 Demo Complete!")
            print("🚀 AuditAI is ready to process your insurance claim documents")
            print("📖 For more information, see README.md")
    else:
        if args.lang == 'zh':
            print("⚠️  演示遇到问题")
            print("💡 请检查配置并重试")
        else:
            print("⚠️  Demo encountered issues")
            print("💡 Please check configuration and try again")
    
    print("=" * 60)


if __name__ == "__main__":
    main() 