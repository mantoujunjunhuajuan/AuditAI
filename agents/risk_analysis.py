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
    Enhanced with North American insurance industry standards and collaborative capabilities.
    """

    def __init__(self, gemini_client: GeminiClient):
        """Initialize the risk analysis agent with AI capabilities."""
        self._gemini = gemini_client
        
        # 北美保险业标准阈值
        self.auto_approve_threshold = 25  # 自动审批阈值
        self.siu_referral_threshold = 75  # SIU调查阈值
        self.expedited_threshold = 15     # 快速处理阈值
        
        # 协作相关配置
        self.collaboration_confidence_threshold = 0.7  # 协作触发阈值
        self.collaboration_enabled = True

    def process(self, extraction_output: ExtractionOutput, validation_result: ValidationResult, doc_intel_output=None, info_extract_agent=None) -> RiskAnalysisOutput:
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
        
        # Get document type information for specialized risk assessment
        doc_type = getattr(doc_intel_output, 'doc_type', 'unknown') if doc_intel_output else 'unknown'
        document_metadata = getattr(doc_intel_output, 'metadata', {}) if doc_intel_output else {}
        confidence_score = getattr(doc_intel_output, 'confidence_score', 1.0) if doc_intel_output else 1.0
        
        # 北美保险欺诈检测模式
        fraud_analysis = self._analyze_fraud_patterns(extracted_data)
        risk_score += fraud_analysis['score_adjustment']
        fraud_indicators.extend(fraud_analysis['indicators'])
        
        # Document type specific risk adjustments
        doc_type_analysis = self._analyze_document_type_risks(doc_type, document_metadata, confidence_score)
        risk_score += doc_type_analysis['score_adjustment']
        fraud_indicators.extend(doc_type_analysis['indicators'])
        risk_factors.extend(doc_type_analysis['risk_factors'])
        
        # Use AI to analyze the extracted data for additional risk factors
        claim_summary = f"""
        North American Insurance Claim Risk Analysis:
        
        Document Information:
        - Document Type: {doc_type}
        - Processing Confidence: {confidence_score:.2f}
        - Processing Method: {document_metadata.get('processing_method', 'standard')}
        
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
        
        Document Type Specific Considerations:
        - If image/scanned document: Look for signs of tampering, alterations, or poor quality that might indicate fraud
        - If medical imaging: Ensure medical necessity and consistency with claim
        - If Word document: Consider ease of digital manipulation
        - If corrupted/error: High suspicion due to document integrity issues
        
        Low processing confidence (< 0.8) should increase scrutiny.
        
        Provide analysis in this format:
        ADDITIONAL_FRAUD_INDICATORS: [list specific indicators or "None"]
        RISK_LEVEL: [Low/Medium/High/Critical]
        SIU_REFERRAL_NEEDED: [Yes/No with reason]
        PROCESSING_PRIORITY: [Expedited/Standard/Enhanced_Review]
        SETTLEMENT_ESTIMATE: [Low amount]-[High amount] or "Insufficient data"
        DETAILED_ANALYSIS: [comprehensive analysis including document type assessment]
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
            
            # 🤝 COLLABORATIVE INTELLIGENCE: Check if we need more information
            collaboration_result = self._evaluate_collaboration_need(
                extracted_data, analysis_results, doc_intel_output, info_extract_agent
            )
            
            if collaboration_result['collaboration_performed']:
                # Update analysis with collaborative insights
                additional_info = collaboration_result['additional_data']
                
                # Re-evaluate risk based on new information
                if additional_info:
                    collaboration_assessment = self._reassess_with_collaboration(
                        extracted_data, additional_info, analysis_results
                    )
                    
                    # Update key metrics based on collaborative findings
                    risk_score += collaboration_assessment['risk_adjustment']
                    fraud_indicators.extend(collaboration_assessment['new_indicators'])
                    analysis_details += f"\n\n🤝 COLLABORATIVE ANALYSIS:\n{collaboration_assessment['analysis']}"
            
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
    
    def _analyze_document_type_risks(self, doc_type: str, metadata: Dict[str, Any], confidence_score: float) -> Dict[str, Any]:
        """
        Analyze risks specific to different document types
        """
        score_adjustment = 0
        indicators = []
        risk_factors = []
        
        # Base confidence adjustment
        if confidence_score < 0.7:
            score_adjustment += 15
            risk_factors.append(f"Low document processing confidence: {confidence_score:.2f}")
        
        # Document type specific risks
        if doc_type == "image_document":
            score_adjustment += 10
            risk_factors.append("Image-based document requires enhanced scrutiny")
            
            # Check image quality indicators
            if metadata.get('file_size_kb', 0) < 100:
                score_adjustment += 15
                indicators.append("Suspiciously small image file size")
            
            image_quality = metadata.get('image_quality_assessment', '').lower()
            if 'poor' in image_quality or 'blurry' in image_quality:
                score_adjustment += 20
                indicators.append("Poor image quality may indicate tampering")
                
        elif doc_type == "image_pdf":
            score_adjustment += 15
            risk_factors.append("Scanned/image-based PDF requires manual review")
            indicators.append("Document may contain handwritten alterations")
            
        elif doc_type in ["word_document", "insurance_word_document"]:
            score_adjustment += 5
            risk_factors.append("Digital document format allows easy modification")
            
            # Check for version information
            if not metadata.get('document_version'):
                score_adjustment += 10
                indicators.append("No document version tracking available")
                
        elif doc_type == "dicom_image":
            score_adjustment += 25  # Medical imaging requires special handling
            risk_factors.append("Medical imaging requires specialized medical review")
            indicators.append("HIPAA compliance verification required")
            
            if metadata.get('privacy_sensitive'):
                risk_factors.append("Contains sensitive medical information")
                
        elif doc_type == "medical_imaging":
            score_adjustment += 20
            risk_factors.append("Medical documentation requires clinical verification")
            
        elif doc_type in ["invalid_pdf", "corrupted_pdf"]:
            score_adjustment += 40
            indicators.append("Corrupted or invalid document format")
            risk_factors.append("Document integrity issues detected")
            
        elif doc_type == "unsupported":
            score_adjustment += 30
            indicators.append("Unsupported file format submitted")
            risk_factors.append("Non-standard document type raises suspicion")
            
        elif doc_type == "error":
            score_adjustment += 35
            indicators.append("Document processing failed")
            risk_factors.append("Technical processing errors require investigation")
        
        # Processing method risks
        processing_method = metadata.get('processing_method', '')
        if processing_method == 'ocr_vision':
            score_adjustment += 10
            risk_factors.append("OCR-based extraction may miss subtle details")
            
        if metadata.get('requires_manual_review'):
            score_adjustment += 15
            risk_factors.append("Document flagged for mandatory manual review")
            
        # File format anomalies
        if metadata.get('error'):
            score_adjustment += 25
            indicators.append(f"Processing error: {metadata.get('error')}")
        
        return {
            'score_adjustment': score_adjustment,
            'indicators': indicators,
            'risk_factors': risk_factors
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
    
    def _evaluate_collaboration_need(self, extracted_data, analysis_results, doc_intel_output, info_extract_agent):
        """
        Evaluate whether collaborative information extraction is needed.
        
        Returns:
            Dict containing collaboration decision and results
        """
        if not self.collaboration_enabled or not info_extract_agent or not doc_intel_output:
            return {'collaboration_performed': False, 'reason': 'Collaboration not available'}
        
        # Identify potential information gaps
        critical_fields = ['claim_amount', 'date_of_incident', 'claimant_name', 'policy_number']
        missing_fields = []
        unclear_fields = []
        
        for field in critical_fields:
            value = extracted_data.get(field)
            if not value or value == "N/A" or value is None:
                missing_fields.append(field)
            elif isinstance(value, str) and ("unclear" in value.lower() or "unknown" in value.lower()):
                unclear_fields.append(field)
        
        # Check if AI analysis confidence is low
        risk_level = analysis_results.get('risk_level', 'Medium')
        confidence_indicators = [
            len(missing_fields) > 0,
            len(unclear_fields) > 0,
            risk_level.lower() == 'medium',  # Medium risk often indicates uncertainty
            'insufficient' in analysis_results.get('detailed_analysis', '').lower()
        ]
        
        confidence_score = 1.0 - (sum(confidence_indicators) / len(confidence_indicators))
        
        if confidence_score < self.collaboration_confidence_threshold:
            # Trigger collaboration
            focus_areas = missing_fields + unclear_fields
            if not focus_areas:
                focus_areas = ['claim_details', 'incident_circumstances', 'claimant_history']
            
            context = f"""
            Risk Analysis Agent requesting collaborative extraction.
            Current confidence: {confidence_score:.2f}
            Missing fields: {missing_fields}
            Unclear fields: {unclear_fields}
            Current risk assessment: {risk_level}
            
            Need deeper information to improve risk assessment accuracy.
            """
            
            print(f"🤝 RiskAnalysisAgent requesting collaboration with InfoExtractAgent")
            print(f"   Focus areas: {focus_areas}")
            print(f"   Confidence: {confidence_score:.2f}")
            print("   📊 Multi-Agent Collaboration Network Activated")
            
            try:
                collaboration_data = info_extract_agent.collaborative_extract(
                    source_document=doc_intel_output,
                    focus_areas=focus_areas,
                    context=context
                )
                
                return {
                    'collaboration_performed': True,
                    'additional_data': collaboration_data,
                    'focus_areas': focus_areas,
                    'confidence_before': confidence_score
                }
                
            except Exception as e:
                print(f"❌ Collaboration failed: {e}")
                return {
                    'collaboration_performed': False,
                    'error': str(e),
                    'reason': 'Collaboration attempt failed'
                }
        
        return {
            'collaboration_performed': False,
            'reason': f'Confidence sufficient: {confidence_score:.2f}'
        }
    
    def _reassess_with_collaboration(self, original_data, collaboration_data, original_analysis):
        """
        Reassess risk based on collaborative findings.
        
        Returns:
            Dict containing risk adjustments and new insights
        """
        risk_adjustment = 0
        new_indicators = []
        analysis_text = "Collaborative extraction provided additional insights:\n"
        
        if not collaboration_data.get('collaboration_success'):
            return {
                'risk_adjustment': 5,  # Small penalty for failed collaboration
                'new_indicators': ['Collaboration extraction failed'],
                'analysis': 'Collaborative extraction failed, using original assessment'
            }
        
        extracted_data = collaboration_data.get('extracted_data', {})
        
        for field, details in extracted_data.items():
            if not isinstance(details, dict):
                continue
                
            confidence = details.get('confidence', 'Low')
            value = details.get('value')
            red_flags = details.get('red_flags', [])
            context = details.get('context', '')
            
            analysis_text += f"- {field}: {value} (Confidence: {confidence})\n"
            
            if red_flags:
                risk_adjustment += len(red_flags) * 10
                new_indicators.extend(red_flags)
                analysis_text += f"  Red flags: {', '.join(red_flags)}\n"
            
            if confidence.lower() == 'low':
                risk_adjustment += 5
                analysis_text += f"  Note: Low confidence in extracted data\n"
            
            if value and original_data.get(field) != value:
                analysis_text += f"  Updated from original: {original_data.get(field)} → {value}\n"
                
                # If we found a previously missing critical field
                if not original_data.get(field) and field in ['claim_amount', 'policy_number']:
                    risk_adjustment -= 10  # Reduce risk for having complete info
        
        # Cap the risk adjustment
        risk_adjustment = max(-20, min(30, risk_adjustment))
        
        return {
            'risk_adjustment': risk_adjustment,
            'new_indicators': new_indicators,
            'analysis': analysis_text
        } 