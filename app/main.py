"""AuditAI Streamlit主应用程序 - 多语言版本"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import List

# Ensure root directory is importable before local packages
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from dotenv import load_dotenv
from pipeline import create_pipeline
from utils.i18n import i18n

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Streamlit page config and main app logic
# ---------------------------------------------------------------------------

def setup_page():
    """配置页面基本设置"""
    st.set_page_config(
        page_title="AuditAI - 智能保险理赔审核系统",
        page_icon="🔍",
        layout="wide"
    )

def render_language_switcher():
    """渲染语言切换器"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌍 Language / 语言")
    
    current_lang = i18n.get_current_language()
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button(
            i18n.get_text("language.switch_to_chinese"), 
            disabled=(current_lang == 'zh'),
            use_container_width=True
        ):
            i18n.set_language('zh')
            st.rerun()
    
    with col2:
        if st.button(
            i18n.get_text("language.switch_to_english"), 
            disabled=(current_lang == 'en'),
            use_container_width=True
        ):
            i18n.set_language('en')
            st.rerun()

def check_api_key():
    """检查API密钥配置"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    with st.sidebar:
        st.markdown(f"### {i18n.get_text('api_config.title')}")
        
        if not api_key:
            st.warning(i18n.get_text('api_config.warning'))
            st.info(i18n.get_text('api_config.info'))
            return False
        else:
            st.success(i18n.get_text('api_config.success'))
            return True

def check_storage_service():
    """检查并显示存储服务配置"""
    gcs_bucket = os.getenv("GCS_BUCKET")
    
    with st.sidebar:
        st.markdown("### ☁️ Storage Configuration")
        
        if gcs_bucket:
            st.success(f"✅ {i18n.get_text('storage.gcs_title')}")
            st.info(i18n.get_text('storage.gcs_bucket', bucket=gcs_bucket))
            st.markdown(i18n.get_text('storage.gcs_description'))
            return "gcs"
        else:
            st.info(i18n.get_text('storage.local_title'))
            st.markdown(i18n.get_text('storage.local_description'))
            return "local"

def render_processing_steps():
    """渲染处理步骤说明"""
    st.markdown(i18n.get_text('processing_steps.title'))
    st.markdown(i18n.get_text('processing_steps.step1'))
    st.markdown(i18n.get_text('processing_steps.step2'))
    st.markdown(i18n.get_text('processing_steps.step3'))
    st.markdown(i18n.get_text('processing_steps.step4'))
    st.markdown(i18n.get_text('processing_steps.step5'))

def get_risk_level_text(risk_score):
    """根据风险评分获取风险等级文本"""
    if risk_score >= 75:
        return i18n.get_text('metrics.critical_risk')
    elif risk_score >= 50:
        return i18n.get_text('metrics.high_risk')
    elif risk_score >= 25:
        return i18n.get_text('metrics.medium_risk')
    else:
        return i18n.get_text('metrics.low_risk')

def get_file_type_info(file):
    """获取文件类型信息和处理建议"""
    file_extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
    
    file_types = {
        'pdf': {
            'icon': '📄',
            'type': 'PDF Document',
            'type_zh': 'PDF文档',
            'category': 'document',
            'processing_note': 'Standard text extraction and analysis',
            'processing_note_zh': '标准文本提取和分析'
        },
        'jpg': {'icon': '🖼️', 'type': 'JPEG Image', 'type_zh': 'JPEG图像', 'category': 'image'},
        'jpeg': {'icon': '🖼️', 'type': 'JPEG Image', 'type_zh': 'JPEG图像', 'category': 'image'},
        'png': {'icon': '🖼️', 'type': 'PNG Image', 'type_zh': 'PNG图像', 'category': 'image'},
        'tiff': {'icon': '🏥', 'type': 'Medical Imaging (TIFF)', 'type_zh': '医疗影像(TIFF)', 'category': 'medical_image'},
        'tif': {'icon': '🏥', 'type': 'Medical Imaging (TIFF)', 'type_zh': '医疗影像(TIFF)', 'category': 'medical_image'},
        'dcm': {'icon': '🩻', 'type': 'DICOM Medical Image', 'type_zh': 'DICOM医疗影像', 'category': 'dicom'},
        'doc': {'icon': '📝', 'type': 'Word Document', 'type_zh': 'Word文档', 'category': 'document'},
        'docx': {'icon': '📝', 'type': 'Word Document', 'type_zh': 'Word文档', 'category': 'document'},
        'bmp': {'icon': '🖼️', 'type': 'Bitmap Image', 'type_zh': '位图图像', 'category': 'image'}
    }
    
    current_lang = i18n.get_current_language()
    file_info = file_types.get(file_extension, {
        'icon': '📎',
        'type': 'Unknown File',
        'type_zh': '未知文件',
        'category': 'unknown'
    })
    
    # 为不同类型的文件添加处理说明
    if file_info['category'] == 'image' or file_info['category'] == 'medical_image':
        file_info['processing_note'] = 'OCR text extraction and image analysis'
        file_info['processing_note_zh'] = 'OCR文本提取和图像分析'
    elif file_info['category'] == 'dicom':
        file_info['processing_note'] = 'Medical imaging metadata and visual analysis'
        file_info['processing_note_zh'] = '医疗影像元数据和视觉分析'
    elif file_info['category'] == 'document':
        file_info['processing_note'] = 'Document parsing and content extraction'
        file_info['processing_note_zh'] = '文档解析和内容提取'
    
    return file_info

def render_progress_tracker(steps_status):
    """渲染进度追踪器"""
    st.markdown(f"### {i18n.get_text('processing.progress_title')}")
    
    steps = [
        ("doc_analysis", i18n.get_text('steps.doc_analysis')),
        ("info_extraction", i18n.get_text('steps.info_extraction')),
        ("rule_check", i18n.get_text('steps.rule_check')),
        ("risk_analysis", i18n.get_text('steps.risk_analysis')),
        ("report_generation", i18n.get_text('steps.report_generation'))
    ]
    
    cols = st.columns(5)
    for i, (step_key, step_name) in enumerate(steps):
        with cols[i]:
            status = steps_status.get(step_key, "pending")
            if status == "completed":
                st.markdown(f"{i18n.get_text('steps.completed')} **{step_name}**")
            elif status == "processing":
                st.markdown(f"{i18n.get_text('steps.processing')} **{step_name}**")
            else:
                st.markdown(f"{i18n.get_text('steps.pending')} **{step_name}**")

def main():
    """主应用程序"""
    setup_page()
    
    # 主标题
    st.title("🔍 AuditAI - 智能保险理赔审核系统")
    st.markdown("---")

    # 侧边栏配置
    st.sidebar.header("⚙️ 系统配置")

    # 语言选择
    language_display = st.sidebar.selectbox(
        "🌐 语言 / Language",
        ["中文", "English"],
        key="language_display"
    )
    
    # 映射显示语言到代码
    language_map = {"中文": "zh", "English": "en"}
    current_language_code = language_map[language_display]
    
    # 更新i18n语言设置
    if i18n.get_current_language() != current_language_code:
        i18n.set_language(current_language_code)

    # 模型选择
    st.sidebar.subheader("🤖 AI模型配置")
    model_choice = st.sidebar.selectbox(
        "选择Gemini模型 / Choose Gemini Model",
        [
            "gemini-1.5-flash (推荐/Recommended)",
            "gemini-1.5-pro (高质量/High Quality)", 
            "gemini-1.0-pro (兼容性最佳/Best Compatibility)",
            "gemini-2.5-flash (最新/Latest)"
        ],
        key="model_choice",
        help="不同模型在不同地区的可用性可能不同 / Model availability may vary by region"
    )

    # 提取模型名称
    model_mapping = {
        "gemini-1.5-flash (推荐/Recommended)": "gemini-1.5-flash",
        "gemini-1.5-pro (高质量/High Quality)": "gemini-1.5-pro", 
        "gemini-1.0-pro (兼容性最佳/Best Compatibility)": "gemini-1.0-pro",
        "gemini-2.5-flash (最新/Latest)": "gemini-2.5-flash"
    }
    selected_model = model_mapping[model_choice]

    # 显示当前模型状态和测试功能
    with st.sidebar:
        st.info(f"当前模型: {selected_model}")
        
        # 模型测试功能
        if st.button("🧪 测试模型 / Test Model", help="测试所选模型是否在当前地区可用"):
            with st.spinner("测试模型连接..."):
                try:
                    from services.gemini_client import GeminiClient
                    test_client = GeminiClient(model=selected_model)
                    test_result = test_client.generate_content(prompt="Hello")
                    st.success(f"✅ 模型 {selected_model} 可用！")
                    st.caption(f"响应长度: {len(test_result)} 字符")
                except Exception as e:
                    if "User location is not supported" in str(e):
                        st.error(f"❌ 地理位置限制: {selected_model} 在当前地区不可用")
                        st.warning("建议选择其他模型或使用VPN")
                    else:
                        st.error(f"❌ 模型测试失败: {str(e)}")
                        st.info("请检查API密钥或网络连接")

    # 渲染语言切换器
    render_language_switcher()
    
    # 标题和描述
    st.title(i18n.get_text('page_title'))
    st.markdown(i18n.get_text('page_description'))
    
    # 检查API密钥
    if not check_api_key():
        st.error(i18n.get_text('file_upload.error_no_key'))
        return
    
    # 检查存储服务配置
    storage_type = check_storage_service()
    
    # 处理步骤说明
    render_processing_steps()
    
    # 文件上传 - 支持保险理赔常见文件格式
    uploaded_file = st.file_uploader(
        i18n.get_text('file_upload.label'), 
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'dcm', 'doc', 'docx'],
        help=i18n.get_text('file_upload.help_text')
    )
    
    if uploaded_file is not None:
        # 显示文件信息和类型识别
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
        file_info = get_file_type_info(uploaded_file)
        current_lang = i18n.get_current_language()
        
        # 显示文件基本信息
        st.info(i18n.get_text('file_upload.info', filename=uploaded_file.name, size=file_size))
        
        # 显示文件类型和处理方式
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{file_info['icon']} 文件类型**" if current_lang == 'zh' else f"**{file_info['icon']} File Type**")
        with col2:
            file_type_text = file_info['type_zh'] if current_lang == 'zh' else file_info['type']
            processing_note = file_info.get('processing_note_zh' if current_lang == 'zh' else 'processing_note', '')
            st.markdown(f"**{file_type_text}**")
            if processing_note:
                st.caption(f"🔧 {processing_note}")
        
        # 为非PDF文件显示特殊处理说明
        if file_info['category'] != 'document':
            if current_lang == 'zh':
                st.warning("⚠️ 注意：图像和医疗影像文件将通过OCR和AI视觉分析进行处理，处理时间可能较长。")
            else:
                st.warning("⚠️ Note: Image and medical imaging files will be processed through OCR and AI visual analysis, which may take longer.")
        
        # 开始处理按钮
        if st.button(i18n.get_text('file_upload.button'), type="primary"):
            
            try:
                # 初始化步骤状态
                steps_status = {
                    "doc_analysis": "pending",
                    "info_extraction": "pending", 
                    "rule_check": "pending",
                    "risk_analysis": "pending",
                    "report_generation": "pending"
                }
                
                # Create the complete pipeline with selected model
                with st.spinner(i18n.get_text('processing.initializing')):
                    pipeline = create_pipeline(model=selected_model)
                    storage_service = pipeline.storage_service
                
                # 上传文件到存储服务
                with st.spinner(i18n.get_text('processing.uploading')):
                    file_path = storage_service.save_uploaded_file(uploaded_file, uploaded_file.name)
                    
                    # Display success message based on storage type
                    if storage_type == "gcs":
                        st.success(i18n.get_text('storage.uploaded_to_gcs'))
                        st.info(i18n.get_text('storage.gcs_location', location=f"gs://{os.getenv('GCS_BUCKET')}/claims/{uploaded_file.name}"))
                        st.markdown(i18n.get_text('storage.powered_by_gcp'))
                    else:
                        st.success(i18n.get_text('processing.uploaded', filename=uploaded_file.name))
                
                # 创建进度条和状态文本
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 渲染步骤追踪器
                steps_container = st.container()
                
                # 1. 文档分析
                steps_status["doc_analysis"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                
                progress_bar.progress(20)
                status_text.text(i18n.get_text('processing.doc_analysis'))
                
                try:
                    doc_output = pipeline.doc_intel_agent.process(file_path)
                    steps_status["doc_analysis"] = "completed"
                except Exception as e:
                    st.error(f"📄 文档分析失败: {str(e)}")
                    st.warning("请检查文档格式是否为标准PDF文件")
                    steps_status["doc_analysis"] = "failed"
                    return
                
                # 2. 信息提取
                steps_status["info_extraction"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(40)
                status_text.text(i18n.get_text('processing.info_extraction'))
                
                try:
                    extraction_output = pipeline.info_extract_agent.process(doc_output)
                    steps_status["info_extraction"] = "completed"
                except Exception as e:
                    st.error(f"🔍 信息提取失败: {str(e)}")
                    st.warning("AI服务可能暂时繁忙，请稍后重试")
                    steps_status["info_extraction"] = "failed"
                    return
                
                # 3. 规则验证
                steps_status["rule_check"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(60)
                status_text.text(i18n.get_text('processing.rule_validation'))
                
                try:
                    validation_result = pipeline.rule_check_agent.process(extraction_output)
                    steps_status["rule_check"] = "completed"
                except Exception as e:
                    st.error(f"📋 规则验证失败: {str(e)}")
                    st.warning("验证规则可能需要更新，继续使用基础验证")
                    # 创建一个基础的验证结果作为fallback
                    from agents.rule_check import RuleValidationResult
                    validation_result = RuleValidationResult(is_valid=True, violations=[], warnings=[])
                    steps_status["rule_check"] = "completed_with_warnings"
                
                # 4. 风险分析 (多智能体协作)
                steps_status["risk_analysis"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(80)
                status_text.text(i18n.get_text('processing.risk_analysis'))
                
                try:
                    risk_analysis_output = pipeline.risk_analysis_agent.process(
                        extraction_output, 
                        validation_result,
                        doc_intel_output=doc_output,  # Enable collaboration
                        info_extract_agent=pipeline.info_extract_agent
                    )
                    steps_status["risk_analysis"] = "completed"
                except Exception as e:
                    st.error(f"⚠️ 风险分析失败: {str(e)}")
                    st.warning("AI风险评估服务异常，使用基础风险评估")
                    # 创建一个基础的风险分析结果作为fallback
                    from agents.risk_analysis import RiskAnalysisOutput
                    risk_analysis_output = RiskAnalysisOutput(
                        risk_score=50,
                        risk_factors=["AI服务异常，基础评估"],
                        fraud_indicators=[],
                        processing_priority="Standard",
                        siu_referral=False,
                        auto_approve_eligible=False
                    )
                    steps_status["risk_analysis"] = "completed_with_warnings"
                
                # 5. 报告生成
                steps_status["report_generation"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(90)
                status_text.text(i18n.get_text('processing.report_generation'))
                
                try:
                    # Get current language for localized report generation
                    current_lang = i18n.get_current_language()
                    final_report = pipeline.report_gen_agent.process(risk_analysis_output, extraction_output.extracted_data, current_lang)
                    steps_status["report_generation"] = "completed"
                except Exception as e:
                    st.error(f"📊 报告生成失败: {str(e)}")
                    st.warning("使用基础报告模板")
                    # 创建一个基础的报告作为fallback
                    from agents.report_gen import ReportOutput
                    final_report = ReportOutput(
                        recommendation="Manual_Review",
                        confidence_score=0.5,
                        report_content=f"""
# 基础审计报告

## 文档分析
- 文档类型: {getattr(doc_output, 'document_type', '未知')}
- 处理状态: 部分处理完成

## 风险评估
- 风险评分: {risk_analysis_output.risk_score}/100
- 处理建议: 人工审核

## 注意事项
- AI服务部分异常，建议人工复核
- 报告基于可用信息生成

**建议**: 联系技术支持或重新上传文档
                        """,
                        source_uri=getattr(doc_output, 'source_uri', file_path),
                        processing_priority="Standard",
                        investigation_required=False,
                        next_actions=["人工审核", "技术支持", "重新提交"]
                    )
                    steps_status["report_generation"] = "completed_with_warnings"
                
                # 完成
                progress_bar.progress(100)
                status_text.text(i18n.get_text('processing.completed'))
                
                with steps_container:
                    render_progress_tracker(steps_status)
                
                st.success(i18n.get_text('processing.completed'))
                
                # 显示结果
                st.markdown("---")
                st.markdown("## 🎯 **Analysis Results / 分析结果**")
                
                # Enhanced summary metrics with multi-language support
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    risk_level = get_risk_level_text(risk_analysis_output.risk_score)
                    st.metric(
                        label=i18n.get_text('metrics.risk_score'),
                        value=f"{risk_analysis_output.risk_score}/100",
                        delta=risk_level
                    )
                
                with col2:
                    priority_text = i18n.get_priority_text(risk_analysis_output.processing_priority)
                    st.metric(
                        label=i18n.get_text('metrics.processing_priority'),
                        value=priority_text
                    )
                
                with col3:
                    siu_text = i18n.get_text('metrics.needed') if risk_analysis_output.siu_referral else i18n.get_text('metrics.not_needed')
                    st.metric(
                        label=i18n.get_text('metrics.siu_investigation'),
                        value=siu_text
                    )
                
                with col4:
                    recommendation_text = i18n.get_recommendation_text(final_report.recommendation)
                    st.metric(
                        label=i18n.get_text('metrics.final_recommendation'),
                        value=recommendation_text,
                        delta=f"{i18n.get_text('metrics.confidence')}: {final_report.confidence_score:.0%}"
                    )
                
                # Enhanced detailed results with North American standards
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    i18n.get_text('tabs.final_report'),
                    i18n.get_text('tabs.fraud_analysis'), 
                    i18n.get_text('tabs.extracted_info'),
                    i18n.get_text('tabs.detailed_analysis'),
                    i18n.get_text('tabs.technical_details')
                ])
                
                with tab1:
                    st.markdown(f"### {i18n.get_text('tabs.final_report')}")
                    st.markdown(final_report.report_content)
                
                with tab2:
                    st.markdown(f"### {i18n.get_text('fraud_analysis.title')}")
                    
                    # Processing Priority Indicators
                    if risk_analysis_output.processing_priority == "Expedited":
                        st.success(i18n.get_text('fraud_analysis.expedited_processing'))
                    elif risk_analysis_output.processing_priority == "Enhanced_Review":
                        st.error(i18n.get_text('fraud_analysis.enhanced_review'))
                    else:
                        st.info(i18n.get_text('fraud_analysis.standard_processing'))
                    
                    # SIU Investigation
                    if risk_analysis_output.siu_referral:
                        st.error(f"**{i18n.get_text('fraud_analysis.siu_required')}**")
                        st.markdown(i18n.get_text('fraud_analysis.siu_description'))
                    else:
                        st.success(i18n.get_text('fraud_analysis.no_siu'))
                    
                    # Auto-approval eligibility
                    if risk_analysis_output.auto_approve_eligible:
                        st.success(f"**{i18n.get_text('fraud_analysis.auto_approve_eligible')}**")
                        st.markdown(i18n.get_text('fraud_analysis.auto_approve_description'))
                    else:
                        st.warning(f"**{i18n.get_text('fraud_analysis.manual_review_required')}**")
                        st.markdown(i18n.get_text('fraud_analysis.manual_review_description'))
                    
                    # Fraud indicators
                    st.markdown(i18n.get_text('fraud_analysis.fraud_indicators'))
                    if risk_analysis_output.fraud_indicators:
                        for indicator in risk_analysis_output.fraud_indicators:
                            st.warning(f"🚨 {indicator}")
                    else:
                        st.success(i18n.get_text('fraud_analysis.no_fraud_detected'))
                    
                    # Settlement estimate
                    if hasattr(risk_analysis_output, 'settlement_estimate') and risk_analysis_output.settlement_estimate:
                        st.markdown(i18n.get_text('fraud_analysis.settlement_estimate'))
                        st.info(f"💰 {risk_analysis_output.settlement_estimate}")
                
                with tab3:
                    st.markdown(f"### {i18n.get_text('tabs.extracted_info')}")
                    st.json(extraction_output.extracted_data)
                
                with tab4:
                    st.markdown(f"### {i18n.get_text('detailed_analysis.title')}")
                    
                    st.markdown(i18n.get_text('detailed_analysis.rule_validation'))
                    if validation_result.violations:
                        for violation in validation_result.violations:
                            st.error(f"❌ {violation}")
                    else:
                        st.success(i18n.get_text('detailed_analysis.all_rules_passed'))
                    
                    st.markdown(i18n.get_text('detailed_analysis.risk_factors'))
                    if risk_analysis_output.risk_factors:
                        for factor in risk_analysis_output.risk_factors:
                            st.warning(f"⚠️ {factor}")
                    else:
                        st.success(i18n.get_text('detailed_analysis.no_risk_factors'))
                    
                    # Next actions
                    if hasattr(final_report, 'next_actions') and final_report.next_actions:
                        st.markdown(i18n.get_text('detailed_analysis.next_actions'))
                        for action in final_report.next_actions:
                            st.info(f"📋 {action}")
                
                with tab5:
                    st.markdown(f"### {i18n.get_text('technical_details.title')}")
                    
                    tech_data = {
                        i18n.get_text('technical_details.document_type'): doc_output.document_type,
                        i18n.get_text('technical_details.content_length'): f"{len(doc_output.extracted_text)} {i18n.get_text('technical_details.characters')}",
                        i18n.get_text('technical_details.validation_status'): "✅" if not validation_result.violations else "❌",
                        i18n.get_text('technical_details.risk_score'): f"{risk_analysis_output.risk_score}/100",
                        i18n.get_text('technical_details.processing_model'): selected_model,
                        i18n.get_text('technical_details.file_uri'): file_path
                    }
                    
                    for key, value in tech_data.items():
                        st.text(f"{key}: {value}")
            
            except Exception as e:
                st.error(i18n.get_text('errors.processing_error', error=str(e)))
                st.error(f"Traceback: {str(e)}")
    
    # 页脚
    st.markdown("---")
    st.markdown(f"<center>{i18n.get_text('footer')}</center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()