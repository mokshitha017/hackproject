from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os
from video_translator import process_local_video, process_youtube_video

UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        lang_codes = request.form.getlist("languages")
        input_type = request.form.get("input_type")

        if input_type == "youtube":
            youtube_url = request.form.get("youtube_url")
            outputs = process_youtube_video(youtube_url, lang_codes)
        else:
            uploaded_file = request.files["video_file"]
            if uploaded_file.filename == "":
                return "No file selected"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            uploaded_file.save(filepath)
            outputs = process_local_video(filepath, lang_codes)

        return render_template("result.html", outputs=outputs)
    return render_template("index.html")

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(directory="final_outputs", path=filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
