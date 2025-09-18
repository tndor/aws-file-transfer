from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
CORS(app)

@app.route('/')
def index():
    """Render the main landing page"""
    return render_template('index.html')

@app.route('/d/<share_id>')
def download_page(share_id):
    """Render the download page for a shared transfer"""
    # TODO: Fetch actual file information from database/S3
    return render_template('download.html', share_id=share_id)

@app.route('/api/upload', methods=['POST'])
def upload():
    """Handle file upload requests"""
    # TODO: Implement S3 upload logic
    return jsonify({'message': 'Upload endpoint - to be implemented'})

@app.route('/api/download/<file_id>', methods=['GET'])
def download(file_id):
    """Handle file download requests"""
    # TODO: Implement S3 download logic
    return jsonify({'message': f'Download endpoint for {file_id} - to be implemented'})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'tndtransfer'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)