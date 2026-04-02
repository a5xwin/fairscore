from app.db.supabase import supabase
from datetime import datetime
import sys
import os
import logging
import json
import hashlib
import re
from uuid import UUID


logger = logging.getLogger(__name__)


_INSIGHTS_CACHE_TABLE = "borrower_score_insights_cache"
_INSIGHTS_CACHE_MEMORY = {}


class ExplanationServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

# Add parent directory to path for Utilities import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
try:
    from models.Utilities.prediction import CreditScorePredictor
    ML_PREDICTOR_AVAILABLE = True
except Exception as e:
    print(f"Warning: CreditScorePredictor not available: {e}")
    ML_PREDICTOR_AVAILABLE = False

# Initialize the predictor once at module level
_credit_predictor = None
if ML_PREDICTOR_AVAILABLE:
    try:
        _credit_predictor = CreditScorePredictor()
    except Exception as e:
        print(f"Warning: Failed to initialize CreditScorePredictor: {e}")
        ML_PREDICTOR_AVAILABLE = False

# -----------------------------
# Helpers
# -----------------------------
def to_months(years: int, months: int) -> int:
    return years * 12 + months


def calculate_ltv(loan_amount: float, asset_value: float) -> float:
    if asset_value <= 0:
        return 0
    return (loan_amount / asset_value) * 100


def validate_loan_and_asset_values(loan_amount: float, asset_value: float) -> None:
    if asset_value <= 0:
        raise ValueError("Asset value must be greater than 0.")
    if loan_amount <= 0:
        raise ValueError("Loan amount must be greater than 0.")
    if loan_amount > asset_value:
        raise ValueError("Loan amount cannot exceed asset value.")


# -----------------------------
# ML PREDICTION for Credit Score
# -----------------------------
def generate_credit_score(dob, income, credit_history_months, loan_no, state, city, 
                         employment_profile, occupation, asset_value, loan_amount, 
                         existing_customer="yes"):
    """
    Generate credit score using the ML model if available, otherwise use stub.
    
    Parameters:
    -----------
    dob : str or datetime - Date of birth in YYYY-MM-DD format
    income : float - Annual income
    credit_history_months : int - Credit history in months
    loan_no : int - Number of existing loans
    state : str - State of residence
    city : str - City of residence
    employment_profile : str - Employment profile (e.g., 'Salaried', 'Self-employed')
    occupation : str - Occupation
    asset_value : float - Asset value
    loan_amount : float - Loan amount
    existing_customer : str - 'yes' or 'no'
    
    Returns:
    --------
    int - Credit score between 300 and 900
    """
    if ML_PREDICTOR_AVAILABLE and _credit_predictor is not None:
        try:
            # Calculate age from DOB
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d')
            else:
                dob_date = dob
            
            today = datetime.now()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            # Calculate LTV ratio
            ltv_ratio = (loan_amount / asset_value) if asset_value > 0 else 0
            
            # Prepare data for prediction
            credit_history_years = credit_history_months / 12
            
            prediction_data = {
                'Age': age,
                'Income': income,
                'Credit History Length': credit_history_years,
                'Number of Existing Loans': loan_no,
                'Existing Customer': 'Yes' if existing_customer.lower() == 'yes' else 'No',
                'State': state,
                'City': city,
                'LTV Ratio': ltv_ratio,
                'Employment Profile': employment_profile,
                'Occupation': occupation
            }
            
            # Get prediction from ML model
            result = _credit_predictor.predict(prediction_data)
            score = int(result['prediction'])
            
            # Ensure score is within valid range
            return int(min(max(score, 300), 900))
        
        except Exception as e:
            print(f"Error in ML prediction: {e}, falling back to stub implementation")
            # Fall back to stub implementation
            pass
    
    # Stub implementation (fallback)
    score = 600
    score += min(income / 10000, 120)
    score += min(credit_history_months / 12, 50)
    score -= loan_no * 15
    return int(min(max(score, 300), 900))


def risk_bucket(score: int):
    if score >= 750:
        return "low"
    elif score >= 650:
        return "medium"
    return "high"


def estimated_credit_line(score, income, ltv):
    base = income * 12 * 0.35
    score_factor = 1.3 if score >= 750 else 1.0 if score >= 650 else 0.6
    ltv_penalty = 0.7 if ltv > 80 else 1.0
    return int(base * score_factor * ltv_penalty)


def _ensure_predictor_available():
    if not ML_PREDICTOR_AVAILABLE or _credit_predictor is None:
        raise ExplanationServiceError(503, "ML explanation service is unavailable")


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _compute_prediction_fingerprint(prediction_data):
    normalized = json.dumps(prediction_data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _read_insights_cache(user_id: str):
    memory_row = _INSIGHTS_CACHE_MEMORY.get(user_id)

    try:
        res = supabase.table(_INSIGHTS_CACHE_TABLE) \
            .select("user_id, profile_fingerprint, reasons_payload, advice_payload") \
            .eq("user_id", user_id) \
            .limit(1) \
            .execute()
        records = res.data or []
        if records:
            record = records[0]
            _INSIGHTS_CACHE_MEMORY[user_id] = record
            return record
    except Exception as exc:
        logger.debug("Insights cache table unavailable; using in-memory cache: %s", exc)

    return memory_row


def _write_insights_cache(user_id: str, fingerprint: str, reasons_payload=None, advice_payload=None):
    existing = _read_insights_cache(user_id) or {}
    row = {
        "user_id": user_id,
        "profile_fingerprint": fingerprint,
        "reasons_payload": reasons_payload if reasons_payload is not None else existing.get("reasons_payload"),
        "advice_payload": advice_payload if advice_payload is not None else existing.get("advice_payload"),
    }

    _INSIGHTS_CACHE_MEMORY[user_id] = row

    try:
        supabase.table(_INSIGHTS_CACHE_TABLE).upsert(row, on_conflict="user_id").execute()
    except Exception as exc:
        logger.debug("Failed to persist insights cache row in Supabase: %s", exc)


def _invalidate_insights_cache(user_id: str):
    _INSIGHTS_CACHE_MEMORY.pop(user_id, None)

    try:
        supabase.table(_INSIGHTS_CACHE_TABLE).delete().eq("user_id", user_id).execute()
    except Exception as exc:
        logger.debug("Failed to invalidate Supabase insights cache row: %s", exc)


def _extract_table_records(table):
    if table is None:
        return []
    if hasattr(table, "to_dict"):
        try:
            return table.to_dict(orient="records")
        except TypeError:
            pass
    if isinstance(table, list):
        return table
    return []


def _format_feature_label(raw_feature: str) -> str:
    if not isinstance(raw_feature, str):
        return "Unknown"
    if "<=" in raw_feature or ">=" in raw_feature or "<" in raw_feature or ">" in raw_feature:
        return raw_feature
    return raw_feature.replace("_", " ")


def _extract_json_array(text: str):
    if not isinstance(text, str):
        return []

    cleaned = text.strip()
    if not cleaned:
        return []

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    json_str = cleaned[start:end + 1]
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _extract_json_object(text: str):
    if not isinstance(text, str):
        return {}

    cleaned = text.strip()
    if not cleaned:
        return {}

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    json_str = cleaned[start:end + 1]
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _fallback_humanize_lime_rule(rule_text: str):
    cleaned_rule = _format_feature_label(rule_text)
    match = re.match(r"^(.*?)(<=|>=|<|>|=)\s*(-?\d+(?:\.\d+)?)$", cleaned_rule)
    if not match:
        return cleaned_rule

    feature, operator, raw_value = match.groups()
    feature = feature.strip()

    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        numeric_value = None

    has_model_scaled_value = numeric_value is not None and (numeric_value < 0 or numeric_value % 1 != 0)
    if has_model_scaled_value:
        if operator in ["<=", "<"]:
            return f"{feature} is on the lower side"
        if operator in [">=", ">"]:
            return f"{feature} is on the higher side"
        return f"{feature} is around this level"

    value = str(int(numeric_value)) if numeric_value is not None and numeric_value.is_integer() else raw_value
    if operator == "<=":
        return f"{feature} is {value} or below"
    if operator == ">=":
        return f"{feature} is {value} or above"
    if operator == "<":
        return f"{feature} is below {value}"
    if operator == ">":
        return f"{feature} is above {value}"
    return f"{feature} is {value}"


def _extract_rule_feature_and_operator(raw_rule: str):
    cleaned_rule = _format_feature_label(raw_rule)
    match = re.match(r"^(.*?)(<=|>=|<|>|=)\s*(-?\d+(?:\.\d+)?)$", cleaned_rule)
    if not match:
        return str(cleaned_rule or "").lower(), None
    feature, operator, _ = match.groups()
    return str(feature or "").strip().lower(), operator


def _resolve_lime_effect_by_domain(raw_rule: str, fallback_effect: str):
    feature, operator = _extract_rule_feature_and_operator(raw_rule)
    if operator is None:
        return fallback_effect

    if operator in ["<=", "<"]:
        trend = "lower"
    elif operator in [">=", ">"]:
        trend = "higher"
    else:
        trend = "neutral"

    if trend == "neutral":
        return fallback_effect

    lower_is_better_features = [
        "number of existing loans",
        "existing loans",
        "loan count",
        "debt to income ratio",
        "dti",
        "utilization",
        "late payment",
        "overdue",
        "ltv ratio",
    ]

    higher_is_better_features = [
        "credit history length",
        "income",
        "monthly income",
        "savings",
        "payment history",
    ]

    lower_is_better = any(token in feature for token in lower_is_better_features)
    higher_is_better = any(token in feature for token in higher_is_better_features)

    if lower_is_better:
        return "helps" if trend == "lower" else "hurts"
    if higher_is_better:
        return "helps" if trend == "higher" else "hurts"

    return fallback_effect


def _fallback_useful_lime_rule(rule_text: str, impact: float):
    lowered = str(rule_text or "").lower()
    non_actionable_tokens = ["city", "existing customer", "customer id", "user id", "id"]
    if any(token in lowered for token in non_actionable_tokens):
        return False
    return abs(_to_float(impact)) >= 0.1


def _ensure_non_empty_lime_rules(filtered_rules, raw_rules):
    if filtered_rules:
        return filtered_rules

    fallback = []
    for rule in raw_rules[:4]:
        source_rule = rule.get("rawRule") or rule.get("rule", "")
        source_summary = rule.get("baseSummary") or rule.get("summary", "")
        effect = rule.get("effect", "hurts")
        fallback.append({
            **rule,
            "rule": source_rule,
            "summary": source_summary or f"{source_rule} {'improves' if effect == 'helps' else 'reduces'} your score.",
            "useful": True,
        })
    return fallback


def _normalize_feature_key(feature_name: str):
    return str(feature_name or "").replace("_", " ").strip().lower()


def _canonical_reason_key(feature_name: str):
    normalized = _normalize_feature_key(feature_name)
    if not normalized:
        return normalized

    alias_map = {
        "having no existing loans": "existing loans",
        "no existing loans": "existing loans",
        "number of existing loans": "existing loans",
        "loan no": "existing loans",
        "loan count": "existing loans",
        "credit history length": "credit history",
        "credit history": "credit history",
        "monthly income": "income",
    }

    return alias_map.get(normalized, normalized)


def _match_reason_feature_key(lime_feature: str, shap_features_by_key):
    normalized_lime = _canonical_reason_key(lime_feature)
    if not normalized_lime:
        return None

    if normalized_lime in shap_features_by_key:
        return normalized_lime

    for shap_key in shap_features_by_key.keys():
        if normalized_lime in shap_key or shap_key in normalized_lime:
            return shap_key

    return None


def _build_combined_score_reasons(shap_factors, lime_rules):
    shap_factors = shap_factors or []
    lime_rules = lime_rules or []

    reasons_by_key = {}

    for factor in shap_factors:
        feature_name = str(factor.get("feature", "")).strip()
        if not feature_name:
            continue

        key = _canonical_reason_key(feature_name)
        impact = abs(_to_float(factor.get("impact"), 0.0))

        reasons_by_key[key] = {
            "feature": feature_name,
            "direction": factor.get("direction", "hurts"),
            "shapImpact": impact,
            "ruleImpact": 0.0,
            "summary": str(factor.get("summary") or "").strip(),
            "supportingRules": [],
            "helpsWeight": impact if factor.get("direction", "hurts") == "helps" else 0.0,
            "hurtsWeight": impact if factor.get("direction", "hurts") == "hurts" else 0.0,
        }

    for rule in lime_rules:
        rule_text = str(rule.get("rule") or "").strip()
        if not rule_text:
            continue

        lime_feature, _ = _extract_rule_feature_and_operator(rule_text)
        matched_key = _match_reason_feature_key(lime_feature, reasons_by_key)

        if matched_key is None:
            matched_key = _canonical_reason_key(lime_feature)
            if matched_key not in reasons_by_key:
                reasons_by_key[matched_key] = {
                    "feature": _format_feature_label(lime_feature.title()),
                    "direction": rule.get("effect", "hurts"),
                    "shapImpact": 0.0,
                    "ruleImpact": 0.0,
                    "summary": "",
                    "supportingRules": [],
                    "helpsWeight": 0.0,
                    "hurtsWeight": 0.0,
                }

        impact = abs(_to_float(rule.get("impact"), 0.0))
        reasons_by_key[matched_key]["ruleImpact"] += impact
        if rule.get("effect", "hurts") == "helps":
            reasons_by_key[matched_key]["helpsWeight"] += impact
        else:
            reasons_by_key[matched_key]["hurtsWeight"] += impact
        reasons_by_key[matched_key]["supportingRules"].append({
            "rule": rule_text,
            "effect": rule.get("effect", "hurts"),
            "impact": impact,
            "summary": str(rule.get("summary") or "").strip(),
        })

    combined_reasons = []
    for item in reasons_by_key.values():
        direction = "helps" if item["helpsWeight"] >= item["hurtsWeight"] else "hurts"
        component_impacts = []
        if item["shapImpact"] > 0:
            component_impacts.append(item["shapImpact"])
        component_impacts.extend([
            abs(_to_float(rule.get("impact"), 0.0))
            for rule in item["supportingRules"]
            if abs(_to_float(rule.get("impact"), 0.0)) > 0
        ])
        total_impact = sum(component_impacts)
        average_impact = round(total_impact / len(component_impacts), 4) if component_impacts else 0.0
        rule_preview = [r.get("rule", "") for r in item["supportingRules"][:2] if r.get("rule")]

        if item["summary"] and rule_preview:
            explanation = (
                f"{item['summary']} Supported by profile patterns such as: "
                f"{'; '.join(rule_preview)}."
            )
        elif item["summary"]:
            explanation = item["summary"]
        elif rule_preview:
            explanation = f"Key profile patterns include: {'; '.join(rule_preview)}."
        else:
            explanation = "This factor materially influences your score."

        combined_reasons.append({
            "feature": item["feature"],
            "direction": direction,
            "impact": average_impact,
            "totalImpact": round(total_impact, 4),
            "signalCount": len(component_impacts),
            "explanation": explanation,
            "shapSummary": item["summary"],
            "supportingRules": item["supportingRules"],
        })

    combined_reasons.sort(key=lambda reason: abs(_to_float(reason.get("impact"), 0.0)), reverse=True)

    top_negative = [r.get("feature") for r in combined_reasons if r.get("direction") == "hurts"][:3]
    top_positive = [r.get("feature") for r in combined_reasons if r.get("direction") == "helps"][:2]

    overview = (
        "Top reasons behind your score are based on both overall feature influence and profile-specific rules. "
        f"Main downward pressure: {', '.join(top_negative) if top_negative else 'none identified'}. "
        f"Main supporting strengths: {', '.join(top_positive) if top_positive else 'none identified'}."
    )

    return {
        "overview": overview,
        "combinedReasons": combined_reasons[:6],
    }


def _build_score_reasons_with_gemini(base_reasons_payload, prediction_data, api_key: str):
    if not api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        base_overview = str(base_reasons_payload.get("overview") or "").strip()
        base_reasons = base_reasons_payload.get("combinedReasons") or []

        prompt = (
            "You are a credit-risk explanation writer for non-technical users. "
            "Given prediction context and preliminary reason items, produce a cleaner deduplicated reason list. "
            "Merge semantically duplicate items (example: 'No Existing Loans' and 'Number of Existing Loans') into one item. "
            "Keep the direction accurate (helps/hurts). Keep impact as a number close to the input values. "
            "Write concise, plain-English explanations. "
            "Return ONLY JSON object with keys: overview (string), combinedReasons (array). "
            "Each combinedReasons item must have: feature (string), direction (helps|hurts), impact (number), explanation (string). "
            "No markdown, no extra keys.\n\n"
            f"Borrower context: {prediction_data}\n"
            f"Base overview: {base_overview}\n"
            f"Base reasons: {base_reasons}"
        )

        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, "text") else str(response)
        parsed = _extract_json_object(response_text)
        if not parsed:
            return None

        overview = str(parsed.get("overview") or "").strip() or base_overview
        raw_reasons = parsed.get("combinedReasons")
        if not isinstance(raw_reasons, list):
            return None

        cleaned_reasons = []
        seen_keys = set()

        for reason in raw_reasons:
            if not isinstance(reason, dict):
                continue
            feature = str(reason.get("feature") or "").strip()
            if not feature:
                continue

            canonical_key = _canonical_reason_key(feature)
            if canonical_key in seen_keys:
                continue
            seen_keys.add(canonical_key)

            direction = str(reason.get("direction") or "hurts").strip().lower()
            if direction not in ["helps", "hurts"]:
                direction = "hurts"

            impact = abs(_to_float(reason.get("impact"), 0.0))
            explanation = str(reason.get("explanation") or "").strip()
            if not explanation:
                explanation = "This factor has a meaningful influence on your score."

            cleaned_reasons.append({
                "feature": feature,
                "direction": direction,
                "impact": round(impact, 4),
                "totalImpact": round(impact, 4),
                "signalCount": 1,
                "explanation": explanation,
                "shapSummary": "",
                "supportingRules": [],
            })

        if not cleaned_reasons:
            return None

        cleaned_reasons.sort(key=lambda reason: abs(_to_float(reason.get("impact"), 0.0)), reverse=True)

        return {
            "overview": overview,
            "combinedReasons": cleaned_reasons[:6],
        }
    except Exception as exc:
        logger.warning("Gemini reason synthesis failed, using fallback reasons: %s", exc)
        return None


def _simplify_lime_rules_with_gemini(rules, prediction_data, api_key: str):
    if not api_key or not rules:
        return []

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt_payload = []
        for index, rule in enumerate(rules):
            prompt_payload.append({
                "index": index,
                "rule": rule.get("rule", ""),
                "effect": rule.get("effect", "hurts"),
                "impact": rule.get("impact", 0.0),
                "summary": rule.get("summary", ""),
            })

        prompt = (
            "You are rewriting credit-score rule explanations for non-technical users. "
            "Rewrite each item in simple plain English that any common person can understand. "
            "Do not use symbols like <=, >=, <, >, = or model-scaled numeric thresholds unless clearly meaningful. "
            "Filter out vague or non-actionable items as useful=false (for example pure location/category labels). "
            "Keep the response strictly as a JSON array with one object per input row and fields: "
            "index (number), readable_rule (string), readable_summary (string), useful (boolean), effect (helps|hurts). "
            "Do not include markdown or extra keys.\n\n"
            f"Borrower context: {prediction_data}\n"
            f"Rules: {prompt_payload}"
        )

        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, "text") else str(response)
        parsed = _extract_json_array(response_text)
        if not parsed:
            return []

        normalized = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            idx = item.get("index")
            if not isinstance(idx, int):
                continue
            effect = str(item.get("effect", "")).strip().lower()
            if effect not in ["helps", "hurts"]:
                effect = "hurts"
            normalized.append({
                "index": idx,
                "readable_rule": str(item.get("readable_rule", "")).strip(),
                "readable_summary": str(item.get("readable_summary", "")).strip(),
                "useful": bool(item.get("useful", True)),
                "effect": effect,
            })

        return normalized
    except Exception as exc:
        logger.warning("Gemini LIME simplification failed: %s", exc)
        return []


def _build_tip_from_feature(feature_name: str):
    tips_map = {
        "Number of Existing Loans": "Reducing the number of active loans can improve your score over time.",
        "LTV Ratio": "Lowering the loan-to-value ratio by increasing down payment can reduce risk.",
        "Income": "A higher and stable income generally helps creditworthiness.",
        "Credit History Length": "Maintaining older active credit accounts can improve history length.",
        "Existing Customer": "Keeping a healthy repayment track record with your bank helps trust.",
    }
    return tips_map.get(feature_name)


def _format_shap_response(raw_shap):
    feature_names = raw_shap.get("feature_names") or []
    shap_values = raw_shap.get("shap_values")
    sample_shap_values = []

    if shap_values is not None:
        try:
            sample_shap_values = [float(v) for v in shap_values[0]]
        except Exception:
            sample_shap_values = []

    shap_by_feature = {}
    for idx, feature_name in enumerate(feature_names):
        if idx < len(sample_shap_values):
            shap_by_feature[feature_name] = sample_shap_values[idx]

    feature_rows = _extract_table_records(raw_shap.get("feature_importance"))
    top_factors = []

    for row in feature_rows[:8]:
        feature_name = row.get("Feature")
        if not feature_name:
            continue
        raw_contribution = shap_by_feature.get(feature_name)
        if raw_contribution is None:
            raw_contribution = _to_float(row.get("SHAP_Importance"), 0.0)

        direction = "helps" if raw_contribution >= 0 else "hurts"
        impact = abs(_to_float(raw_contribution))
        top_factors.append({
            "feature": _format_feature_label(feature_name),
            "direction": direction,
            "impact": round(impact, 4),
            "summary": f"{_format_feature_label(feature_name)} {direction} your score.",
        })

    prediction = _to_float(raw_shap.get("prediction"))
    return {
        "prediction": prediction,
        "topFactors": top_factors,
        "model": "shap",
    }


def _format_lime_response(raw_lime, prediction_data=None, api_key: str = ""):
    feature_rows = _extract_table_records(raw_lime.get("feature_contributions"))
    rules = []

    for row in feature_rows[:8]:
        rule = row.get("Feature_Rule")
        contribution = _to_float(row.get("Contribution"), 0.0)
        if not rule:
            continue
        base_rule = _format_feature_label(rule)
        base_effect = "helps" if contribution >= 0 else "hurts"
        resolved_effect = _resolve_lime_effect_by_domain(base_rule, base_effect)
        rules.append({
            "rule": base_rule,
            "effect": resolved_effect,
            "impact": round(abs(contribution), 4),
            "summary": f"{base_rule} {'improves' if resolved_effect == 'helps' else 'reduces'} your score.",
            "baseSummary": f"{base_rule} {'improves' if resolved_effect == 'helps' else 'reduces'} your score.",
            "rawRule": base_rule,
            "useful": _fallback_useful_lime_rule(base_rule, contribution),
        })

    raw_rules_snapshot = [dict(rule) for rule in rules]

    gemini_rows = _simplify_lime_rules_with_gemini(rules, prediction_data or {}, api_key)
    if gemini_rows:
        by_index = {item["index"]: item for item in gemini_rows}
        updated_rules = []
        for idx, rule in enumerate(rules):
            rewritten = by_index.get(idx)
            if rewritten:
                readable_rule = rewritten.get("readable_rule") or _fallback_humanize_lime_rule(rule.get("rule", ""))
                incoming_effect = rewritten.get("effect", rule.get("effect", "hurts"))
                final_effect = _resolve_lime_effect_by_domain(rule.get("rawRule", rule.get("rule", "")), incoming_effect)
                rule["rule"] = readable_rule
                rule["summary"] = f"{readable_rule} {'improves' if final_effect == 'helps' else 'reduces'} your score."
                rule["effect"] = final_effect
                rule["useful"] = bool(rewritten.get("useful", rule.get("useful", True)))
            else:
                source_rule = rule.get("rawRule") or rule.get("rule", "")
                source_summary = rule.get("baseSummary") or rule.get("summary", "")
                fallback_effect = _resolve_lime_effect_by_domain(source_rule, rule.get("effect", "hurts"))
                rule["rule"] = source_rule
                rule["effect"] = fallback_effect
                rule["summary"] = source_summary or f"{source_rule} {'improves' if fallback_effect == 'helps' else 'reduces'} your score."
                rule["useful"] = _fallback_useful_lime_rule(source_rule, rule.get("impact", 0.0))

            if rule.get("useful", True):
                updated_rules.append(rule)
        rules = _ensure_non_empty_lime_rules(updated_rules, raw_rules_snapshot)
    else:
        fallback_rules = []
        for rule in rules:
            source_rule = rule.get("rawRule") or rule.get("rule", "")
            source_summary = rule.get("baseSummary") or rule.get("summary", "")
            fallback_effect = _resolve_lime_effect_by_domain(source_rule, rule.get("effect", "hurts"))
            rule["rule"] = source_rule
            rule["effect"] = fallback_effect
            rule["summary"] = source_summary or f"{source_rule} {'improves' if fallback_effect == 'helps' else 'reduces'} your score."
            rule["useful"] = _fallback_useful_lime_rule(source_rule, rule.get("impact", 0.0))
            if rule.get("useful", True):
                fallback_rules.append(rule)
        rules = _ensure_non_empty_lime_rules(fallback_rules, raw_rules_snapshot)

    prediction = _to_float(raw_lime.get("prediction"))
    return {
        "prediction": prediction,
        "rules": rules,
        "model": "lime",
    }


def _build_fallback_advice(prediction_data, shap_response, lime_response):
    tips = []

    for factor in shap_response.get("topFactors", []):
        if factor.get("direction") != "hurts":
            continue
        tip = _build_tip_from_feature(factor.get("feature"))
        if tip and tip not in tips:
            tips.append(tip)
        if len(tips) >= 4:
            break

    if len(tips) < 4:
        for rule in lime_response.get("rules", []):
            if rule.get("effect") == "hurts":
                tip = f"Work on improving the condition: {rule.get('rule')}"
                if tip not in tips:
                    tips.append(tip)
            if len(tips) >= 4:
                break

    if not tips:
        income = _to_float(prediction_data.get("Income"))
        loan_count = int(_to_float(prediction_data.get("Number of Existing Loans")))
        if income > 0:
            tips.append("Maintaining steady and higher income can improve score outcomes.")
        if loan_count > 0:
            tips.append("Reducing simultaneous active loans can lower perceived credit risk.")
        tips.append("Pay all EMIs and credit dues on time to build a positive repayment history.")

    return tips[:4]


def _normalize_advice_text(raw_advice, prediction_value: float):
    advice_text = str(raw_advice or "").strip()

    if not advice_text:
        if prediction_value >= 700:
            return (
                "Your score looks healthy. Focus on maintaining strong repayment behavior and low credit utilization "
                "to preserve or improve your score."
            )
        return (
            "Based on your profile, the key actions listed below can help improve your credit score over time."
        )

    if "No improvement advice requested" in advice_text:
        return (
            "Your score is currently in a stable range. Keep paying dues on time, avoid unnecessary new loans, "
            "and maintain low utilization to strengthen your profile further."
        )

    return advice_text


def _get_user_prediction_data(user_id: str):
    """
    Helper function to build prediction data dictionary for a given user
    from the database.
    """
    _ensure_predictor_available()

    if not user_id:
        raise ExplanationServiceError(400, "userid is required")

    try:
        UUID(str(user_id))
    except (TypeError, ValueError) as exc:
        raise ExplanationServiceError(400, "userid must be a valid UUID") from exc

    try:
        borrower_res = supabase.table("borrower").select("*").eq("id", user_id).limit(1).execute()
    except Exception as exc:
        logger.exception("Failed to fetch borrower record for explanation")
        raise ExplanationServiceError(500, "Failed to fetch borrower details") from exc

    records = borrower_res.data or []
    if not records:
        raise ExplanationServiceError(404, "Borrower not found")

    b_data = records[0]
    
    # Calculate age from DOB
    dob = b_data.get("dob")
    if not dob:
        raise ExplanationServiceError(400, "Borrower date of birth is missing")

    try:
        if isinstance(dob, str):
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
        else:
            dob_date = dob
    except Exception as exc:
        raise ExplanationServiceError(400, "Borrower date of birth is invalid") from exc
    today = datetime.now()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    credit_history_years = b_data.get("credit_history_length", 0) / 12
    
    prediction_data = {
        'Age': age,
        'Income': b_data.get("income"),
        'Credit History Length': credit_history_years,
        'Number of Existing Loans': b_data.get("loan_no"),
        'Existing Customer': 'Yes' if b_data.get("existing_customer", "yes").lower() == 'yes' else 'No',
        'State': b_data.get("state"),
        'City': b_data.get("city"),
        'LTV Ratio': b_data.get("ltv_ratio", 0),
        'Employment Profile': b_data.get("employment_profile"),
        'Occupation': b_data.get("occupation")
    }
    
    required_fields = [
        'Income',
        'Number of Existing Loans',
        'State',
        'City',
        'Employment Profile',
        'Occupation',
    ]
    missing = [field for field in required_fields if prediction_data.get(field) in [None, ""]]
    if missing:
        raise ExplanationServiceError(400, f"Borrower profile is incomplete: {', '.join(missing)}")

    return prediction_data


def get_shap_explanation(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        raw_shap = _credit_predictor.explain_prediction_shap(data)
        return _format_shap_response(raw_shap)
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate SHAP explanation")
        raise ExplanationServiceError(500, "Failed to generate SHAP explanation") from exc


def get_score_reasons(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        fingerprint = _compute_prediction_fingerprint(data)
        cached = _read_insights_cache(user_id)

        if cached and cached.get("profile_fingerprint") == fingerprint:
            cached_reasons = cached.get("reasons_payload")
            if isinstance(cached_reasons, dict) and cached_reasons.get("section") == "reason_for_score":
                return cached_reasons

        raw_shap = _credit_predictor.explain_prediction_shap(data)
        shap_response = _format_shap_response(raw_shap)

        raw_lime = _credit_predictor.explain_prediction_lime(data)
        api_key = os.getenv("GEMINI_API_KEY", "")
        lime_response = _format_lime_response(raw_lime, prediction_data=data, api_key=api_key)
        fallback_combined = _build_combined_score_reasons(
            shap_response.get("topFactors", []),
            lime_response.get("rules", []),
        )

        gemini_combined = _build_score_reasons_with_gemini(
            fallback_combined,
            data,
            api_key,
        )
        combined = gemini_combined or fallback_combined
        reason_source = "gemini" if gemini_combined else "fallback"

        prediction = _to_float(
            shap_response.get("prediction"),
            _to_float(lime_response.get("prediction"), 0.0),
        )

        reasons_payload = {
            "section": "reason_for_score",
            "source": reason_source,
            "prediction": prediction,
            "overview": combined.get("overview", ""),
            "combinedReasons": combined.get("combinedReasons", []),
            "topFactors": shap_response.get("topFactors", []),
            "rules": lime_response.get("rules", []),
        }

        _write_insights_cache(
            user_id,
            fingerprint,
            reasons_payload=reasons_payload,
            advice_payload=(cached or {}).get("advice_payload") if cached and cached.get("profile_fingerprint") == fingerprint else None,
        )
        return reasons_payload
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate score reasons")
        raise ExplanationServiceError(500, "Failed to generate score reasons") from exc


def get_lime_explanation(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        raw_lime = _credit_predictor.explain_prediction_lime(data)
        api_key = os.getenv("GEMINI_API_KEY", "")
        return _format_lime_response(raw_lime, prediction_data=data, api_key=api_key)
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate LIME explanation")
        raise ExplanationServiceError(500, "Failed to generate LIME explanation") from exc


def get_gemini_advice(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)

        try:
            shap_raw = _credit_predictor.explain_prediction_shap(data)
            shap_response = _format_shap_response(shap_raw)
        except Exception as exc:
            logger.warning("Could not generate SHAP data for Gemini advice: %s", exc)
            shap_raw = None
            shap_response = {"prediction": 0.0, "topFactors": []}

        try:
            lime_raw = _credit_predictor.explain_prediction_lime(data)
            lime_response = _format_lime_response(lime_raw)
        except Exception as exc:
            logger.warning("Could not generate LIME data for Gemini fallback advice: %s", exc)
            lime_response = {"prediction": 0.0, "rules": []}

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("Warning: GEMINI_API_KEY not set, falling back to practical advice tips")
            tips = _build_fallback_advice(data, shap_response, lime_response)
            return {
                "prediction": shap_response.get("prediction") or lime_response.get("prediction") or 0.0,
                "advice": "AI advice is temporarily unavailable. Showing practical recommendations based on your profile.",
                "source": "fallback",
                "improvementTips": tips,
            }

        try:
            gemini_result = _credit_predictor.get_credit_improvement_advice(
                data,
                shap_explanation=shap_raw,
                api_key=api_key,
            )

            prediction_value = _to_float(
                gemini_result.get("prediction"),
                shap_response.get("prediction") or lime_response.get("prediction") or 0.0,
            )
            tips = _build_fallback_advice(data, shap_response, lime_response)

            return {
                "prediction": prediction_value,
                "advice": _normalize_advice_text(gemini_result.get("advice", ""), prediction_value),
                "source": "gemini",
                "improvementTips": tips,
            }
        except Exception as exc:
            logger.warning("Gemini advice generation failed: %s", exc)
            tips = _build_fallback_advice(data, shap_response, lime_response)
            return {
                "prediction": shap_response.get("prediction") or lime_response.get("prediction") or 0.0,
                "advice": "AI advice is temporarily unavailable. Showing practical recommendations based on your profile.",
                "source": "fallback",
                "improvementTips": tips,
            }
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate Gemini advice")
        raise ExplanationServiceError(500, "Failed to generate Gemini advice") from exc


def get_score_advice(user_id: str):
    try:
        data = _get_user_prediction_data(user_id)
        fingerprint = _compute_prediction_fingerprint(data)
        cached = _read_insights_cache(user_id)

        if cached and cached.get("profile_fingerprint") == fingerprint:
            cached_advice = cached.get("advice_payload")
            if isinstance(cached_advice, dict) and cached_advice.get("section") == "improvement_advice":
                return cached_advice

        advice_response = get_gemini_advice(user_id)
        advice_payload = {
            "section": "improvement_advice",
            **advice_response,
        }
        _write_insights_cache(
            user_id,
            fingerprint,
            reasons_payload=(cached or {}).get("reasons_payload") if cached and cached.get("profile_fingerprint") == fingerprint else None,
            advice_payload=advice_payload,
        )
        return advice_payload
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate score advice")
        raise ExplanationServiceError(500, "Failed to generate score advice") from exc


def get_credit_score_insights(user_id: str):
    try:
        return {
            "reasonForScore": get_score_reasons(user_id),
            "improvementAdvice": get_score_advice(user_id),
        }
    except ExplanationServiceError:
        raise
    except Exception as exc:
        logger.exception("Failed to generate score insights")
        raise ExplanationServiceError(500, "Failed to generate score insights") from exc


# -----------------------------
# POST /borrower/details
# -----------------------------
def create_borrower_details(data):

    #Age validation for new user onboarding
    from datetime import datetime
    dob_date = datetime.strptime(str(data.dob), '%Y-%m-%d')
    today = datetime.now()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    if age < 18 or age > 105:
        raise ValueError("Age must be between 18 and 105")

    _invalidate_insights_cache(data.userid)

    credit_history_months = to_months(
        data.creditHistoryYr, data.creditHistoryMon
    )
    loan_tenure_months = to_months(
        data.loanTenureYr, data.loanTenureMon
    )
    validate_loan_and_asset_values(data.loanAmount, data.assetValue)
    ltv = calculate_ltv(data.loanAmount, data.assetValue)

    # Insert borrower
    supabase.table("borrower").insert({
        "id": data.userid,
        "dob": str(data.dob),
        "gender": data.gender,
        "state": data.state,
        "city": data.city,
        "phone_no": data.phone,
        "employment_profile": data.empProfile,
        "occupation": data.occupation,
        "income": data.income,
        "credit_history_length": credit_history_months,
        "loan_no": data.loanNo,
        "asset_value": data.assetValue,
        "ltv_ratio": ltv,
        "existing_customer": "yes"
    }).execute()

    # Insert loan details
    supabase.table("borrower_loan_details").insert({
        "borrower_id": data.userid,
        "loan_amount": data.loanAmount,
        "loan_tenure": loan_tenure_months,
        "purpose": data.purpose
    }).execute()

    # Credit score + risk + credit line
    score = generate_credit_score(
        dob=data.dob,
        income=data.income,
        credit_history_months=credit_history_months,
        loan_no=data.loanNo,
        state=data.state,
        city=data.city,
        employment_profile=data.empProfile,
        occupation=data.occupation,
        asset_value=data.assetValue,
        loan_amount=data.loanAmount,
        existing_customer="yes"
    )
    risk = risk_bucket(score)
    credit_line = estimated_credit_line(score, data.income, ltv)

    supabase.table("borrower_credit_info").insert({
        "id": data.userid,
        "credit_score": score,
        "risk": risk,
        "credit_line": credit_line
    }).execute()

    return {"status": "success"}


# -----------------------------
# GET /borrower/credit-info
# -----------------------------
def get_credit_info(user_id: str):
    res = supabase.table("borrower_credit_info") \
        .select("credit_score, risk, credit_line") \
        .eq("id", user_id).single().execute()

    return {
        "creditScore": res.data["credit_score"],
        "Risk": res.data["risk"],
        "creditLine": res.data["credit_line"]
    }


# -----------------------------
# GET /borrower/profile-details
# -----------------------------
def get_profile_details(user_id: str):
    res = supabase.table("borrower") \
        .select("id, dob, gender, state, city, phone_no, employment_profile, occupation, income, credit_history_length, loan_no, asset_value") \
        .eq("id", user_id).single().execute()

    credit_history_length = res.data.get("credit_history_length") or 0

    return {
        "id": res.data.get("id"),
        "dob": str(res.data.get("dob")) if res.data.get("dob") else "",
        "gender": res.data.get("gender") or "",
        "state": res.data.get("state") or "",
        "city": res.data.get("city") or "",
        "phone": res.data.get("phone_no") or "",
        "empProfile": res.data.get("employment_profile") or "",
        "occupation": res.data.get("occupation") or "",
        "income": res.data.get("income") or 0,
        "creditHistoryYr": credit_history_length // 12,
        "creditHistoryMon": credit_history_length % 12,
        "loanNo": res.data.get("loan_no") or 0,
        "assetValue": res.data.get("asset_value") or 0,
    }


# -----------------------------
# GET /borrower/loan-info
# -----------------------------
def get_loan_info(user_id: str):
    res = supabase.table("borrower_loan_details") \
        .select("loan_amount, loan_tenure, purpose") \
        .eq("borrower_id", user_id).single().execute()

    return {
        "loanAmount": res.data["loan_amount"],
        "loanTenureYr": res.data["loan_tenure"] // 12,
        "loanTenureMon": res.data["loan_tenure"] % 12,
        "purpose": res.data["purpose"]
    }


# -----------------------------
# GET /borrower/onboarding-status
# Check if borrower has completed onboarding
# Returns True if borrower record exists, False otherwise
# -----------------------------
def check_borrower_onboarding(user_id: str):
    try:
        res = supabase.table("borrower") \
            .select("id") \
            .eq("id", user_id).single().execute()
        return bool(res.data)
    except Exception:
        return False


# -----------------------------
# PUT /borrower/loan-update
# -----------------------------
def update_loan_info(data):
    tenure_months = to_months(
        data.loanTenureYr, data.loanTenureMon
    )
    borrower_row = supabase.table("borrower") \
        .select("asset_value") \
        .eq("id", data.userid).single().execute()
    asset_value = borrower_row.data.get("asset_value") if borrower_row.data else None
    if asset_value is None:
        raise ValueError("Borrower profile not found for loan update.")
    validate_loan_and_asset_values(data.loanAmount, float(asset_value))

    supabase.table("borrower_loan_details") \
        .update({
            "loan_amount": data.loanAmount,
            "loan_tenure": tenure_months,
            "purpose": data.purpose
        }) \
        .eq("borrower_id", data.userid) \
        .execute()

    _invalidate_insights_cache(data.userid)

    return {"status": "updated"}


# PUT /borrower/personal-update
# -----------------------------
def update_personal_info(data):
    ltv = calculate_ltv(
        supabase.table("borrower_loan_details") \
            .select("loan_amount") \
            .eq("borrower_id", data.userid).single().execute().data["loan_amount"],
        data.assetValue if hasattr(data, 'assetValue') else 0
    )
    
    supabase.table("borrower") \
        .update({
            "dob": str(data.dob),
            "gender": data.gender,
            "state": data.state,
            "city": data.city,
            "phone_no": data.phone
        }) \
        .eq("id", data.userid) \
        .execute()

    _invalidate_insights_cache(data.userid)

    return {"status": "updated"}


# PUT /borrower/employment-update
# --------------------------------
def update_employment_info(data):
    supabase.table("borrower") \
        .update({
            "employment_profile": data.empProfile,
            "occupation": data.occupation,
            "income": data.income
        }) \
        .eq("id", data.userid) \
        .execute()

    _invalidate_insights_cache(data.userid)

    return {"status": "updated"}


# PUT /borrower/credit-update
# ----------------------------
def update_credit_info(data):
    credit_history_months = to_months(data.creditHistoryYr, data.creditHistoryMon)
    loan_row = supabase.table("borrower_loan_details") \
        .select("loan_amount") \
        .eq("borrower_id", data.userid).single().execute()
    loan_amount = loan_row.data.get("loan_amount") if loan_row.data else None
    if loan_amount is None:
        raise ValueError("Loan details not found for borrower.")
    validate_loan_and_asset_values(float(loan_amount), data.assetValue)
    
    supabase.table("borrower") \
        .update({
            "credit_history_length": credit_history_months,
            "loan_no": data.loanNo,
            "asset_value": data.assetValue
        }) \
        .eq("id", data.userid) \
        .execute()

    _invalidate_insights_cache(data.userid)

    return {"status": "updated"}


# -----------------------------
# GET /borrower/lender-info
# -----------------------------
def get_lenders():
    res = supabase.table("lender") \
        .select("id, type, loan_amount_from, loan_amount_to, interest") \
        .execute()

    # Also fetch lender names from users table
    lender_ids = [l["id"] for l in res.data]
    if not lender_ids:
        return []
    users_res = supabase.table("users").select("id, name").in_("id", lender_ids).execute()
    name_map = {u["id"]: u["name"] for u in users_res.data}

    return [
        {
            "lenderid": l["id"],
            "name": name_map.get(l["id"], "Unknown"),
            "type": l["type"],
            "loanAmountFrom": l["loan_amount_from"],
            "loanAmountTo": l["loan_amount_to"],
            "Interest": l["interest"]
        }
        for l in res.data
    ]


# -----------------------------
# POST /borrower/apply
# -----------------------------
def apply_to_lender(user_id: str, lender_id: str):
    supabase.table("loan").insert({
        "borrower_id": user_id,
        "lender_id": lender_id,
        "status": "requested"
    }).execute()

    return {"status": "requested"}


# -----------------------------
# GET /borrower/approved-lenders
# -----------------------------
def get_approved_lenders(user_id: str):
    res = supabase.table("loan") \
        .select("lender_id") \
        .eq("borrower_id", user_id) \
        .eq("status", "approved") \
        .execute()

    if not res.data:
        return []

    lender_ids = [r["lender_id"] for r in res.data]
    lenders_res = supabase.table("lender") \
        .select("id, type, capacity, loan_amount_from, loan_amount_to, interest") \
        .in_("id", lender_ids) \
        .execute()

    # Fetch names
    users_res = supabase.table("users").select("id, name").in_("id", lender_ids).execute()
    name_map = {u["id"]: u["name"] for u in users_res.data}

    return [
        {
            "lenderId": r["id"],
            "Name": name_map.get(r["id"], "Unknown"),
            "type": r["type"],
            "capacity": r["capacity"],
            "loanAmountFrom": r["loan_amount_from"],
            "loanAmountTo": r["loan_amount_to"],
            "interest": r["interest"]
        }
        for r in lenders_res.data
    ]