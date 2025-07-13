from flask import Flask, request, render_template_string, jsonify
import requests
from werkzeug.utils import secure_filename
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key for production
UPLOAD_FOLDER = 'received_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# HTML template for the frontend
UPLOAD_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>File Transfer App</title>
    <style>
        .progress { display: none; margin-top: 10px; }
        .progress-bar { width: 0%; height: 20px; background-color: #4caf50; }
    </style>
</head>
<body>
    <h2>Send File to Another Device</h2>
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" name="file" id="fileInput">
        <input type="text" name="target" id="targetInput" placeholder="Target address (e.g., 192.168.1.100)">
        <input type="submit" value="Send File">
    </form>
    <div class="progress" id="progressContainer">
        <div class="progress-bar" id="progressBar"></div>
        <span id="progressText">0%</span>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const targetInput = document.getElementById('targetInput');
            const file = fileInput.files[0];
            const target = targetInput.value;

            if (!file) {
                alert('Please select a file');
                return;
            }
            if (!target) {
                alert('Please enter a target address');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('target', target);

            const xhr = new XMLHttpRequest();
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            const progressContainer = document.getElementById('progressContainer');

            xhr.upload.addEventListener('progress', function(event) {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                    progressText.textContent = Math.round(percentComplete) + '%';
                    progressContainer.style.display = 'block';
                }
            });

            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    alert(response.message);
                } else {
                    alert('Error sending file');
                }
                fileInput.value = '';
                targetInput.value = '';
                progressContainer.style.display = 'none';
            });

            xhr.addEventListener('error', function() {
                alert('Error sending file');
                progressContainer.style.display = 'none';
            });

            xhr.open('POST', '/send', true);
            xhr.send(formData);
        });
    </script>
</body>
</html>
'''

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the frontend
@app.route('/')
def index():
    return render_template_string(UPLOAD_FORM)

# Route to send a file to another device
@app.route('/send', methods=['POST'])
def send_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    target = request.form.get('target')
    if not target:
        return jsonify({'status': 'error', 'message': 'Target address is required'}), 400

    target_url = f'http://{target}:5000/receive'  # Assumes both apps run on port 5000
    try:
        response = requests.post(target_url, files={'file': (file.filename, file.stream, file.content_type)})
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'File sent successfully'})
        else:
            return jsonify({'status': 'error', 'message': f'Failed to send file: {response.text}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Error sending file: {str(e)}'}), 500

# Route to receive a file from another device
@app.route('/receive', methods=['POST'])
def receive_file():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'error': 'No file selected'}, 400

    if not allowed_file(file.filename):
        return {'error': 'Invalid file type'}, 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Handle filename conflicts
    base, extension = os.path.splitext(filename)
    counter = 1
    while os.path.exists(file_path):
        filename = f"{base} ({counter}){extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        counter += 1

    try:
        file.save(file_path)
        return {'message': f'File {filename} received and saved'}, 200
    except Exception as e:
        return {'error': f'Error saving file: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
