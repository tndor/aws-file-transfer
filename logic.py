import boto3
import sys
import os, io
import uuid
import zipfile
from datetime import datetime

from pathlib import Path
from botocore.exceptions import ClientError

import dotenv
dotenv.load_dotenv()

aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'us-east-1')
bucket_name = os.getenv('BUCKET_NAME')

DEFAULT_EXPIRATION = 259200

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
    
    def upload_folder(self, folder_path, object_name=None):

        # Get all files from folder
        folder = Path(folder_path)
        files = [f for f in folder.rglob('*') if f.is_file()]
        
        if object_name is not None:
            s3_folder = str(uuid.uuid4()) + '/' + str(object_name) + '/'
        
        try:
            for file in files:
                relative_path = file.relative_to(folder)
                print(str(s3_folder) + str(relative_path))
                self.upload_file(str(file), str(s3_folder) + str(relative_path))
            return True, s3_folder
        except ClientError as e:
            print(f"Error uploading folder: {e}")
            return False
        
    def create_presigned_urls_for_folder(self, bucket_name, folder_prefix, expiration=DEFAULT_EXPIRATION):
        """
        Create presigned URLs for all files in an S3 folder
        
        Args:
            bucket_name (str): Name of the S3 bucket
            folder_prefix (str): Folder path (e.g., 'my-folder/' or 'path/to/folder/')
            expiration (int): URL expiration time in seconds (default: 3 days)
        
        Returns:
            dict: Dictionary with file keys and their presigned URLs
        """
        presigned_urls = {}
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
            
            if 'Contents' not in response:
                print(f"No files found in folder {folder_prefix}")
                return presigned_urls
            
            for file in response['Contents']:
                file_key = file['Key']
                print(file_key)
                
                if file_key.endswith('/'):
                    continue  # Skip folders
                
                try:
                    presigned_url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': file_key},
                        ExpiresIn=expiration
                    )
                    presigned_urls[file_key] = presigned_url
                except ClientError as e:
                    print(f"Error generating presigned URL for {file_key}: {e}")
                
        except ClientError as e:
            print(f"Error listing objects: {e}")
        
        return presigned_urls
    
    
    def create_zip_download(self, bucket_name, folder_prefix, object_name=None):
        """
        Create a ZIP file of all files in folder and return its download URL
        """
        
        # List files in folder
        response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for obj in response.get('Contents', []):
                if not obj['Key'].endswith('/'):  # Skip folders
                    # Get file content
                    file_content = self.s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])['Body'].read()
                    # Add to ZIP
                    filename = obj['Key'].split('/')[-1]  # Just the filename
                    zip_file.writestr(filename, file_content)
        
        # Upload ZIP to S3
        zip_key = f"temp/{object_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=zip_key,
            Body=zip_buffer.getvalue()
        )
        
        # Return presigned URL for ZIP
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': zip_key},
            ExpiresIn=DEFAULT_EXPIRATION
        )



uploader = S3Uploader()
handler = uploader.upload_folder('./templates', "html files")
uuid = handler[1]

print(uploader.create_presigned_urls_for_folder(bucket_name, uuid))
print(uploader.create_zip_download(bucket_name, uuid, "html files"))