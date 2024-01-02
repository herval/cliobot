import boto3
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self, access_key, secret, bucket, region):
        self.bucket = bucket
        self.s3 = boto3.client('s3',
                               aws_access_key_id=access_key,
                               aws_secret_access_key=secret,
                               region_name=region)
        self.bucket = bucket
        print(f'Connected to S3')

    def full_path(self, path):
        return self.base_path() + path

    def upload_file(self, file, key):
        self.s3.upload_file(file, self.bucket, key)


    def base_path(self):
        return f'https://{self.bucket}.s3.amazonaws.com/'

    def save_data(self, data, path, mimetype):
        self.s3.put_object(Body=data, Bucket=self.bucket, Key=path, ContentType=mimetype)

    def get_data(self, path):
        return self.fetch_file(path)['Body'].read()

    def exists(self, path):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise e

    def get_data_text(self, path):
        return self.fetch_file(path)['Body'].read().decode('UTF-8')

    def fetch_file(self, key):
        return self.s3.get_object(Bucket=self.bucket, Key=key)

    def stream_data(self, path, localpath):
        try:
            return self.s3.download_file(self.bucket, path, localpath)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
                raise FileNotFoundError(path)
            raise e
