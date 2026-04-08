# 🧭 RiskPilot AI — Business Risk Analyzer

Professional-grade AI business risk assessment tool. Built with Streamlit + Google Gemini.

---

## Files

```
app.py                            ← Main application
requirements.txt                  ← Python dependencies
.streamlit/config.toml            ← Dark-navy theme
.streamlit/secrets.toml.template  ← Copy this for your secrets (see below)
.gitignore                        ← Keeps secrets.toml out of git
```

---

## One-Time Setup (30 minutes total)

### Step 1 — Get a Free Gemini API Key

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key — you'll need it in Step 3

### Step 2 — Create a GitHub Repository

1. Go to **https://github.com/new**
2. Name it `riskpilot-ai` (or anything you like)
3. Set it to **Public**
4. Do NOT initialise with a README (the code is already here)
5. Push this code to it:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/riskpilot-ai.git
   git push -u origin main
   ```

### Step 3 — Deploy on Streamlit Community Cloud (Free)

1. Go to **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **New app**
4. Choose your `riskpilot-ai` repo → branch `main` → file `app.py`
5. Click **Advanced settings → Secrets** and paste:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
PREMIUM_CODE   = "RISK-PILOT-YOURCODE-2024"
```

6. Click **Deploy** — your live URL will be `https://riskpilot.streamlit.app` (or similar)

### Step 4 — Set Up Gumroad (Free)

1. Go to **https://app.gumroad.com** and create a free account
2. Create two products:
   - **Free product**: "RiskPilot AI — Free Access" (price: $0, description links to your Streamlit URL)
   - **Subscription product**: "RiskPilot AI — Premium" (price: $19/month)
     - In the confirmation email / product page, include your `PREMIUM_CODE` value
3. Your Gumroad store URL becomes your payment page — no website needed

### Step 5 — Set Up Free Landing Page on Carrd

1. Go to **https://carrd.co** and sign up free
2. Use the single-page template
3. Include: headline, 3 bullet benefits, "Try Free" button (→ Streamlit URL), "Get Premium" button (→ Gumroad)
4. Your free Carrd URL: `yourname.carrd.co`

---

## Updating the Premium Code

To rotate the premium code monthly:

1. Go to Streamlit Community Cloud → your app → Settings → Secrets
2. Change the `PREMIUM_CODE` value
3. Update the value in your Gumroad product description / delivery email
4. Save — the app reloads automatically, no redeployment needed

---

## Adding Tool 2 (Investment Risk Profiler) — Week 3

When ready, ask your developer to add `pages/2_Investment_Risk_Profiler.py`.
Streamlit automatically turns files in the `pages/` folder into a multi-page app
with navigation — zero extra configuration needed.

---

## Revenue Streams

| Stream | Platform | Price |
|---|---|---|
| Premium subscription | Gumroad | $19/month |
| Risk Playbook PDF | Gumroad | $47 one-time |
| Affiliate links in tool outputs | Embedded | Varies |

---

## Support

This tool is self-serve by design. Direct users to the tool's built-in FAQ
(add a Streamlit expander at the bottom of the page) rather than handling
support manually.
