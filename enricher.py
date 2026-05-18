import requests
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv

load_dotenv()


def scrape_website(url: str) -> str:
    if not url:
        return ""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        print(f"[SCRAPE] Failed: {e}")
        return ""


def _sanitize_enrichment(data, company_name):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            pass

    if isinstance(data, list):
        print("[ENRICH] LLM returned a list instead of a dictionary. Extracting dict...")
        if not data:
            data = {}
        elif isinstance(data[0], dict):
            data = data[0]
        else:
            data = {
                "findings": [str(x) for x in data],
                "recommendations": ["Optimize operations and services based on findings."]
            }

    if not isinstance(data, dict):
        data = {}

    default_data = {
        "industry": "Unknown Industry",
        "company_summary": f"{company_name} is a business seeking to improve its operations.",
        "services": ["General Services", "Consulting"],
        "findings": [
            "Website structure could be optimized",
            "Potential for better online engagement",
            "Automation opportunities exist"
        ],
        "recommendations": [
            "Implement a modern digital strategy",
            "Integrate AI-driven customer support",
            "Optimize conversion funnels"
        ],
        "personalized_opening": f"We've prepared an initial analysis for {company_name} based on standard industry practices."
    }

    sanitized = {}
    for key, def_val in default_data.items():
        val = data.get(key)
        if isinstance(def_val, list):
            if isinstance(val, list):
                sanitized[key] = [str(x) for x in val if x]
            elif isinstance(val, str):
                sanitized[key] = [val]
            else:
                sanitized[key] = def_val
        else:
            sanitized[key] = str(val) if val else def_val

    return sanitized


def _enrich_company_raw(company_name: str, website: str) -> dict:
    raw_text = scrape_website(website)

    context = f"Company name: {company_name}\n"
    if raw_text:
        context += f"Website content:\n{raw_text}"
    else:
        context += "No website found. Use general knowledge."

    prompt = f"""You are a business analyst creating a lead audit report.

{context}

Based on the website content or your general knowledge about the company, analyze the business and identify potential problems and improvements.
Return ONLY valid JSON with these exact keys:
{{
  "industry": "...",
  "company_summary": "what the company does",
  "services": ["service 1", "service 2"],
  "findings": ["problem 1", "problem 2", "problem 3"],
  "recommendations": ["improvement 1", "improvement 2", "improvement 3"],
  "personalized_opening": "warm 2-sentence opening for the report"
}}

No markdown, no explanation. Only JSON."""

    # ── 1. Try Gemini (default) ──────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("YOUR_"):
        print("[ENRICH] Using Gemini for enrichment...")
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-flash-latest", contents=prompt
            )
            raw = response.text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[ENRICH] Gemini error: {e}")

    # ── 2. Try OpenRouter if key is present ───────────────────────────
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and not openrouter_key.startswith("YOUR_"):
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        # We loop through a few excellent free models in case of upstream rate-limits
        models_to_try = [
            "openrouter/free",
            "google/gemma-4-26b-a4b-it:free",
            "liquid/lfm-2.5-1.2b-instruct:free"
        ]
        for model in models_to_try:
            print(f"[ENRICH] Using OpenRouter ({model}) for enrichment...")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                raw = response.choices[0].message.content
                if not raw:
                    raise Exception("Received empty response content from model")
                raw = raw.strip()
                return json.loads(raw)
            except Exception as e:
                print(f"[ENRICH] OpenRouter model {model} failed: {e}. Trying next...")
        print("[ENRICH] All OpenRouter models failed. Continuing to next provider...")

    # ── 3. Try OpenAI if key is present ───────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("YOUR_"):
        print("[ENRICH] Using OpenAI for enrichment...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[ENRICH] OpenAI error: {e}")

    # ── 4. Try Anthropic (Claude) if key is present ────────────────
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if anthropic_key and not anthropic_key.startswith("YOUR_"):
        print("[ENRICH] Using Anthropic (Claude) for enrichment...")
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[ENRICH] Anthropic error: {e}")

    # ── 5. Fallback if all APIs fail ─────────────────────────────
    print("[ENRICH] All AI APIs failed or keys are missing. Using standard fallback...")
    return {
        "industry": "Unknown Industry",
        "company_summary": f"{company_name} is a business seeking to improve its operations.",
        "services": ["General Services", "Consulting"],
        "findings": [
            "Website structure could be optimized",
            "Potential for better online engagement",
            "Automation opportunities exist"
        ],
        "recommendations": [
            "Implement a modern digital strategy",
            "Integrate AI-driven customer support",
            "Optimize conversion funnels"
        ],
        "personalized_opening": f"We've prepared an initial analysis for {company_name} based on standard industry practices. Note: AI enrichment failed due to an API error."
    }


def enrich_company(company_name: str, website: str) -> dict:
    try:
        raw_data = _enrich_company_raw(company_name, website)
        return _sanitize_enrichment(raw_data, company_name)
    except Exception as e:
        print(f"[ENRICH] Critical error during enrichment pipeline: {e}")
        return _sanitize_enrichment({}, company_name)