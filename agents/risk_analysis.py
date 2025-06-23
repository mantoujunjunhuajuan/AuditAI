"""The RiskAnalysis agent: assigns a risk score to a validated claim."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.rule_check import ValidationResult
from agents.info_extract import ExtractionOutput
from services.gemini_client import GeminiClient

@dataclass
class RiskAnalysisOutput:
    """Represents the output of the risk analysis process."""
    risk_score: int  # A score from 0 (low risk) to 100 (high risk)
    risk_level: str  # "Low", "Medium", "High", "Critical"
    risk_factors: List[str]
    analysis_details: str
    source_uri: str
    # 新增：北美标准字段
    fraud_indicators: List[str]  # 欺诈指标
    siu_referral: bool  # 是否需要SIU调查
    auto_approve_eligible: bool  # 是否符合自动审批
    processing_priority: str  # "Expedited", "Standard", "Enhanced_Review"
    estimated_settlement_range: Optional[Dict[str, float]]  # 预估理赔金额范围

class RiskAnalysisAgent(BaseAgent):
    """
    An agent that analyzes validation results and extracted data to assign a risk score.
    Enhanced with North American insurance industry standards.
    """

    def __init__(self, gemini_client: GeminiClient):
        """Initialize the risk analysis agent with AI capabilities."""
        self._gemini = gemini_client
        
        # 北美保险业标准阈值
        self.auto_approve_threshold = 25  # 自动审批阈值
        self.siu_referral_threshold = 75  # SIU调查阈值
        self.expedited_threshold = 15     # 快速处理阈值

    def process(self, extraction_output: ExtractionOutput, validation_result: ValidationResult) -> RiskAnalysisOutput:
        """
        Calculates a risk score based on validation violations and extracted data.
        Enhanced with North American insurance standards.

        Args:
            extraction_output: The extracted claim data
            validation_result: The result from the RuleCheckAgent

        Returns:
            A RiskAnalysisOutput object with the calculated score and analysis
        """
        # Start with base risk assessment
        risk_score = 0
        risk_factors = []
        fraud_indicators = []
        
        # Analyze validation violations
        if not validation_result.is_valid:
            risk_score += 10
            risk_factors.extend(validation_result.violations)
            
            # Add weight for specific violations
            for violation in validation_result.violations:
                if "Missing required field" in violation:
                    risk_score += 20
                    fraud_indicators.append("Incomplete documentation")
                elif "Claim amount" in violation:
                    risk_score += 40  # High risk
                    fraud_indicators.append("Claim amount irregularity")
                elif "invalid format" in violation:
                    risk_score += 15

        # Enhanced AI analysis with North American fraud patterns
        extracted_data = validation_result.extracted_data if hasattr(validation_result, 'extracted_data') else extraction_output.extracted_data
        
        # 北美保险欺诈检测模式
        fraud_analysis = self._analyze_fraud_patterns(extracted_data)
        risk_score += fraud_analysis['score_adjustment']
        fraud_indicators.extend(fraud_analysis['indicators'])
        
        # Use AI to analyze the extracted data for additional risk factors
        claim_summary = f"""
        North American Insurance Claim Risk Analysis:
        
        Basic Information:
        - Claimant: {extracted_data.get('claimant_name', 'N/A')}
        - Policy Number: {extracted_data.get('policy_number', 'N/A')}
        - Claim Amount: {extracted_data.get('claim_amount', 'N/A')}
        - Date of Incident: {extracted_data.get('date_of_incident', 'N/A')}
        - Vehicle Details: {extracted_data.get('vehicle_details', 'N/A')}
        
        Validation Issues:
        {', '.join(validation_result.violations) if validation_result.violations else 'None'}
        
        Fraud Indicators Detected:
        {', '.join(fraud_indicators) if fraud_indicators else 'None'}
        """
        
        ai_prompt = f"""
        You are a senior insurance fraud investigator following North American insurance standards.
        Analyze this claim for fraud indicators, processing priority, and settlement recommendations.
        
        {claim_summary}
        
        Consider these North American insurance fraud patterns:
        1. Staged accidents and false claims
        2. Claim inflation and padding
        3. Identity theft and policy fraud
        4. Medical mill operations
        5. Organized fraud rings
        
        Provide analysis in this format:
        ADDITIONAL_FRAUD_INDICATORS: [list specific indicators or "None"]
        RISK_LEVEL: [Low/Medium/High/Critical]
        SIU_REFERRAL_NEEDED: [Yes/No with reason]
        PROCESSING_PRIORITY: [Expedited/Standard/Enhanced_Review]
        SETTLEMENT_ESTIMATE: [Low amount]-[High amount] or "Insufficient data"
        DETAILED_ANALYSIS: [comprehensive analysis]
        """
        
        try:
            ai_response = self._gemini.generate_content(prompt=ai_prompt)
            
            # Parse AI response
            analysis_results = self._parse_ai_response(ai_response)
            
            # Add AI-identified fraud indicators
            fraud_indicators.extend(analysis_results.get('fraud_indicators', []))
            
            # Adjust risk score based on AI assessment
            risk_level = analysis_results.get('risk_level', 'Medium')
            if risk_level.lower() == "critical":
                risk_score += 40
            elif risk_level.lower() == "high":
                risk_score += 30
            elif risk_level.lower() == "medium":
                risk_score += 15
            # Low adds nothing
            
            analysis_details = analysis_results.get('detailed_analysis', ai_response)
            siu_referral_needed = analysis_results.get('siu_referral', False)
            processing_priority = analysis_results.get('processing_priority', 'Standard')
            settlement_estimate = analysis_results.get('settlement_estimate', None)
            
        except Exception as e:
            # Fallback analysis if AI fails
            analysis_details = f"AI analysis failed: {str(e)}. Using basic rule-based analysis."
            risk_level = "Medium" if risk_score > 30 else "Low"
            siu_referral_needed = risk_score > self.siu_referral_threshold
            processing_priority = "Standard"
            settlement_estimate = None
        
        # Normalize score to be within 0-100
        final_score = min(risk_score, 100)
        
        # Determine final risk level based on score
        if final_score >= 85:
            final_risk_level = "Critical"
        elif final_score >= 70:
            final_risk_level = "High"
        elif final_score >= 40:
            final_risk_level = "Medium"
        else:
            final_risk_level = "Low"

        # Determine processing decisions
        auto_approve_eligible = final_score <= self.auto_approve_threshold and not fraud_indicators
        siu_referral = final_score >= self.siu_referral_threshold or siu_referral_needed
        
        if final_score <= self.expedited_threshold:
            processing_priority = "Expedited"
        elif final_score >= self.siu_referral_threshold:
            processing_priority = "Enhanced_Review"

        return RiskAnalysisOutput(
            risk_score=final_score,
            risk_level=final_risk_level,
            risk_factors=risk_factors,
            analysis_details=analysis_details,
            source_uri=extraction_output.source_uri,
            fraud_indicators=fraud_indicators,
            siu_referral=siu_referral,
            auto_approve_eligible=auto_approve_eligible,
            processing_priority=processing_priority,
            estimated_settlement_range=settlement_estimate
        )
    
    def _analyze_fraud_patterns(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析北美常见的保险欺诈模式"""
        score_adjustment = 0
        indicators = []
        
        claim_amount = extracted_data.get('claim_amount')
        if claim_amount:
            try:
                amount = float(str(claim_amount).replace('$', '').replace(',', ''))
                # 高额理赔增加风险
                if amount > 50000:
                    score_adjustment += 15
                    indicators.append("High-value claim requiring enhanced review")
                elif amount > 100000:
                    score_adjustment += 25
                    indicators.append("Very high-value claim - potential inflation")
            except (ValueError, TypeError):
                score_adjustment += 10
                indicators.append("Invalid claim amount format")
        
        # 检查时间因素
        incident_date = extracted_data.get('date_of_incident')
        if incident_date:
            # 可以添加时间相关的欺诈检测逻辑
            pass
        
        return {
            'score_adjustment': score_adjustment,
            'indicators': indicators
        }
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """解析AI响应"""
        results = {}
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            if line.startswith("ADDITIONAL_FRAUD_INDICATORS:"):
                indicators_text = line.split(":", 1)[1].strip()
                if indicators_text.lower() != "none":
                    results['fraud_indicators'] = [i.strip() for i in indicators_text.split(',')]
                else:
                    results['fraud_indicators'] = []
            elif line.startswith("RISK_LEVEL:"):
                results['risk_level'] = line.split(":", 1)[1].strip()
            elif line.startswith("SIU_REFERRAL_NEEDED:"):
                referral_text = line.split(":", 1)[1].strip().lower()
                results['siu_referral'] = referral_text.startswith('yes')
            elif line.startswith("PROCESSING_PRIORITY:"):
                results['processing_priority'] = line.split(":", 1)[1].strip()
            elif line.startswith("SETTLEMENT_ESTIMATE:"):
                estimate_text = line.split(":", 1)[1].strip()
                if "insufficient" not in estimate_text.lower():
                    # 尝试解析金额范围
                    try:
                        if '-' in estimate_text:
                            low, high = estimate_text.split('-')
                            results['settlement_estimate'] = {
                                'low': float(low.strip().replace('$', '').replace(',', '')),
                                'high': float(high.strip().replace('$', '').replace(',', ''))
                            }
                    except:
                        results['settlement_estimate'] = None
            elif line.startswith("DETAILED_ANALYSIS:"):
                results['detailed_analysis'] = line.split(":", 1)[1].strip()
        
        return results 