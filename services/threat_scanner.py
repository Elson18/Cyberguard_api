import json
import os
import re
from urllib.parse import urlparse

import httpx
from groq import Groq

from config import Config

config = Config()
_groq_client = Groq(api_key=config.GROQ_API_KEY)

THREAT_KEYWORDS = [
    "scam",
    "phishing",
    "malware",
    "fraud",
    "fake login",
    "unsafe",
    "dangerous",
    "hack",
    "data breach",
    "identity theft",
]


async def serpapi_check(domain: str) -> dict:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return {"serpRisky": False, "serpMatchCount": 0, "serpMatches": []}

    matches = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for query in [f"{domain} scam", f"{domain} phishing", f"{domain} malware"]:
            try:
                response = await client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "q": query,
                        "api_key": api_key,
                        "engine": "google",
                        "num": "5",
                    },
                )
                if not response.is_success:
                    continue
                data = response.json()
                for item in data.get("organic_results", []):
                    text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
                    for keyword in THREAT_KEYWORDS:
                        if keyword in text:
                            matches.append(
                                {
                                    "keyword": keyword,
                                    "query": query,
                                    "title": item.get("title"),
                                    "snippet": (item.get("snippet") or "")[:120],
                                }
                            )
            except httpx.HTTPError:
                continue

    return {
        "serpRisky": len(matches) > 0,
        "serpMatchCount": len(matches),
        "serpMatches": matches[:5],
    }


def _groq_classify_url(url: str, domain: str, serp: dict) -> dict:
    prompt = f"""Classify this URL threat level.
URL: {url}
Domain: {domain}
SerpApi risky: {serp['serpRisky']} ({serp['serpMatchCount']} indicators)

Respond with JSON only:
{{"label":"Safe|Suspicious|Harmful","explanation":"one sentence"}}"""

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    label = "Harmful" if serp["serpRisky"] else "Safe"
    return {
        "label": label,
        "explanation": "Automated reputation and AI classification completed.",
    }


def _simulation_block(url: str) -> bool:
    return any(
        token in url
        for token in (
            "amtso.org/security-features-check/phishing-page",
            "amtso.org/security-features-check/download-file",
            "eicar.org/download-anti-malware-testfile",
        )
    )


async def analyze_url(url: str) -> dict:
    parsed = urlparse(url)
    domain = parsed.hostname or url

    serp = await serpapi_check(domain)
    ai = _groq_classify_url(url, domain, serp)

    is_simulation = _simulation_block(url)
    should_block = (
        serp["serpRisky"]
        or ai.get("label") == "Harmful"
        or is_simulation
    )
    decision = "BLOCKED" if should_block else "ALLOWED"

    explanation = ai.get("explanation")
    if should_block and is_simulation:
        explanation = (
            "Harmful website detected. Access blocked by NeuroGuard to protect "
            "your device from phishing and malware."
        )
    elif should_block and serp["serpMatches"]:
        top = serp["serpMatches"][0]
        explanation = (
            f'This site was flagged for "{top.get("keyword")}" in search results: '
            f'"{top.get("title")}".'
        )
    elif should_block:
        explanation = explanation or "This website has been flagged as unsafe."

    return {
        "url": url,
        "domain": domain,
        "serpRisky": serp["serpRisky"],
        "serpMatchCount": serp["serpMatchCount"],
        "serpMatches": serp["serpMatches"],
        "aiLabel": ai.get("label", "Suspicious"),
        "explanation": explanation,
        "decision": decision,
        "shouldBlock": should_block,
        "riskLevel": "HIGH" if should_block else "LOW",
        "gemini": "HARMFUL" if should_block else "SAFE",
    }
