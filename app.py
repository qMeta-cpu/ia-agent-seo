from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Clé API Google PageSpeed Insights (à remplacer par la vôtre)
API_KEY = "AIzaSyAadcx3MR0Mx8Cg6KWYdztg5sMY7jHja4w"


@app.route('/analyze-seo', methods=['GET'])
def analyze_seo():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # Récupération des données
    psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}&category=SEO&category=PERFORMANCE"
    psi_data = requests.get(psi_url).json()
    audits = psi_data.get("lighthouseResult", {}).get("audits", {})
    categories = psi_data.get("lighthouseResult", {}).get("categories", {})

    # Métriques principales
    results = {
        # Scores globaux
        "performance_score": round(categories.get("performance", {}).get("score", 0) * 100,
        "seo_score": round(categories.get("seo", {}).get("score", 0) * 100,
        "accessibility_score": round(categories.get("accessibility", {}).get("score", 0) * 100,
        
        # Technique
        "loading_time": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
        "mobile_friendly": audits.get("viewport", {}).get("score", 0) == 1,
        "ssl": audits.get("is-on-https", {}).get("score", 0) == 1,
        
        # Contenu
        "missing_titles": len(audits.get("document-title", {}).get("details", {}).get("items", [])),
        "missing_meta_descriptions": len(audits.get("meta-description", {}).get("details", {}).get("items", [])),
        "images_without_alt": len(audits.get("image-alt", {}).get("details", {}).get("items", [])),
        
        # Liens
        "internal_links": audits.get("internal-links", {}).get("numericValue", 0),
        "external_links": audits.get("external-links", {}).get("numericValue", 0),
        "broken_links": len(audits.get("broken-links", {}).get("details", {}).get("items", [])),
        
        # Best Practices
        "has_structured_data": audits.get("structured-data", {}).get("score", 0) == 1,
        "proper_heading_hierarchy": audits.get("heading-order", {}).get("score", 0) == 1,
        "font_sizes_legible": audits.get("font-size", {}).get("score", 0) == 1
    }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
