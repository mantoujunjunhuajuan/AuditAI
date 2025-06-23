import streamlit as st
import google.generativeai as genai
from google.cloud import storage
import os
import tempfile
from PIL import Image

# --- 页面配置 ---
st.set_page_config(
    page_title="AuditAI - 您的AI保险审核助手",
    page_icon="🤖"
)

# --- 配置 ---
GCS_BUCKET_NAME = "auditai-claims-bucket" # 请确保这是你创建的真实存储桶名称

# --- 配置Google AI Gemini API ---
def setup_gemini_api():
    """设置Gemini API"""
    api_key = st.text_input(
        "请输入您的Google AI Gemini API密钥:",
        type="password",
        help="在 https://aistudio.google.com/ 获取您的API密钥"
    )
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.success("✅ Gemini API 配置成功！")
            return True
        except Exception as e:
            st.error(f"❌ API密钥配置失败: {e}")
            return False
    else:
        st.info("📝 请先输入您的Gemini API密钥以开始使用")
        return False

# --- Google Cloud Storage 函数 ---
def upload_to_gcs(file_to_upload, bucket_name, destination_blob_name):
    """上传文件到GCS（可选功能）"""
    try:
        storage_client = storage.Client() 
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        file_to_upload.seek(0)
        blob.upload_from_file(file_to_upload)
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
        st.success(f"文件 '{destination_blob_name}' 已成功上传到云端！")
        return gcs_uri
    except Exception as e:
        st.warning(f"GCS上传失败 (将使用本地处理): {e}")
        return None

# --- Google AI Gemini 函数 ---
def analyze_document_with_gemini(uploaded_file):
    """使用Google AI Gemini API分析文档"""
    import time
    
    # 检查文件大小
    file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
    if file_size > 20:  # 超过20MB的文件可能会有问题
        st.warning(f"⚠️ 文件较大（{file_size:.1f}MB），可能需要更长时间处理")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 将上传的文件保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                uploaded_file.seek(0)
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # 上传文件到Gemini（带重试）
            st.info(f"📤 正在上传文件到Gemini... (尝试 {attempt + 1}/{max_retries})")
            
            uploaded_gemini_file = genai.upload_file(tmp_file_path)
            st.success("✅ 文件上传成功！")
            
            # 使用Gemini分析文档
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt_text = """
            你是一个经验丰富的保险理赔审核员。
            请仔细审查以下这份保险理赔文件。
            你的任务是：
            1. 总结文件的核心内容，包括索赔人、索赔日期和索赔金额。
            2. 根据常见的欺诈风险点（例如：日期逻辑矛盾、金额异常、描述含糊等），识别出任何潜在的疑点。
            3. 给出一个最终的审核建议：'批准'、'拒绝' 或 '建议人工复核'。
            请以清晰、有条理的格式返回你的分析报告。
            """
            
            st.info("🤖 AI正在分析文档...")
            response = model.generate_content([uploaded_gemini_file, prompt_text])
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            st.warning(f"⚠️ 尝试 {attempt + 1} 失败: {error_msg}")
            
            # 清理临时文件
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            
            # 如果是SSL错误，提供具体建议
            if "SSL" in error_msg or "EOF" in error_msg:
                if attempt < max_retries - 1:
                    st.info(f"🔄 检测到网络连接问题，{2 ** attempt} 秒后重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    st.error("❌ 网络连接不稳定，建议：")
                    st.markdown("""
                    1. 检查网络连接是否稳定
                    2. 尝试使用较小的PDF文件（<10MB）
                    3. 如果使用VPN，请尝试关闭
                    4. 等待几分钟后重试
                    5. 或尝试在网络条件更好的环境下使用
                    """)
            
            # 如果不是最后一次尝试，继续重试
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
    
    # 所有重试都失败了
    st.error("❌ 多次尝试后仍然失败，请检查网络连接或尝试较小的文件")
    return None

# --- 主应用 ---
def main():
    st.title("🤖 AuditAI - AI保险审核助手")
    st.write("欢迎使用！我们现在使用**Google AI Gemini API**进行文档分析。")
    
    # 显示API说明
    with st.expander("🔑 关于Google AI Gemini API"):
        st.markdown("""
        **为什么切换到Google AI Gemini API？**
        - 🚀 **更简单**：只需要API密钥，无需复杂的GCP配置
        - ⚡ **更快速**：直接调用，无需等待权限设置
        - 🎯 **更可靠**：专为开发者设计的快速通道
        
        **如何获取API密钥？**
        1. 访问 [Google AI Studio](https://aistudio.google.com/)
        2. 登录您的Google账号
        3. 点击 "Get API key"
        4. 选择 "Create API key in new project"
        5. 复制生成的API密钥到下面的输入框
        """)
    
    # 设置API密钥
    api_configured = setup_gemini_api()
    
    if api_configured:
        st.markdown("---")
        st.subheader("📄 文档分析")
        
        # 文件大小提示
        st.info("💡 建议上传20MB以下的PDF文件以获得最佳性能")
        
        # 文件上传
        uploaded_file = st.file_uploader(
            label="请上传PDF理赔文件",
            type=['pdf'],
            accept_multiple_files=False
        )
        
        if uploaded_file:
            st.success(f"✅ 文件已选择: {uploaded_file.name}")
            
            # 显示文件信息
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
            st.info(f"📊 文件大小: {file_size:.2f} MB")
            
            # 分析按钮
            if st.button("🚀 开始AI审核", type="primary"):
                with st.spinner("🔍 AI正在分析文档，请稍候..."):
                    # 可选：尝试上传到GCS（如果配置了的话）
                    gcs_uri = None
                    try:
                        gcs_uri = upload_to_gcs(uploaded_file, GCS_BUCKET_NAME, uploaded_file.name)
                    except:
                        st.info("ℹ️ 跳过GCS上传，直接进行本地分析")
                    
                    # 使用Gemini分析
                    analysis_result = analyze_document_with_gemini(uploaded_file)
                
                # 显示结果
                st.markdown("---")
                st.subheader("📋 AI审核报告")
                
                if analysis_result:
                    st.success("✅ 分析完成！")
                    st.markdown(analysis_result)
                    
                    # 额外信息
                    with st.expander("📊 技术详情"):
                        st.json({
                            "模型": "Google AI Gemini 1.5 Flash",
                            "API方式": "Google AI Gemini API",
                            "文件名": uploaded_file.name,
                            "文件大小": f"{file_size:.2f} MB",
                            "GCS上传": "成功" if gcs_uri else "跳过"
                        })
                        
                else:
                    st.error("❌ 分析失败，请检查文件格式或网络连接")
    
    else:
        st.warning("⚠️ 请先配置API密钥才能继续使用")

if __name__ == "__main__":
    main()