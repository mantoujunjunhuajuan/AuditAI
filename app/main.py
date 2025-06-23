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
        page_title="AuditAI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
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
    
    # 渲染语言切换器
    render_language_switcher()
    
    # 标题和描述
    st.title(i18n.get_text('page_title'))
    st.markdown(i18n.get_text('page_description'))
    
    # 检查API密钥
    if not check_api_key():
        st.error(i18n.get_text('file_upload.error_no_key'))
        return
    
    # 处理步骤说明
    render_processing_steps()
    
    # 文件上传
    uploaded_file = st.file_uploader(
        i18n.get_text('file_upload.label'), 
        type=['pdf']
    )
    
    if uploaded_file is not None:
        # 显示文件信息
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
        st.info(i18n.get_text('file_upload.info', filename=uploaded_file.name, size=file_size))
        
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
                
                # Create the complete pipeline
                with st.spinner(i18n.get_text('processing.initializing')):
                    pipeline = create_pipeline()
                    storage_service = pipeline.storage_service
                
                # 上传文件到本地存储
                with st.spinner(i18n.get_text('processing.uploading')):
                    file_path = storage_service.save_uploaded_file(uploaded_file, uploaded_file.name)
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
                doc_output = pipeline.doc_intel_agent.process(file_path)
                steps_status["doc_analysis"] = "completed"
                
                # 2. 信息提取
                steps_status["info_extraction"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(40)
                status_text.text(i18n.get_text('processing.info_extraction'))
                extraction_output = pipeline.info_extract_agent.process(doc_output)
                steps_status["info_extraction"] = "completed"
                
                # 3. 规则验证
                steps_status["rule_check"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(60)
                status_text.text(i18n.get_text('processing.rule_validation'))
                validation_result = pipeline.rule_check_agent.process(extraction_output)
                steps_status["rule_check"] = "completed"
                
                # 4. 风险分析
                steps_status["risk_analysis"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(80)
                status_text.text(i18n.get_text('processing.risk_analysis'))
                risk_analysis_output = pipeline.risk_analysis_agent.process(extraction_output, validation_result)
                steps_status["risk_analysis"] = "completed"
                
                # 5. 报告生成
                steps_status["report_generation"] = "processing"
                with steps_container:
                    render_progress_tracker(steps_status)
                    
                progress_bar.progress(90)
                status_text.text(i18n.get_text('processing.report_generation'))
                final_report = pipeline.report_gen_agent.process(risk_analysis_output)
                steps_status["report_generation"] = "completed"
                
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
                        i18n.get_text('technical_details.processing_model'): "gemini-1.5-flash",
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