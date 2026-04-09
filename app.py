"""LinkedIn to Portfolio Site - Flask Application."""
import os
import json
import tempfile
import shutil
from flask import Flask, render_template, request, jsonify

from lib.linkedin_parser import parse_linkedin_pdf
from lib.site_generator import generate_portfolio_html
from lib.cv_generator import generate_docx, generate_cv_html, generate_cv_pdf
from lib.vercel_deploy import deploy_to_vercel

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def parse_pdf():
    """Parse uploaded LinkedIn PDF and return structured data."""
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400

    pdf_file = request.files["pdf"]
    if not pdf_file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Save PDF temporarily
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf_file.save(tmp.name)
    tmp.close()

    try:
        data = parse_linkedin_pdf(tmp.name)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"error": f"Failed to parse PDF: {str(e)}"}), 500
    finally:
        os.unlink(tmp.name)


@app.route("/api/deploy", methods=["POST"])
def deploy():
    """Generate site + CV and deploy to Vercel."""
    try:
        # Get form data
        vercel_token = request.form.get("vercel_token", "").strip()
        project_name = request.form.get("project_name", "").strip().lower()
        custom_domain = request.form.get("custom_domain", "").strip()
        profile_data = request.form.get("profile_data", "")

        if not vercel_token:
            return jsonify({"error": "Vercel token is required"}), 400
        if not project_name:
            return jsonify({"error": "Project name is required"}), 400

        data = json.loads(profile_data)
        data["domain"] = custom_domain

        # Handle photo
        photo_file = request.files.get("photo")
        photo_bytes = None
        photo_ext = "png"
        photo_tmp = None

        if photo_file and photo_file.filename:
            photo_ext = photo_file.filename.rsplit(".", 1)[-1].lower() if "." in photo_file.filename else "png"
            photo_tmp = tempfile.NamedTemporaryFile(suffix=f".{photo_ext}", delete=False)
            photo_file.save(photo_tmp.name)
            photo_tmp.close()
            with open(photo_tmp.name, "rb") as f:
                photo_bytes = f.read()

        photo_filename = f"photo.{photo_ext}"
        cv_pdf_name = f"CV {data.get('name', 'CV')}.pdf"
        cv_docx_name = f"CV {data.get('name', 'CV')}.docx"

        # Generate portfolio site
        site_html = generate_portfolio_html(data, photo_filename=photo_filename, cv_filename=cv_pdf_name)

        # Generate CV HTML and PDF
        cv_html = generate_cv_html(data, photo_filename=photo_filename)

        cv_pdf_path = None
        cv_pdf_bytes = None
        try:
            cv_pdf_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            cv_pdf_tmp.close()
            generate_cv_pdf(cv_html, cv_pdf_tmp.name)
            with open(cv_pdf_tmp.name, "rb") as f:
                cv_pdf_bytes = f.read()
            cv_pdf_path = cv_pdf_tmp.name
        except Exception as e:
            print(f"Warning: PDF generation failed: {e}")

        # Generate DOCX
        docx_bytes = None
        try:
            docx_tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
            docx_tmp.close()
            generate_docx(data, photo_tmp.name if photo_tmp else None, docx_tmp.name)
            with open(docx_tmp.name, "rb") as f:
                docx_bytes = f.read()
            os.unlink(docx_tmp.name)
        except Exception as e:
            print(f"Warning: DOCX generation failed: {e}")

        # Prepare deployment files
        files = {
            "index.html": site_html.encode("utf-8"),
            "cv.html": cv_html.encode("utf-8"),
            "vercel.json": json.dumps({"cleanUrls": True}).encode("utf-8"),
        }

        if photo_bytes:
            files[photo_filename] = photo_bytes
        if cv_pdf_bytes:
            files[cv_pdf_name] = cv_pdf_bytes
        if docx_bytes:
            files[cv_docx_name] = docx_bytes

        # Deploy to Vercel
        result = deploy_to_vercel(vercel_token, project_name, files)

        # Add custom domain if provided
        domain_result = None
        if custom_domain:
            try:
                domain_result = add_domain(vercel_token, project_name, custom_domain)
            except Exception as e:
                domain_result = {"warning": str(e)}

        # Cleanup temp files
        if photo_tmp:
            os.unlink(photo_tmp.name)
        if cv_pdf_path and os.path.exists(cv_pdf_path):
            os.unlink(cv_pdf_path)

        return jsonify({
            "success": True,
            "deployment": result,
            "domain": domain_result,
            "files_deployed": list(files.keys()),
        })

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid profile data format"}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Deployment failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
