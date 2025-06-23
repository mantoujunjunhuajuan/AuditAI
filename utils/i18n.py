"""国际化(i18n)工具模块 - 支持中英文切换"""

import json
from typing import Dict, Any
import streamlit as st

class I18nManager:
    """多语言管理器"""
    
    def __init__(self):
        self.translations = {
            "zh": {
                # 页面标题和主要信息
                "page_title": "AuditAI – 智能保险理赔审核系统",
                "page_description": """
                上传保险理赔文档（PDF格式）开始自动化分析。
                系统将提取信息、检查一致性、评估风险，并生成最终的审核报告。
                """,
                "processing_steps": {
                    "title": "**处理流程：**",
                    "step1": "1. 📄 文档智能分析",
                    "step2": "2. 🔍 信息结构化提取",
                    "step3": "3. 📋 规则验证检查",
                    "step4": "4. 🤝 智能体协作风险分析",
                    "step5": "5. 📊 生成最终报告"
                },
                
                # API配置
                "api_config": {
                    "title": "🔑 API 配置",
                    "warning": "⚠️ 请先配置 GEMINI_API_KEY 环境变量，或在项目根目录创建 .env 文件",
                    "success": "✅ API 密钥已配置",
                    "info": "💡 获取API密钥：访问 https://aistudio.google.com/"
                },
                
                # 文件上传
                "file_upload": {
                    "label": "选择理赔文档进行分析",
                    "info": "📄 文件: {filename} ({size:.2f} MB)",
                    "button": "🚀 开始智能审核",
                    "error_no_key": "❌ 请先配置 GEMINI_API_KEY 环境变量",
                    "help_text": "支持格式: PDF文档、医疗影像(JPEG/PNG/TIFF/DICOM)、医疗报告(DOCX/DOC)"
                },
                
                # 处理进度
                "processing": {
                    "initializing": "🔧 初始化AI处理管道...",
                    "uploading": "📤 上传文件到存储服务...",
                    "uploaded": "✅ 文件已上传: {filename}",
                    "progress_title": "🔄 处理进度",
                    "doc_analysis": "📄 执行文档智能分析...",
                    "info_extraction": "🔍 提取结构化信息...",
                    "rule_validation": "📋 执行规则验证...",
                    "risk_analysis": "🤝 智能风险分析 (多Agent协作)...",
                    "report_generation": "📊 生成最终报告...",
                    "completed": "🎉 处理完成！"
                },
                
                # 步骤状态
                "steps": {
                    "pending": "⏸️",
                    "processing": "⏳",
                    "completed": "✅",
                    "doc_analysis": "文档分析",
                    "info_extraction": "信息提取",
                    "rule_check": "规则检查",
                    "risk_analysis": "风险分析",
                    "report_generation": "报告生成"
                },
                
                # 指标卡片
                "metrics": {
                    "risk_score": "📊 风险评分",
                    "processing_priority": "🚀 处理优先级",
                    "siu_investigation": "🔍 SIU调查",
                    "final_recommendation": "📋 最终建议",
                    "high_risk": "高风险",
                    "medium_risk": "中等风险",
                    "low_risk": "低风险",
                    "critical_risk": "严重风险",
                    "auto_approve": "自动审批",
                    "manual_review": "人工审核",
                    "needed": "需要",
                    "not_needed": "不需要",
                    "fraud_indicators": "欺诈指标",
                    "confidence": "置信度"
                },
                
                # 标签页
                "tabs": {
                    "final_report": "📋 最终报告",
                    "fraud_analysis": "🚨 欺诈分析",
                    "extracted_info": "📄 提取信息",
                    "detailed_analysis": "🔍 详细分析",
                    "technical_details": "🛠️ 技术详情"
                },
                
                # 欺诈分析
                "fraud_analysis": {
                    "title": "🚨 欺诈检测与风险分析",
                    "expedited_processing": "🚀 **快速处理通道** - 低风险，符合自动审批条件",
                    "enhanced_review": "⚠️ **增强审核要求** - 高风险，需要详细调查",
                    "standard_processing": "📋 **标准处理流程** - 中等风险，常规审核",
                    "siu_required": "🚨 **SIU调查推荐**",
                    "siu_description": "需要特殊调查单位介入",
                    "no_siu": "✅ **无需SIU调查**",
                    "auto_approve_eligible": "⚡ **自动审批合格**",
                    "auto_approve_description": "符合快速审批条件",
                    "manual_review_required": "👤 **需人工审核**",
                    "manual_review_description": "不符合自动审批条件",
                    "fraud_indicators": "**🔍 欺诈风险指标:**",
                    "no_fraud_detected": "✅ 未检测到欺诈指标",
                    "settlement_estimate": "**💰 预估理赔金额:**"
                },
                
                # 详细分析
                "detailed_analysis": {
                    "title": "🔍 详细分析结果",
                    "rule_validation": "**规则验证结果:**",
                    "all_rules_passed": "✅ 所有规则验证通过",
                    "risk_factors": "**风险因素分析:**",
                    "no_risk_factors": "✅ 未发现风险因素",
                    "next_actions": "**📋 建议后续行动:**"
                },
                
                # 技术详情
                "technical_details": {
                    "title": "🛠️ 技术处理详情",
                    "document_type": "文档类型",
                    "content_length": "内容长度",
                    "validation_status": "验证状态",
                    "risk_score": "风险评分",
                    "processing_model": "处理模型",
                    "file_uri": "文件URI",
                    "characters": "字符"
                },
                
                # 页脚
                "footer": "🤖 AuditAI - 智能保险理赔审核系统 | 基于多代理AI架构构建",
                
                # 错误信息
                "errors": {
                    "processing_error": "❌ 处理过程中发生错误: {error}",
                    "initialization_error": "❌ 初始化失败: {error}"
                },
                
                # 语言切换
                "language": {
                    "switch_to_english": "🇺🇸 English",
                    "switch_to_chinese": "🇨🇳 中文"
                },
                
                # 存储服务
                "storage": {
                    "gcs_title": "☁️ Google Cloud Storage",
                    "gcs_bucket": "📦 存储桶: `{bucket}`",
                    "gcs_description": "*文件将安全存储在Google云端*",
                    "gcs_trial_title": "☁️ Google Cloud Storage",
                    "gcs_trial_description": "*云端安全存储，全球可访问*",
                    "local_title": "📁 本地存储",
                    "local_description": "*文件存储在本地（开发模式）*",
                    "uploaded_to_gcs": "✅ 文件已上传至 Google Cloud Storage",
                    "gcs_location": "☁️ 存储位置: `{location}`",
                    "powered_by_gcp": "*🌟 基于Google Cloud基础设施*"
                },
                
                # 协作功能
                "collaboration": {
                    "agent_collaboration": "🤝 智能体协作中...",
                    "collaboration_triggered": "🤝 协作机制已触发",
                    "requesting_collaboration": "📞 请求协作分析...",
                    "collaboration_success": "✅ 协作分析成功",
                    "collaboration_failed": "❌ 协作分析失败",
                    "enhanced_analysis": "🔬 增强分析结果",
                    "collaborative_insights": "🤝 协作洞察",
                    "multi_agent_network": "🕸️ 多智能体网络"
                }
            },
            
            "en": {
                # 页面标题和主要信息
                "page_title": "AuditAI – Intelligent Insurance Claim Auditing System",
                "page_description": """
                Upload insurance claim documents (PDF format) to start automated analysis.
                The system will extract information, check consistency, assess risks, and generate final audit reports.
                """,
                "processing_steps": {
                    "title": "**Processing Pipeline:**",
                    "step1": "1. 📄 Document Intelligence Analysis",
                    "step2": "2. 🔍 Structured Information Extraction",
                    "step3": "3. 📋 Rule Validation Check",
                    "step4": "4. 🤝 Multi-Agent Collaborative Risk Analysis",
                    "step5": "5. 📊 Final Report Generation"
                },
                
                # API配置
                "api_config": {
                    "title": "🔑 API Configuration",
                    "warning": "⚠️ Please configure GEMINI_API_KEY environment variable or create .env file in project root",
                    "success": "✅ API key configured",
                    "info": "💡 Get API key: Visit https://aistudio.google.com/"
                },
                
                # 文件上传
                "file_upload": {
                    "label": "Choose claim document for analysis",
                    "info": "📄 File: {filename} ({size:.2f} MB)",
                    "button": "🚀 Start Intelligent Review",
                    "error_no_key": "❌ Please configure GEMINI_API_KEY environment variable first",
                    "help_text": "Supported formats: PDF documents, Medical imaging (JPEG/PNG/TIFF/DICOM), Medical reports (DOCX/DOC)"
                },
                
                # 处理进度
                "processing": {
                    "initializing": "🔧 Initializing AI processing pipeline...",
                    "uploading": "📤 Uploading file to storage service...",
                    "uploaded": "✅ File uploaded: {filename}",
                    "progress_title": "🔄 Processing Progress",
                    "doc_analysis": "📄 Executing document intelligence analysis...",
                    "info_extraction": "🔍 Extracting structured information...",
                    "rule_validation": "📋 Executing rule validation...",
                    "risk_analysis": "🤝 Intelligent Risk Analysis (Multi-Agent Collaboration)...",
                    "report_generation": "📊 Generating final report...",
                    "completed": "🎉 Processing completed!"
                },
                
                # 步骤状态
                "steps": {
                    "pending": "⏸️",
                    "processing": "⏳",
                    "completed": "✅",
                    "doc_analysis": "Document Analysis",
                    "info_extraction": "Info Extraction",
                    "rule_check": "Rule Check",
                    "risk_analysis": "Risk Analysis",
                    "report_generation": "Report Generation"
                },
                
                # 指标卡片
                "metrics": {
                    "risk_score": "📊 Risk Score",
                    "processing_priority": "🚀 Processing Priority",
                    "siu_investigation": "🔍 SIU Investigation",
                    "final_recommendation": "📋 Final Recommendation",
                    "high_risk": "High Risk",
                    "medium_risk": "Medium Risk",
                    "low_risk": "Low Risk",
                    "critical_risk": "Critical Risk",
                    "auto_approve": "Auto Approve",
                    "manual_review": "Manual Review",
                    "needed": "Required",
                    "not_needed": "Not Required",
                    "fraud_indicators": "Fraud Indicators",
                    "confidence": "Confidence"
                },
                
                # 标签页
                "tabs": {
                    "final_report": "📋 Final Report",
                    "fraud_analysis": "🚨 Fraud Analysis",
                    "extracted_info": "📄 Extracted Information",
                    "detailed_analysis": "🔍 Detailed Analysis",
                    "technical_details": "🛠️ Technical Details"
                },
                
                # 欺诈分析
                "fraud_analysis": {
                    "title": "🚨 Fraud Detection & Risk Analysis",
                    "expedited_processing": "🚀 **Expedited Processing** - Low risk, eligible for auto-approval",
                    "enhanced_review": "⚠️ **Enhanced Review Required** - High risk, detailed investigation needed",
                    "standard_processing": "📋 **Standard Processing** - Medium risk, routine review",
                    "siu_required": "🚨 **SIU Investigation Recommended**",
                    "siu_description": "Special Investigation Unit intervention required",
                    "no_siu": "✅ **No SIU Investigation Required**",
                    "auto_approve_eligible": "⚡ **Auto-Approval Eligible**",
                    "auto_approve_description": "Meets expedited approval criteria",
                    "manual_review_required": "👤 **Manual Review Required**",
                    "manual_review_description": "Does not meet auto-approval criteria",
                    "fraud_indicators": "**🔍 Fraud Risk Indicators:**",
                    "no_fraud_detected": "✅ No fraud indicators detected",
                    "settlement_estimate": "**💰 Estimated Settlement Amount:**"
                },
                
                # 详细分析
                "detailed_analysis": {
                    "title": "🔍 Detailed Analysis Results",
                    "rule_validation": "**Rule Validation Results:**",
                    "all_rules_passed": "✅ All rule validations passed",
                    "risk_factors": "**Risk Factor Analysis:**",
                    "no_risk_factors": "✅ No risk factors identified",
                    "next_actions": "**📋 Recommended Next Actions:**"
                },
                
                # 技术详情
                "technical_details": {
                    "title": "🛠️ Technical Processing Details",
                    "document_type": "Document Type",
                    "content_length": "Content Length",
                    "validation_status": "Validation Status",
                    "risk_score": "Risk Score",
                    "processing_model": "Processing Model",
                    "file_uri": "File URI",
                    "characters": "characters"
                },
                
                # 页脚
                "footer": "🤖 AuditAI - Intelligent Insurance Claim Auditing System | Built on Multi-Agent AI Architecture",
                
                # 错误信息
                "errors": {
                    "processing_error": "❌ Error occurred during processing: {error}",
                    "initialization_error": "❌ Initialization failed: {error}"
                },
                
                # 语言切换
                "language": {
                    "switch_to_english": "🇺🇸 English",
                    "switch_to_chinese": "🇨🇳 中文"
                },
                
                # 存储服务
                "storage": {
                    "gcs_title": "☁️ Google Cloud Storage",
                    "gcs_bucket": "📦 Bucket: `{bucket}`",
                    "gcs_description": "*Files stored securely in Google Cloud*",
                    "gcs_trial_title": "☁️ Google Cloud Storage",
                    "gcs_trial_description": "*Secure cloud storage with global accessibility*",
                    "local_title": "📁 Local Storage",
                    "local_description": "*Files stored locally (development mode)*",
                    "uploaded_to_gcs": "✅ File uploaded to Google Cloud Storage",
                    "gcs_location": "☁️ Storage Location: `{location}`",
                    "powered_by_gcp": "*🌟 Powered by Google Cloud Infrastructure*"
                },
                
                # 协作功能
                "collaboration": {
                    "agent_collaboration": "🤝 Agent Collaboration in Progress...",
                    "collaboration_triggered": "🤝 Collaboration Mechanism Triggered",
                    "requesting_collaboration": "📞 Requesting Collaborative Analysis...",
                    "collaboration_success": "✅ Collaborative Analysis Successful",
                    "collaboration_failed": "❌ Collaborative Analysis Failed",
                    "enhanced_analysis": "🔬 Enhanced Analysis Results",
                    "collaborative_insights": "🤝 Collaborative Insights",
                    "multi_agent_network": "🕸️ Multi-Agent Network"
                }
            }
        }
        
        # 初始化语言设置
        if 'language' not in st.session_state:
            st.session_state.language = 'zh'  # 默认中文
    
    def set_language(self, lang: str):
        """设置当前语言"""
        if lang in self.translations:
            st.session_state.language = lang
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return st.session_state.get('language', 'zh')
    
    def get_text(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        current_lang = self.get_current_language()
        
        # 支持嵌套键，如 "api_config.title"
        keys = key.split('.')
        text = self.translations[current_lang]
        
        try:
            for k in keys:
                text = text[k]
            
            # 支持格式化参数
            if kwargs:
                return text.format(**kwargs)
            return text
        except (KeyError, TypeError):
            # 如果找不到翻译，返回键名作为fallback
            return key
    
    def get_recommendation_text(self, recommendation: str) -> str:
        """获取推荐决策的翻译文本"""
        current_lang = self.get_current_language()
        
        recommendation_map = {
            "zh": {
                "approve": "批准",
                "deny": "拒绝",
                "manual_review": "人工审核",
                "siu_referral": "SIU调查",
                "expedited_approve": "快速批准"
            },
            "en": {
                "approve": "Approve",
                "deny": "Deny", 
                "manual_review": "Manual Review",
                "siu_referral": "SIU Referral",
                "expedited_approve": "Expedited Approve"
            }
        }
        
        return recommendation_map[current_lang].get(recommendation, recommendation)
    
    def get_priority_text(self, priority: str) -> str:
        """获取处理优先级的翻译文本"""
        current_lang = self.get_current_language()
        
        priority_map = {
            "zh": {
                "Expedited": "快速处理",
                "Standard": "标准处理",
                "Enhanced_Review": "增强审核"
            },
            "en": {
                "Expedited": "Expedited",
                "Standard": "Standard",
                "Enhanced_Review": "Enhanced Review"
            }
        }
        
        return priority_map[current_lang].get(priority, priority)

# 创建全局实例
i18n = I18nManager() 
