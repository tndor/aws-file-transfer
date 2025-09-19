import boto3
import sys
import os
import uuid

from pathlib import Path
from botocore.exceptions import ClientError

import dotenv
dotenv.load_dotenv()

aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'us-east-1')
bucket_name = os.getenv('BUCKET_NAME')

s3_client = boto3.client('s3', region_name=aws_region)

class S3Uploader:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        self.bucket_name = bucket_name
    
    def progress_callback(self, bytes_transferred):
        sys.stdout.write(f"\rTransferred: {bytes_transferred} bytes \n")
        sys.stdout.flush()
        
    def upload_file(self, file_name, object_name=None):
        if object_name is None:
            object_name = file_name
        
        try:
            self.s3_client.upload_file(file_name, self.bucket_name, object_name, Callback=self.progress_callback)
            print(f"File {file_name} uploaded to {self.bucket_name}/{object_name}")
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False
        return True
    
    def upload_folder(self, folder_path):
        # Get all files from folder
        folder = Path(folder_path)
        files = [f for f in folder.rglob('*') if f.is_file()]
        
        s3_folder = str(uuid.uuid4()) + '/'
        
        try:
            for file in files:
                relative_path = file.relative_to(folder)
                print(str(s3_folder) + str(relative_path))
                self.upload_file(str(file), str(s3_folder) + str(relative_path))
            return True
        except ClientError as e:
            print(f"Error uploading folder: {e}")
            return False


uploader = S3Uploader()
print(uploader.upload_folder('./templates'))