"""
ai_serice.py
Calls OpenAI API to generate a health prediction (Remarks).
Falls back to a rule-based local function if no API key is set.
"""
import json
import urllib.request
import urllib.error
try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = " "
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

#public function
def get_health_prediction(glucose: float, haemoglobin: float, cholesterol: float)-> str:
    if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-key-here":
        result = _call_openai(glucose, haemoglobin, cholesterol)
        if result:
            return result
    return _rule_based(glucose, haemoglobin, cholesterol)

# OpenAI API call  (uses only stdlib — no pip install needed)
def _call_openai(glucose, haemoglobin, cholesterol):
    """Call OpenAI and return the text response, or None on any failure."""
    prompt = (
        f"A patient has the following blood test results:\n"
        f"- Glucose: {glucose} mg/dL\n"
        f"- Haemoglobin: {haemoglobin} g/dL\n"
        f"- Cholesterol: {cholesterol} mg/dL\n\n"
        f"In 2-3 sentences: identify any values outside normal range, "
        f"name the most likely health risk, and state whether the patient "
        f"should consult a doctor. Keep it plain and factual. "
        f"This is for educational purposes only."
    )
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    ) 
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        print(f"[ai_service] OpenAI call failed: {e} — using fallback.")
        return None

# Rule-based fallback
def _rule_based(glucose, haemoglobin, cholesterol):
    """
    Simple medical-range logic.
    Reference ranges:
      Glucose:      70–99  mg/dL  fasting (pre-diabetes 100–125, diabetes ≥126)
      Haemoglobin: 12.0–17.5 g/dL  (anaemia <12, high >17.5)
      Cholesterol:  <200  mg/dL  (borderline 200–239, high ≥240)
    """
    issues = []
    advice = []

#Glucose
    if glucose < 70:
        issues.append("low glucose (hypoglycaemia)")
        advice.append("eat regular meals and seek medical advice")
    elif 100 <= glucose < 126:
        issues.append("elevated glucose indicating pre-diabetes risk")
        advice.append("reduce sugar/refined carb intake and monitor closely")
    elif glucose >= 126:
        issues.append("high glucose consistent with possible diabetes")
        advice.append("consult a doctor for a formal diabetes assessment")

#Haemoglobin 
    if haemoglobin < 12.0:
        issues.append("low haemoglobin suggesting anaemia")
        advice.append("increase iron-rich foods and see a doctor")
    elif haemoglobin > 17.5:
        issues.append("elevated haemoglobin (possible polycythaemia)")
        advice.append("consult a doctor for further blood panel tests")

#Cholesterol 
    if 200 <= cholesterol < 240:
        issues.append("borderline-high cholesterol")
        advice.append("adopt a heart-healthy diet and increase exercise")
    elif cholesterol >= 240:
        issues.append("high cholesterol with elevated cardiovascular risk")
        advice.append("consult a doctor and consider lipid-lowering therapy")
 
#  Build result string 
    if not issues:
        return (
            "All blood test values are within normal reference ranges. "
            "Continue maintaining a healthy lifestyle with balanced diet and regular exercise. "
            "Routine check-ups every 6–12 months are recommended."
        )
    issues_str = "; ".join(issues)
    advice_str = "; ".join(advice)
    return (
        f"Analysis indicates: {issues_str}. "
        f"Recommended actions: {advice_str}. "
        f"Please consult a qualified healthcare professional for a proper diagnosis — "
        f"this prediction is for educational purposes only."
    )

