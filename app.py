from flask import Flask, request, jsonify, render_template
import requests
import urllib.parse
import os
import re
from bs4 import BeautifulSoup
from collections import Counter
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env si présent
load_dotenv()

app = Flask(__name__)

API_KEY_PAGESPEED = os.getenv("PSI_API_KEY", "AIzaSyAadcx3MR0Mx8Cg6KWYdztg5sMY7jHja4w")
API_KEY_OPR = os.getenv("OPR_API_KEY", "ss84cosk8g44sww8ckwwkwcsco8wkkks48wko0oc")

HEADERS = {"User-Agent": "SEO-Agent/1.0"}
STOPWORDS = {"le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "en", "que", "qui",
             "pour", "sur", "dans", "pas", "plus", "par", "avec", "au", "aux", "ce", "cette", "ces",
             "il", "elle", "ils", "elles", "vous", "nous", "je", "moi", "tu", "ton", "ta", "tes"}

def fetch_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ").strip()

def semantic_keywords(text, top_n=10):
    words = [re.sub(r"[^a-zàâäéèêëïîôöùûüç]", "", w.lower()) for w in text.split()]
    words = [w for w in words if w and w not in STOPWORDS and len(w) > 2]
    counts = Counter(words)
    return counts.most_common(top_n)

def get_backlinks_count(domain):
    if not API_KEY_OPR:
        return None
    try:
        api_url = f"https://openpagerank.com/api/v1.0/getPageRank?domains[]={domain}"
        headers = {"API-OPR": API_KEY_OPR}
        r = requests.get(api_url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return int(data["response"][0].get("backlinks_external", 0))
    except Exception:
        return None

@app.route("/analyze-seo")
def analyze_seo():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    encoded_url = urllib.parse.quote_plus(url)
    psi_url = (
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        f"?url={encoded_url}&key={API_KEY_PAGESPEED}"
        f"&category=SEO&category=PERFORMANCE&category=ACCESSIBILITY"
    )

    try:
        r = requests.get(psi_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return jsonify({"error": f"Erreur API PageSpeed : {str(e)}"}), 500

    audits = data.get("lighthouseResult", {}).get("audits", {})
    categories = data.get("lighthouseResult", {}).get("categories", {})

    def safe_get_score(name):
        return round(categories.get(name, {}).get("score", 0) * 100)

    def safe_get_list(audit_key):
        return audits.get(audit_key, {}).get("details", {}).get("items", []) or []

    html = fetch_html(url)
    content_text = extract_text(html)
    keywords = semantic_keywords(content_text)
    content_score = min(len(keywords) * 5, 100)

    performance_score = safe_get_score("performance")
    seo_score = safe_get_score("seo")
    accessibility_score = safe_get_score("accessibility")

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc
    backlinks = get_backlinks_count(domain)

    mobile_friendly = audits.get("viewport", {}).get("score")
    if mobile_friendly is not None:
        mobile_friendly = float(mobile_friendly)

    estimated_rank = max(1, int(100 - seo_score / 2))

    results = {
        "performance_score": performance_score,
        "seo_score": seo_score,
        "accessibility_score": accessibility_score,
        "semantic_keywords": keywords,
        "content_score": content_score,
        "mobile_friendly": mobile_friendly,
        "ssl": audits.get("is-on-https", {}).get("score", 0) == 1,
        "loading_time": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
        "missing_titles": len(safe_get_list("document-title")),
        "missing_meta_descriptions": len(safe_get_list("meta-description")),
        "images_without_alt": len(safe_get_list("image-alt")),
        "backlinks": backlinks,
        "rank_google": estimated_rank,
        "global_score": round((performance_score * 0.3 + seo_score * 0.3 + content_score * 0.2 + 20) / 1.0)
    }

    return jsonify(results)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)