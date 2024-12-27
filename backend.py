import os
import boto3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'home-energy-application')
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Check if AWS credentials are loaded correctly
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS credentials are missing in the .env file")

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    region_name='us-east-2',  # Your AWS region
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum allowed file size for uploads (in bytes)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

@app.route('/energy/input', methods=['POST'])
def handle_form_data():
    """
    Endpoint to handle form data submission (Date and Usage).
    This endpoint accepts POST requests with form data (Date and Usage).

    Args:
        None

    Returns:
        JSON response with success or error message.
    """
    # Get date and usage from the form data
    date = request.form.get('date')
    usage = request.form.get('usage')

    if not date or not usage:
        logger.error("Date or usage is missing in the form data.")
        return jsonify({"error": "Both date and usage are required"}), 400

    # Log received data (this could be stored in a database in production)
    logger.info(f"Received data - Date: {date}, Usage: {usage}")

    # Ideally, save this data to a database (e.g., DynamoDB) here.
    # For now, we're just logging the data for demo purposes.

    return jsonify({"message": "Energy data saved successfully"}), 200


@app.route('/energy/upload', methods=['POST'])
def handle_file_upload():
    """
    Endpoint to handle file upload (CSV file) and upload the file to S3.

    This endpoint accepts POST requests with a file upload. The file is checked to ensure 
    it's a CSV file before uploading to the specified S3 bucket.

    Args:
        None

    Returns:
        JSON response indicating success or error.
    """
    if 'file' not in request.files:
        logger.error("No file part in the request.")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']

    if file.filename == '':
        logger.error("No file selected for upload.")
        return jsonify({"error": "No selected file"}), 400

    # Ensure file is a CSV file
    if file and file.filename.endswith('.csv'):
        try:
            # Secure the filename and save it temporarily
            filename = secure_filename(file.filename)

            # Upload the file directly to S3
            s3_client.upload_fileobj(file, S3_BUCKET_NAME, filename)

            # Optionally, you can make the file public or private
            # s3_client.put_object_acl(ACL='public-read', Bucket=S3_BUCKET_NAME, Key=filename)

            logger.info(f"File '{filename}' uploaded successfully to S3.")
            return jsonify({"message": "File uploaded successfully to S3"}), 200

        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return jsonify({"error": f"Error uploading file to S3: {e}"}), 500
    else:
        logger.error("Invalid file format. Only CSV files are allowed.")
        return jsonify({"error": "Invalid file format. Only CSV files are allowed."}), 400

# Run the application
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
