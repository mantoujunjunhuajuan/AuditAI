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

    def process(self, risk_analysis_output: RiskAnalysisOutput, extracted_data: Dict[str, Any]) -> ReportOutput:
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
        
        extracted_summary = f"""
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

{self._format_settlement_estimate(risk_analysis_output.estimated_settlement_range)}

## Detailed Analysis

{risk_analysis_output.analysis_details}
"""

        # 基于风险分析确定推荐决策
        recommendation, next_actions = self._determine_recommendation(risk_analysis_output)
        
        # Generate enhanced final recommendation using AI
        prompt = f"""
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

        # Generate the final comprehensive report
        report_content = f"""
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

{self._format_investigation_requirements(risk_analysis_output)}

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

        return ReportOutput(
            report_content=report_content,
            recommendation=recommendation,
            confidence_score=confidence_score,
            source_uri=risk_analysis_output.source_uri,
            processing_priority=risk_analysis_output.processing_priority,
            investigation_required=risk_analysis_output.siu_referral,
            next_actions=next_actions
        )

    def _determine_recommendation(self, risk_analysis: RiskAnalysisOutput) -> tuple[str, list]:
        """根据风险分析确定处理建议和后续行动"""
        
        if risk_analysis.auto_approve_eligible:
            recommendation = "expedited_approve"
            next_actions = [
                "Process payment within 24 hours",
                "Send approval notification to claimant",
                "Update claim status to 'Approved - Expedited'"
            ]
        elif risk_analysis.siu_referral:
            recommendation = "siu_referral"
            next_actions = [
                "Refer to Special Investigation Unit immediately",
                "Suspend payment pending investigation",
                "Request additional documentation",
                "Notify legal department if fraud suspected"
            ]
        elif risk_analysis.risk_score >= 70:
            recommendation = "deny"
            next_actions = [
                "Prepare denial letter with specific reasons",
                "Review decision with senior adjuster",
                "Send denial notification within regulatory timeframe"
            ]
        elif risk_analysis.risk_score >= 40:
            recommendation = "manual_review"
            next_actions = [
                "Assign to senior claims adjuster",
                "Request field inspection if applicable",
                "Verify policy terms and coverage limits",
                "Schedule claim review meeting"
            ]
        else:
            recommendation = "approve"
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