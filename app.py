from flask import Flask, request, jsonify
import requests
import urllib.parse  # à sa bonne place, en haut

app = Flask(__name__)

# Clé API Google PageSpeed Insights (à remplacer par la vôtre)
API_KEY = "AIzaSyAadcx3MR0Mx8Cg6KWYdztg5sMY7jHja4w"

@app.route('/analyze-seo', methods=['GET'])
def analyze_seo():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # Encodage de l’URL saisie par l’utilisateur
    encoded_url = urllib.parse.quote_plus(url)

    # Création de l'URL pour l'API PageSpeed avec l’URL encodée
    psi_url = (
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        f"?url={encoded_url}&key={API_KEY}&category=SEO&category=PERFORMANCE"
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
from flask import render_template_string
@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Analyse SEO avec qMeta Agent</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 30px; background-color: #f8f9fa; }
            .score-bar {
                height: 30px;
                font-weight: bold;
                font-size: 1.1em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">Analyse SEO avec qMeta Agent</h1>
            <div class="mb-3">
                <input type="text" id="urlInput" class="form-control" placeholder="https://exemple.com">
            </div>
            <button class="btn btn-primary mb-4" onclick="analyze()">Analyser</button>

            <div id="resultSection" style="display:none;">
                <h3>Performance</h3>
                <div class="progress mb-3">
                    <div id="performanceBar" class="progress-bar score-bar" role="progressbar" style="width: 0%;">
                        0%
                    </div>
                </div>

                <div class="mb-3">
                    <span class="badge bg-success" id="seoScore">SEO: 0%</span>
                    <span class="badge bg-info text-dark" id="accessibilityScore">Accessibilité: 0%</span>
                    <span class="badge bg-secondary" id="mobileFriendly">Mobile Friendly</span>
                    <span class="badge bg-danger" id="sslStatus">HTTPS</span>
                </div>

                <h4>Détails techniques</h4>
                <ul id="detailsList" class="list-group mb-3"></ul>
            </div>

            <div id="errorMessage" class="alert alert-danger" style="display:none;"></div>
        </div>

        <script>
            function setPerformanceBar(score) {
                const bar = document.getElementById('performanceBar');
                bar.style.width = score + "%";
                bar.textContent = score + "%";

                // Couleur selon score
                if (score >= 90) bar.className = "progress-bar score-bar bg-success";
                else if (score >= 50) bar.className = "progress-bar score-bar bg-warning text-dark";
                else bar.className = "progress-bar score-bar bg-danger";
            }

            function analyze() {
                const url = document.getElementById('urlInput').value;
                if (!url) {
                    alert("Merci d'entrer une URL !");
                    return;
                }

                fetch(`/analyze-seo?url=${encodeURIComponent(url)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            document.getElementById('resultSection').style.display = 'none';
                            document.getElementById('errorMessage').style.display = 'block';
                            document.getElementById('errorMessage').textContent = data.error;
                            return;
                        }

                        document.getElementById('resultSection').style.display = 'block';
                        document.getElementById('errorMessage').style.display = 'none';

                        setPerformanceBar(data.performance_score);
                        document.getElementById('seoScore').textContent = "SEO: " + data.seo_score + "%";
                        document.getElementById('accessibilityScore').textContent = "Accessibilité: " + data.accessibility_score + "%";
                        document.getElementById('mobileFriendly').className = data.mobile_friendly ? "badge bg-success" : "badge bg-warning";
                        document.getElementById('mobileFriendly').textContent = data.mobile_friendly ? "Mobile Friendly" : "Pas Mobile";
                        document.getElementById('sslStatus').className = data.ssl ? "badge bg-success" : "badge bg-danger";
                        document.getElementById('sslStatus').textContent = data.ssl ? "HTTPS OK" : "HTTPS Manquant";

                        const details = [
                            "Temps de chargement : " + data.loading_time + " ms",
                            "Titres manquants : " + data.missing_titles,
                            "Meta descriptions manquantes : " + data.missing_meta_descriptions,
                            "Images sans alt : " + data.images_without_alt,
                            "Liens internes : " + (data.internal_links ?? "N/A"),
                            "Liens externes : " + (data.external_links ?? "N/A"),
                            "Liens cassés : " + data.broken_links,
                            "Données structurées : " + (data.has_structured_data ? "Oui" : "Non"),
                            "Hiérarchie des titres correcte : " + (data.proper_heading_hierarchy ? "Oui" : "Non"),
                            "Tailles de police lisibles : " + (data.font_sizes_legible ? "Oui" : "Non")
                        ];

                        const list = document.getElementById('detailsList');
                        list.innerHTML = "";
                        details.forEach(item => {
                            const li = document.createElement("li");
                            li.className = "list-group-item";
                            li.textContent = item;
                            list.appendChild(li);
                        });
                    })
                    .catch(err => {
                        document.getElementById('resultSection').style.display = 'none';
                        document.getElementById('errorMessage').style.display = 'block';
                        document.getElementById('errorMessage').textContent = "Erreur : " + err;
                    });
            }
        </script>
    </body>
    </html>
    ''')
if __name__ == '__main__':
    app.run(debug=True)
