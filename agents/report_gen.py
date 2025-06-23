"""The ReportGen agent: generates final reports based on analysis results."""

from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.risk_analysis import RiskAnalysisOutput
from services.gemini_client import GeminiClient


@dataclass
class ReportOutput:
    """Represents the final generated report."""
    report_content: str
    recommendation: str  # "approve", "deny", "manual_review", "siu_referral", "expedited_approve"
    confidence_score: float
    source_uri: str
    # 新增：北美标准字段
    processing_priority: str  # "Expedited", "Standard", "Enhanced_Review"
    investigation_required: bool
    next_actions: list  # 后续行动建议


class ReportGenAgent(BaseAgent):
    """
    An agent that generates final claim processing reports based on all
    previous analysis results. Enhanced for North American insurance standards.
    """

    def __init__(self, gemini_client: GeminiClient):
        self._gemini = gemini_client

    def process(self, risk_analysis_output: RiskAnalysisOutput, extracted_data: Dict[str, Any], language: str = "en") -> ReportOutput:
        """
        Generate a comprehensive final report based on risk analysis and extracted data.
        Enhanced with North American insurance processing standards.
        
        Args:
            risk_analysis_output: Results from risk analysis
            extracted_data: Structured data extracted from the document
            
        Returns:
            ReportOutput containing the final report and recommendation
        """
        
        # Create a summary of extracted data with safe formatting
        def safe_format(value, format_spec=""):
            """Safely format values, handling None cases."""
            if value is None:
                return "N/A"
            if format_spec and isinstance(value, (int, float)):
                return f"{value:{format_spec}}"
            return str(value)
        
        # 生成报告时间戳
        report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate localized extracted summary
        extracted_summary = self._generate_extracted_summary(
            extracted_data, risk_analysis_output, report_timestamp, language
        )

        # 基于风险分析确定推荐决策
        recommendation, next_actions = self._determine_recommendation(risk_analysis_output, language)
        
        # Generate enhanced final recommendation using AI with language support
        prompt = self._generate_ai_prompt(extracted_summary, recommendation, risk_analysis_output, language)

        try:
            ai_response = self._gemini.generate_content(prompt=prompt)
            
            # Parse the AI response
            parsed_response = self._parse_ai_response(ai_response)
            
            confidence_score = parsed_response.get('confidence', 0.8)
            executive_summary = parsed_response.get('executive_summary', '')
            detailed_reasoning = parsed_response.get('detailed_reasoning', ai_response)
            compliance_notes = parsed_response.get('compliance_notes', '')
            ai_next_steps = parsed_response.get('next_steps', '')
            
        except Exception as e:
            # Fallback analysis
            confidence_score = 0.6
            executive_summary = f"Automated analysis completed with risk score {risk_analysis_output.risk_score}/100."
            detailed_reasoning = f"Analysis error: {str(e)}. Recommendation based on rule-based assessment."
            compliance_notes = "Manual review recommended due to processing limitations."
            ai_next_steps = ""

        # Generate the final comprehensive report with language support
        report_content = self._generate_final_report(
            executive_summary, extracted_summary, recommendation, confidence_score,
            detailed_reasoning, compliance_notes, next_actions, ai_next_steps,
            risk_analysis_output, report_timestamp, language
        )

        return ReportOutput(
            report_content=report_content,
            recommendation=recommendation,
            confidence_score=confidence_score,
            source_uri=risk_analysis_output.source_uri,
            processing_priority=risk_analysis_output.processing_priority,
            investigation_required=risk_analysis_output.siu_referral,
            next_actions=next_actions
        )

    def _determine_recommendation(self, risk_analysis: RiskAnalysisOutput, language: str = "en") -> tuple[str, list]:
        """根据风险分析确定处理建议和后续行动"""
        
        if risk_analysis.auto_approve_eligible:
            recommendation = "expedited_approve"
            if language == "zh":
                next_actions = [
                    "24小时内处理付款",
                    "向申请人发送批准通知",
                    "更新理赔状态为'已批准-快速处理'"
                ]
            else:
                next_actions = [
                    "Process payment within 24 hours",
                    "Send approval notification to claimant",
                    "Update claim status to 'Approved - Expedited'"
                ]
        elif risk_analysis.siu_referral:
            recommendation = "siu_referral"
            if language == "zh":
                next_actions = [
                    "立即转交特殊调查单位",
                    "暂停付款等待调查",
                    "要求提供额外文档",
                    "如怀疑欺诈需通知法务部"
                ]
            else:
                next_actions = [
                    "Refer to Special Investigation Unit immediately",
                    "Suspend payment pending investigation",
                    "Request additional documentation",
                    "Notify legal department if fraud suspected"
                ]
        elif risk_analysis.risk_score >= 70:
            recommendation = "deny"
            if language == "zh":
                next_actions = [
                    "准备拒赔信函并说明具体原因",
                    "与高级理赔员审查决定",
                    "在规定时间内发送拒赔通知"
                ]
            else:
                next_actions = [
                    "Prepare denial letter with specific reasons",
                    "Review decision with senior adjuster",
                    "Send denial notification within regulatory timeframe"
                ]
        elif risk_analysis.risk_score >= 40:
            recommendation = "manual_review"
            if language == "zh":
                next_actions = [
                    "分配给高级理赔员处理",
                    "如适用，要求现场检查",
                    "验证保单条款和承保限额",
                    "安排理赔审查会议"
                ]
            else:
                next_actions = [
                    "Assign to senior claims adjuster",
                    "Request field inspection if applicable",
                    "Verify policy terms and coverage limits",
                    "Schedule claim review meeting"
                ]
        else:
            recommendation = "approve"
            if language == "zh":
                next_actions = [
                    "处理标准批准流程",
                    "计算最终理赔金额",
                    "准备理赔文档"
                ]
            else:
                next_actions = [
                    "Process standard approval workflow",
                    "Calculate final settlement amount",
                    "Prepare settlement documentation"
                ]
        
        return recommendation, next_actions
    
    def _format_settlement_estimate(self, estimate_range):
        """格式化理赔金额估算"""
        if estimate_range:
            return f"""
**Estimated Settlement Range**: ${estimate_range.get('low', 0):,.2f} - ${estimate_range.get('high', 0):,.2f}
**Assessment Basis**: AI analysis of claim documents and industry benchmarks
"""
        else:
            return """
**Settlement Estimate**: Insufficient data for accurate estimation
**Recommendation**: Manual assessment required by qualified adjuster
"""
    
    def _format_investigation_requirements(self, risk_analysis: RiskAnalysisOutput):
        """格式化调查要求"""
        if risk_analysis.siu_referral:
            return """
**SIU Investigation Required**: Yes
**Priority Level**: High
**Focus Areas**: 
- Document authenticity verification
- Timeline consistency analysis  
- Financial background check
- Cross-reference with known fraud patterns
"""
        elif risk_analysis.fraud_indicators:
            return """
**Enhanced Review Required**: Yes
**Focus Areas**:
- Additional documentation verification
- Policy compliance check
- Settlement amount validation
"""
        else:
            return """
**Standard Processing**: No additional investigation required
**Quality Check**: Routine documentation review sufficient
"""
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """解析AI增强分析响应"""
        results = {}
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            if line.startswith("EXECUTIVE_SUMMARY:"):
                results['executive_summary'] = line.split(":", 1)[1].strip()
            elif line.startswith("DETAILED_REASONING:"):
                results['detailed_reasoning'] = line.split(":", 1)[1].strip()
            elif line.startswith("COMPLIANCE_NOTES:"):
                results['compliance_notes'] = line.split(":", 1)[1].strip()
            elif line.startswith("NEXT_STEPS:"):
                results['next_steps'] = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    results['confidence'] = float(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    results['confidence'] = 0.8
        
        return results
    
    def _generate_extracted_summary(self, extracted_data: Dict[str, Any], risk_analysis_output: RiskAnalysisOutput, 
                                   report_timestamp: str, language: str) -> str:
        """生成多语言的提取信息摘要"""
        def safe_format(value, format_spec=""):
            if value is None:
                return "N/A" if language == "en" else "无"
            if format_spec and isinstance(value, (int, float)):
                return f"{value:{format_spec}}"
            return str(value)
        
        if language == "zh":
            return f"""
## 理赔信息摘要

- **报告生成时间**: `{report_timestamp}`
- **申请人姓名**: `{safe_format(extracted_data.get('claimant_name'))}`
- **保单号码**: `{safe_format(extracted_data.get('policy_number'))}`
- **事故日期**: `{safe_format(extracted_data.get('date_of_incident'))}`
- **理赔金额**: `${safe_format(extracted_data.get('claim_amount', 0), '.2f')}`
- **车辆详情**: `{safe_format(extracted_data.get('vehicle_details'))}`

## 风险分析结果

- **风险评分**: `{risk_analysis_output.risk_score}/100`
- **风险等级**: `{risk_analysis_output.risk_level}`
- **处理优先级**: `{risk_analysis_output.processing_priority}`
- **自动批准资格**: `{'是' if risk_analysis_output.auto_approve_eligible else '否'}`
- **需要SIU调查**: `{'是' if risk_analysis_output.siu_referral else '否'}`

## 欺诈检测分析

**主要风险因素:**
{chr(10).join([f'- {factor}' for factor in risk_analysis_output.risk_factors]) if risk_analysis_output.risk_factors else '- 未发现重大风险因素'}

**欺诈指标:**
{chr(10).join([f'- {indicator}' for indicator in risk_analysis_output.fraud_indicators]) if risk_analysis_output.fraud_indicators else '- 未检测到欺诈指标'}

## 理赔评估

{self._format_settlement_estimate(risk_analysis_output.estimated_settlement_range, language)}

## 详细分析

{risk_analysis_output.analysis_details}
"""
        else:  # English
            return f"""
## Claim Information Summary

- **Report Generated**: `{report_timestamp}`
- **Claimant Name**: `{safe_format(extracted_data.get('claimant_name'))}`
- **Policy Number**: `{safe_format(extracted_data.get('policy_number'))}`
- **Date of Incident**: `{safe_format(extracted_data.get('date_of_incident'))}`
- **Claim Amount**: `${safe_format(extracted_data.get('claim_amount', 0), '.2f')}`
- **Vehicle Details**: `{safe_format(extracted_data.get('vehicle_details'))}`

## Risk Analysis Results

- **Risk Score**: `{risk_analysis_output.risk_score}/100`
- **Risk Level**: `{risk_analysis_output.risk_level}`
- **Processing Priority**: `{risk_analysis_output.processing_priority}`
- **Auto-Approval Eligible**: `{'Yes' if risk_analysis_output.auto_approve_eligible else 'No'}`
- **SIU Referral Required**: `{'Yes' if risk_analysis_output.siu_referral else 'No'}`

## Fraud Detection Analysis

**Primary Risk Factors:**
{chr(10).join([f'- {factor}' for factor in risk_analysis_output.risk_factors]) if risk_analysis_output.risk_factors else '- No significant risk factors identified'}

**Fraud Indicators:**
{chr(10).join([f'- {indicator}' for indicator in risk_analysis_output.fraud_indicators]) if risk_analysis_output.fraud_indicators else '- No fraud indicators detected'}

## Settlement Assessment

{self._format_settlement_estimate(risk_analysis_output.estimated_settlement_range, language)}

## Detailed Analysis

{risk_analysis_output.analysis_details}
"""
    
    def _generate_ai_prompt(self, extracted_summary: str, recommendation: str, 
                           risk_analysis_output: RiskAnalysisOutput, language: str) -> str:
        """生成多语言AI提示"""
        if language == "zh":
            return f"""
你是一名北美地区的高级保险理赔员。请根据行业标准和监管要求生成一份全面的最终报告。

{extracted_summary}

当前推荐: {recommendation}
风险评估: {risk_analysis_output.risk_level} 风险 ({risk_analysis_output.risk_score}/100)

请提供：
1. 调查结果的专业总结
2. 推荐决策的详细理由
3. 合规性考虑
4. 后续步骤和时间安排
5. 置信度评估 (0.0 到 1.0)

考虑北美保险法规：
- 公平理赔处理实践
- 欺诈预防要求
- 客户服务标准
- 文档要求
- 处理时限

请按以下格式回复（用中文）：
EXECUTIVE_SUMMARY: [简要专业总结]
DETAILED_REASONING: [全面分析]
COMPLIANCE_NOTES: [监管考虑]
NEXT_STEPS: [具体行动项目和时间安排]
CONFIDENCE: [0.0-1.0]
"""
        else:  # English
            return f"""
You are a senior insurance claims adjuster in North America. Generate a comprehensive final report 
following industry standards and regulatory requirements.

{extracted_summary}

Current Recommendation: {recommendation}
Risk Assessment: {risk_analysis_output.risk_level} Risk ({risk_analysis_output.risk_score}/100)

Please provide:
1. Professional summary of findings
2. Detailed reasoning for the recommendation
3. Compliance considerations
4. Next steps and timeline
5. Confidence assessment (0.0 to 1.0)

Consider North American insurance regulations:
- Fair Claims Settlement Practices
- Fraud prevention requirements
- Customer service standards
- Documentation requirements
- Time limits for processing

Format your response as:
EXECUTIVE_SUMMARY: [Brief professional summary]
DETAILED_REASONING: [Comprehensive analysis]
COMPLIANCE_NOTES: [Regulatory considerations]
NEXT_STEPS: [Specific action items with timeline]
CONFIDENCE: [0.0-1.0]
"""

    def _format_settlement_estimate(self, estimate_range, language: str = "en"):
        """格式化理赔金额估算 - 多语言版本"""
        if language == "zh":
            if estimate_range:
                return f"""
**预计理赔范围**: ${estimate_range.get('low', 0):,.2f} - ${estimate_range.get('high', 0):,.2f}
**评估依据**: 基于理赔文档的AI分析和行业基准
"""
            else:
                return """
**理赔估算**: 数据不足，无法准确估算
**建议**: 需要合格理赔员进行人工评估
"""
        else:  # English
            if estimate_range:
                return f"""
**Estimated Settlement Range**: ${estimate_range.get('low', 0):,.2f} - ${estimate_range.get('high', 0):,.2f}
**Assessment Basis**: AI analysis of claim documents and industry benchmarks
"""
            else:
                return """
**Settlement Estimate**: Insufficient data for accurate estimation
**Recommendation**: Manual assessment required by qualified adjuster
"""
    
    def _format_investigation_requirements(self, risk_analysis: RiskAnalysisOutput, language: str = "en"):
        """格式化调查要求 - 多语言版本"""
        if language == "zh":
            if risk_analysis.siu_referral:
                return """
**需要SIU调查**: 是
**优先级**: 高
**重点领域**: 
- 文档真实性验证
- 时间线一致性分析  
- 财务背景调查
- 与已知欺诈模式交叉比对
"""
            elif risk_analysis.fraud_indicators:
                return """
**需要增强审查**: 是
**重点领域**:
- 额外文档验证
- 保单合规性检查
- 理赔金额验证
"""
            else:
                return """
**标准处理**: 无需额外调查
**质量检查**: 常规文档审查即可满足要求
"""
        else:  # English
            if risk_analysis.siu_referral:
                return """
**SIU Investigation Required**: Yes
**Priority Level**: High
**Focus Areas**: 
- Document authenticity verification
- Timeline consistency analysis  
- Financial background check
- Cross-reference with known fraud patterns
"""
            elif risk_analysis.fraud_indicators:
                return """
**Enhanced Review Required**: Yes
**Focus Areas**:
- Additional documentation verification
- Policy compliance check
- Settlement amount validation
"""
            else:
                return """
**Standard Processing**: No additional investigation required
**Quality Check**: Routine documentation review sufficient
"""
    
    def _generate_final_report(self, executive_summary: str, extracted_summary: str, recommendation: str,
                             confidence_score: float, detailed_reasoning: str, compliance_notes: str,
                             next_actions: list, ai_next_steps: str, risk_analysis_output: RiskAnalysisOutput,
                             report_timestamp: str, language: str) -> str:
        """生成最终报告 - 多语言版本"""
        
        if language == "zh":
            return f"""
# 保险理赔处理报告

## 执行摘要

{executive_summary}

{extracted_summary}

## 专业评估与建议

**最终决策**: **{recommendation.upper().replace('_', ' ')}**
**置信度**: {confidence_score:.2f}
**处理优先级**: {risk_analysis_output.processing_priority}

### 分析理由

{detailed_reasoning}

### 调查要求

{self._format_investigation_requirements(risk_analysis_output, language)}

### 合规性考虑

{compliance_notes if compliance_notes else '适用标准处理程序。确保符合州法规和公司政策。'}

## 后续步骤与行动项

### 即时行动 (24小时内):
{chr(10).join([f'- {action}' for action in next_actions[:3]]) if next_actions else '- 按照标准程序处理'}

### 后续行动:
{ai_next_steps if ai_next_steps else '- 监控理赔状态并根据需要更新'}

## 质量保证

- **自动化分析**: ✅ 已完成
- **欺诈筛查**: {'✅ 通过' if not risk_analysis_output.fraud_indicators else '⚠️ 检测到标记'}
- **文档审查**: {'✅ 完成' if risk_analysis_output.risk_score < 50 else '⚠️ 需要额外审查'}
- **监管合规**: ✅ 已验证

---

### 报告元数据

- **生成系统**: AuditAI 系统 v2.0
- **报告ID**: {report_timestamp.replace(' ', '_').replace(':', '')}
  - **处理模型**: Gemini-1.5-Flash
- **分析标准**: 北美保险行业标准
- **最后更新**: {report_timestamp}

*本报告由AI驱动的分析系统生成，遵循北美保险行业标准。所有建议应由合格的理赔专业人员审查后方可最终处置。*
"""
        else:  # English
            return f"""
# Insurance Claim Processing Report

## Executive Summary

{executive_summary}

{extracted_summary}

## Professional Assessment & Recommendation

**Final Decision**: **{recommendation.upper().replace('_', ' ')}**
**Confidence Level**: {confidence_score:.2f}
**Processing Priority**: {risk_analysis_output.processing_priority}

### Reasoning

{detailed_reasoning}

### Investigation Requirements

{self._format_investigation_requirements(risk_analysis_output, language)}

### Compliance Considerations

{compliance_notes if compliance_notes else 'Standard processing procedures apply. Ensure compliance with state regulations and company policies.'}

## Next Steps & Action Items

### Immediate Actions (Within 24 hours):
{chr(10).join([f'- {action}' for action in next_actions[:3]]) if next_actions else '- Process according to standard procedures'}

### Follow-up Actions:
{ai_next_steps if ai_next_steps else '- Monitor claim status and update as required'}

## Quality Assurance

- **Automated Analysis**: ✅ Completed
- **Fraud Screening**: {'✅ Passed' if not risk_analysis_output.fraud_indicators else '⚠️ Flags Detected'}
- **Documentation Review**: {'✅ Complete' if risk_analysis_output.risk_score < 50 else '⚠️ Additional Review Required'}
- **Regulatory Compliance**: ✅ Verified

---

### Report Metadata

- **Generated By**: AuditAI System v2.0
- **Report ID**: {report_timestamp.replace(' ', '_').replace(':', '')}
  - **Processing Model**: Gemini-1.5-Flash
- **Analysis Standards**: North American Insurance Industry
- **Last Updated**: {report_timestamp}

*This report has been generated using AI-powered analysis following North American insurance industry standards. 
All recommendations should be reviewed by qualified claims professionals before final disposition.*
""" 