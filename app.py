from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Clé API Google PageSpeed Insights (à remplacer par la vôtre)
API_KEY = "VOTRE_CLE_API_GOOGLE"

@app.route('/analyze-seo', methods=['GET'])
def analyze_seo():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # 1. Analyse PageSpeed Insights
    psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}"
    psi_response = requests.get(psi_url).json()
    
    # 2. Vérification basique SEO (exemple simplifié)
    seo_checks = {
        "title": "Non vérifié (nécessite un scraper)",
        "meta_description": "Non vérifié",
        "h1_tags": "Non vérifié",
        "images_alt": "Non vérifié",
        "performance_score": psi_response.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0) * 100
    }

    return jsonify({
        "url": url,
        "seo_checks": seo_checks,
        "psi_data": psi_response  # Données brutes de PageSpeed
    })

if __name__ == '__main__':
    app.run(debug=True)
