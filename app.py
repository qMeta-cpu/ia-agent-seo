from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Clé API Google PageSpeed Insights (à remplacer par la vôtre)
API_KEY = "AIzaSyAadcx3MR0Mx8Cg6KWYdztg5sMY7jHja4w"

@app.route('/analyze-seo', methods=['GET'])
def analyze_seo():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # Récupération des données depuis l'API PageSpeed
    psi_url = (
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        f"?url={url}&key={API_KEY}&category=SEO&category=PERFORMANCE"
    )
    
    try:
        response = requests.get(psi_url)
        response.raise_for_status()
        psi_data = response.json()
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'appel à l'API: {str(e)}"}), 500

    audits = psi_data.get("lighthouseResult", {}).get("audits", {})
    categories = psi_data.get("lighthouseResult", {}).get("categories", {})

    def safe_get_list(audit_key):
        return audits.get(audit_key, {}).get("details", {}).get("items", []) or []

    results = {
        # Scores globaux
        "performance_score": round(categories.get("performance", {}).get("score", 0) * 100),
        "seo_score": round(categories.get("seo", {}).get("score", 0) * 100),
        "accessibility_score": round(categories.get("accessibility", {}).get("score", 0) * 100),

        # Technique
        "loading_time": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
        "mobile_friendly": audits.get("viewport", {}).get("score", 0) == 1,
        "ssl": audits.get("is-on-https", {}).get("score", 0) == 1,

        # Contenu
        "missing_titles": len(safe_get_list("document-title")),
        "missing_meta_descriptions": len(safe_get_list("meta-description")),
        "images_without_alt": len(safe_get_list("image-alt")),

        # Liens (ces audits peuvent ne pas exister, donc on vérifie d'abord)
        "internal_links": audits.get("internal-links", {}).get("numericValue", None),
        "external_links": audits.get("external-links", {}).get("numericValue", None),
        "broken_links": len(safe_get_list("broken-links")),

        # Best Practices
        "has_structured_data": audits.get("structured-data", {}).get("score", 0) == 1,
        "proper_heading_hierarchy": audits.get("heading-order", {}).get("score", 0) == 1,
        "font_sizes_legible": audits.get("font-size", {}).get("score", 0) == 1
    }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
