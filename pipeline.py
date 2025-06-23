"""The main orchestration pipeline for processing an insurance claim."""

from agents.doc_intel import DocIntelAgent
from agents.info_extract import InfoExtractAgent
from agents.report_gen import ReportGenAgent, ReportOutput
from agents.risk_analysis import RiskAnalysisAgent
from agents.rule_check import RuleCheckAgent
from services.gemini_client import GeminiClient
from services.storage_service import LocalStorageService
from utils.pdf_parser import PDFParser
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ClaimProcessingPipeline:
    """
    Orchestrates the entire claim processing workflow by executing a sequence of agents.
    """

    def __init__(self, gemini_client: GeminiClient, storage_service: LocalStorageService, pdf_parser: PDFParser):
        """
        Initialize the pipeline with required services and agents.
        
        Args:
            gemini_client: Client for AI model interactions
            storage_service: Service for file storage operations
            pdf_parser: Service for PDF parsing operations
        """
        self.storage_service = storage_service
        self.pdf_parser = pdf_parser
        
        # Initialize all agents with their dependencies
        self.doc_intel_agent = DocIntelAgent(storage_service, pdf_parser, gemini_client)
        self.info_extract_agent = InfoExtractAgent(gemini_client)
        self.rule_check_agent = RuleCheckAgent()
        self.risk_analysis_agent = RiskAnalysisAgent(gemini_client)
        self.report_gen_agent = ReportGenAgent(gemini_client)

    def run(self, file_uri: str) -> ReportOutput:
        """
        Execute the complete claim processing pipeline.
        
        Args:
            file_uri: URI of the uploaded file to process
            
        Returns:
            ReportOutput: Final generated report with recommendation
        """
        print("🚀 Starting claim processing pipeline...")
        
        # Step 1: Document Intelligence Analysis
        print("\n📄 Step 1: Document Intelligence Analysis...")
        doc_intel_output = self.doc_intel_agent.process(file_uri)
        print(f"✅ Document analysis completed")
        print(f"   - Document type: {doc_intel_output.doc_type}")
        print(f"   - Content length: {len(doc_intel_output.content)} characters")

        # Step 2: Information Extraction
        print("\n🔍 Step 2: Information Extraction...")
        extraction_output = self.info_extract_agent.process(doc_intel_output)
        print(f"✅ Information extraction completed")
        print(f"   - Extracted fields: {list(extraction_output.extracted_data.keys())}")

        # Step 3: Rule Validation
        print("\n📋 Step 3: Rule Validation...")
        validation_result = self.rule_check_agent.process(extraction_output)
        print(f"✅ Rule validation completed")
        print(f"   - Valid: {validation_result.is_valid}")
        print(f"   - Violations: {len(validation_result.violations)}")

        # Step 4: Risk Analysis
        print("\n⚠️  Step 4: Risk Analysis...")
        risk_analysis_output = self.risk_analysis_agent.process(extraction_output, validation_result)
        print(f"✅ Risk analysis completed")
        print(f"   - Risk score: {risk_analysis_output.risk_score}/100")

        # Step 5: Final Report Generation
        print("\n📊 Step 5: Final Report Generation...")
        final_report = self.report_gen_agent.process(risk_analysis_output, extraction_output.extracted_data)
        print(f"✅ Final report generated")
        print(f"   - Recommendation: {final_report.recommendation}")
        print(f"   - Confidence: {final_report.confidence_score:.2f}")

        return final_report


def create_pipeline() -> ClaimProcessingPipeline:
    """
    Factory function to create a fully configured pipeline instance.
    
    Returns:
        ClaimProcessingPipeline: Ready-to-use pipeline instance
    """
    # Initialize services
    gemini_client = GeminiClient()
    storage_service = LocalStorageService()
    pdf_parser = PDFParser()
    
    # Create and return pipeline
    return ClaimProcessingPipeline(gemini_client, storage_service, pdf_parser)


if __name__ == "__main__":
    # Get file path from command line argument or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Interactive mode - ask user for file path
        file_path = input("请输入PDF文件路径: ").strip()
    
    if not file_path or not Path(file_path).exists():
        print("❌ 错误：请提供有效的文件路径")
        sys.exit(1)
    
    try:
        # Create pipeline
        print("🔧 初始化处理管道...")
        pipeline = create_pipeline()
        print("✅ 管道初始化成功")
        
        # Upload file to storage
        print(f"📤 上传文件: {Path(file_path).name}")
        file_uri = pipeline.storage_service.upload_file(file_path, "test_claims")
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
        
    except Exception as e:
        print(f"❌ 管道执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 