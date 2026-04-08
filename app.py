import json
import re
from datetime import datetime

import requests
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RiskPilot AI — Business Risk Analyzer",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────────
FREE_TIER_LIMIT = 3

# ── Session state defaults ─────────────────────────────────────────────────────
if "uses" not in st.session_state:
    st.session_state.uses = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "last_report" not in st.session_state:
    st.session_state.last_report = None  # (business_data, report) tuple


# ── Helpers ────────────────────────────────────────────────────────────────────

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)


def call_gemini(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("Gemini API key not configured. See README for setup instructions.")
        st.stop()
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096},
    }
    resp = requests.post(GEMINI_URL, params={"key": api_key}, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def check_premium_code(code: str) -> bool:
    stored = st.secrets.get("PREMIUM_CODE", "")
    return bool(stored) and code.strip() == stored.strip()


def extract_json(text: str) -> dict:
    """Robustly extract the first JSON object from a Gemini response."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response.")
    return json.loads(match.group())


def build_prompt(d: dict) -> str:
    return f"""
You are a senior risk management consultant with 20+ years of experience in
financial, operational, and strategic risk. Analyse the business below and
return a structured JSON risk assessment. Be specific to this business — avoid
generic advice. Use professional risk management terminology throughout.

BUSINESS PROFILE
────────────────
Business / Product:  {d["business_type"]}
Industry:            {d["industry"]}
Stage:               {d["stage"]}
Monthly Revenue:     ${d["revenue"]}
Team Size:           {d["employees"]}
Business Model:      {d["model"]}
Primary Market:      {d["geography"]}
Owner's Concerns:    {d["concerns"]}

Return ONLY valid JSON in exactly this structure (no markdown, no commentary):

{{
  "risk_score": <integer 1-100, higher = more risk>,
  "risk_rating": "<LOW | MODERATE | HIGH | CRITICAL>",
  "executive_summary": "<2-3 sentence plain-English summary of overall risk posture>",
  "top_risks": [
    {{
      "rank": <1-10>,
      "category": "<e.g. Financial, Operational, Legal, Reputational, Market>",
      "risk": "<Short risk name>",
      "description": "<Why this risk applies specifically to this business>",
      "likelihood": "<LOW | MEDIUM | HIGH>",
      "impact": "<LOW | MEDIUM | HIGH | CRITICAL>",
      "mitigation": "<Concrete, actionable mitigation step>",
      "timeframe": "<IMMEDIATE | 30-DAYS | 90-DAYS | ONGOING>"
    }}
  ],
  "policy_gaps": [
    "<Specific policy or procedure gap for this business>"
  ],
  "quick_wins": [
    "<Action the owner can take THIS WEEK to reduce risk>"
  ],
  "risk_matrix_notes": "<One sentence on the highest-priority risk intersection>"
}}

Rules:
- top_risks must contain exactly 10 items ranked highest to lowest priority.
- policy_gaps must contain 4-6 items.
- quick_wins must contain 3-5 items.
- Every field is required. No nulls.
"""


def generate_risk_assessment(business_data: dict) -> dict:
    prompt = build_prompt(business_data)
    text = call_gemini(prompt)
    return extract_json(text)


# ── Report rendering ───────────────────────────────────────────────────────────

IMPACT_ICON = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
RATING_ICON = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}


def render_report(data: dict, report: dict):
    score = report["risk_score"]
    rating = report["risk_rating"]
    icon = RATING_ICON.get(rating, "⚪")

    st.markdown("---")

    # Score banner
    col_l, col_m, col_r = st.columns([1, 3, 1])
    with col_m:
        st.markdown(
            f"<h2 style='text-align:center'>{icon} Risk Score: {score}/100 — {rating}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align:center; color:#888'>{report['executive_summary']}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Top 10 risks
    st.markdown("### 🔍 Top 10 Business Risks")
    for risk in report["top_risks"]:
        with st.expander(f"#{risk['rank']} — {risk['risk']}  |  Impact: {risk['impact']}  |  Likelihood: {risk['likelihood']}"):
            st.markdown(f"**Category:** `{risk['category']}`")
            st.markdown(f"**Description:** {risk['description']}")
            st.markdown(f"**Mitigation:** {risk['mitigation']}")
            st.markdown(f"**Action Timeframe:** `{risk['timeframe']}`")

    # Policy gaps
    st.markdown("---")
    st.markdown("### 📋 Policy & Procedure Gaps")
    for gap in report["policy_gaps"]:
        st.markdown(f"- {gap}")

    # Quick wins
    st.markdown("---")
    st.markdown("### ⚡ Quick Wins — Do These This Week")
    for i, win in enumerate(report["quick_wins"], 1):
        st.markdown(f"**{i}.** {win}")

    # Risk matrix note
    st.markdown("---")
    st.info(f"**Risk Matrix Analysis:** {report['risk_matrix_notes']}")

    # Download
    st.markdown("---")
    txt = build_text_report(data, report)
    st.download_button(
        label="⬇️  Download Full Report (.txt)",
        data=txt,
        file_name=f"riskpilot_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True,
    )


def build_text_report(data: dict, report: dict) -> str:
    lines = [
        "=" * 65,
        "  RISKPILOT AI — BUSINESS RISK ASSESSMENT REPORT",
        f"  Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}",
        "=" * 65,
        "",
        "BUSINESS PROFILE",
        "-" * 40,
        f"Business / Product : {data['business_type']}",
        f"Industry           : {data['industry']}",
        f"Stage              : {data['stage']}",
        f"Monthly Revenue    : ${data['revenue']}",
        f"Team Size          : {data['employees']}",
        f"Business Model     : {data['model']}",
        f"Primary Market     : {data['geography']}",
        f"Key Concerns       : {data['concerns']}",
        "",
        "RISK SUMMARY",
        "-" * 40,
        f"Overall Risk Score : {report['risk_score']}/100",
        f"Risk Rating        : {report['risk_rating']}",
        f"Summary            : {report['executive_summary']}",
        "",
        "TOP 10 RISKS",
        "-" * 40,
    ]

    for r in report["top_risks"]:
        lines += [
            "",
            f"#{r['rank']} — {r['risk']}",
            f"  Category   : {r['category']}",
            f"  Impact     : {r['impact']}   Likelihood: {r['likelihood']}",
            f"  Description: {r['description']}",
            f"  Mitigation : {r['mitigation']}",
            f"  Timeframe  : {r['timeframe']}",
        ]

    lines += ["", "POLICY GAPS", "-" * 40]
    for gap in report["policy_gaps"]:
        lines.append(f"  • {gap}")

    lines += ["", "QUICK WINS (THIS WEEK)", "-" * 40]
    for i, win in enumerate(report["quick_wins"], 1):
        lines.append(f"  {i}. {win}")

    lines += [
        "",
        "RISK MATRIX NOTE",
        "-" * 40,
        f"  {report['risk_matrix_notes']}",
        "",
        "=" * 65,
        "  RiskPilot AI  |  riskpilot.streamlit.app",
        "  Upgrade to Premium: riskpilot.gumroad.com",
        "=" * 65,
    ]
    return "\n".join(lines)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧭 RiskPilot AI")
    st.markdown("Professional business risk assessment powered by AI.")
    st.markdown("---")

    if st.session_state.is_premium:
        st.success("✅ Premium — Unlimited analyses")
    else:
        remaining = max(0, FREE_TIER_LIMIT - st.session_state.uses)
        st.info(f"Free tier: **{remaining} / {FREE_TIER_LIMIT}** analyses remaining this session")

    st.markdown("---")
    st.markdown("### 🔓 Unlock Premium")
    st.markdown("**$19/month** — unlimited analyses, all tools, priority updates.")

    code_input = st.text_input("Premium code", type="password", placeholder="Paste your code here")
    if st.button("Activate", use_container_width=True):
        if check_premium_code(code_input):
            st.session_state.is_premium = True
            st.success("Premium activated!")
            st.rerun()
        else:
            st.error("Invalid code. Get yours at the link below.")

    st.markdown("[Get Premium ($19/mo) →](https://riskpilot.gumroad.com)")
    st.markdown("[Risk Playbook PDF ($47) →](https://riskpilot.gumroad.com)")
    st.markdown("---")
    st.caption("Built by a risk management expert. Not financial advice.")


# ── Main ───────────────────────────────────────────────────────────────────────

st.title("🧭 RiskPilot AI")
st.markdown(
    "**Get a professional-grade business risk assessment in 90 seconds.** "
    "Built on real risk management frameworks — not generic AI outputs."
)

# Hard gate for free tier exhaustion
if not st.session_state.is_premium and st.session_state.uses >= FREE_TIER_LIMIT:
    st.warning(
        "You've used all 3 free analyses for this session. "
        "Upgrade to Premium for unlimited access."
    )
    st.markdown(
        "### [→ Upgrade to Premium ($19/month)](https://riskpilot.gumroad.com)"
    )
    if st.session_state.last_report:
        st.markdown("---")
        st.markdown("*Your last report is shown below.*")
        render_report(*st.session_state.last_report)
    st.stop()

# Input form
st.markdown("---")
st.markdown("### Tell us about your business")

with st.form("risk_form", clear_on_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        business_type = st.text_input(
            "Business name or type *",
            placeholder="e.g. Online fitness coaching, SaaS invoicing tool, E-commerce candle brand",
        )
        industry = st.selectbox(
            "Industry *",
            [
                "Technology / SaaS",
                "E-commerce / Retail",
                "Professional Services / Consulting",
                "Food & Beverage",
                "Healthcare / Wellness",
                "Finance / Fintech",
                "Education / Edtech",
                "Real Estate",
                "Manufacturing / Physical Products",
                "Media / Content / Creator",
                "Non-profit",
                "Other",
            ],
        )
        stage = st.selectbox(
            "Business stage *",
            [
                "Idea / Pre-revenue",
                "Early Stage (< 6 months old)",
                "Growing ($1k-$10k/month revenue)",
                "Scaling ($10k-$100k/month revenue)",
                "Established ($100k+/month revenue)",
            ],
        )
        employees = st.selectbox(
            "Team size",
            ["Solo founder", "2-5 people", "6-15 people", "16-50 people", "50+"],
        )

    with col2:
        revenue = st.text_input(
            "Approximate monthly revenue ($)",
            placeholder="e.g. 5000  (enter 0 if pre-revenue)",
        )
        geography = st.selectbox(
            "Primary market",
            [
                "United States",
                "United Kingdom",
                "Canada",
                "Australia / NZ",
                "Europe",
                "Latin America",
                "Asia Pacific",
                "Global / Fully Online",
                "Other",
            ],
        )
        model = st.selectbox(
            "Business model",
            [
                "SaaS / Subscription",
                "E-commerce (physical products)",
                "Digital products / Info products",
                "Service / Consulting / Freelance",
                "Marketplace / Platform",
                "Advertising / Content / Creator",
                "Franchise / Licensing",
                "Other",
            ],
        )
        concerns = st.text_area(
            "Your top concerns or focus areas *",
            placeholder=(
                "e.g. Cash flow problems, losing our one big client, "
                "data security gaps, a competitor launching a similar product"
            ),
            height=120,
        )

    submitted = st.form_submit_button(
        "🔍  Generate Risk Assessment", use_container_width=True
    )

if submitted:
    if not business_type.strip() or not concerns.strip():
        st.error("Please fill in the required fields: Business type and Concerns.")
    else:
        business_data = {
            "business_type": business_type.strip(),
            "industry": industry,
            "stage": stage,
            "revenue": revenue.strip() or "0",
            "employees": employees,
            "geography": geography,
            "model": model,
            "concerns": concerns.strip(),
        }

        with st.spinner("Analysing your business risk profile... (15-30 seconds)"):
            try:
                report = generate_risk_assessment(business_data)
                st.session_state.uses += 1
                st.session_state.last_report = (business_data, report)
                render_report(business_data, report)
            except json.JSONDecodeError:
                st.error(
                    "The AI returned a malformed response. Please try again — "
                    "this is usually a one-off Gemini quirk."
                )
            except Exception as exc:
                st.error(f"Something went wrong: {exc}. Please try again.")

elif st.session_state.last_report:
    render_report(*st.session_state.last_report)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#888; font-size:0.8em'>"
    "RiskPilot AI &nbsp;|&nbsp; Built by a certified risk management professional &nbsp;|&nbsp; "
    "<a href='https://riskpilot.gumroad.com'>Premium</a> &nbsp;|&nbsp; "
    "<a href='https://riskpilot.gumroad.com'>Risk Playbook PDF</a>"
    "</div>",
    unsafe_allow_html=True,
)
