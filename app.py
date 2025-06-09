# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from image_logic import find_duplicates_by_message_part

app = Flask(__name__)
CORS(app, resources={r"/process-images": {"origins": "*"}})

@app.route('/process-images', methods=['POST'])
def process_images():
    data = request.json
    drive_url = data.get('drive_url')
    coords = data.get('coords')  # Expecting [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

    if not drive_url or not coords or len(coords) != 4:
        return jsonify({"status": "error",
                        "message": "Missing drive_url or coordinates",
                        "duplicates": {}}), 400

    try:
        folder_id = drive_url.split("/folders/")[1].split("?")[0]
        # coords already in correct format
        duplicates = find_duplicates_by_message_part(folder_id, coords)

        # Always include duplicates key
        return jsonify({
            "status": "success",
            "message": "Duplicates found." if duplicates else "No duplicates found.",
            "duplicates": duplicates
        })

    except Exception as e:
        return jsonify({"status": "error",
                        "message": str(e),
                        "duplicates": {}}), 500

if __name__ == '__main__':
    app.run(debug=True)
