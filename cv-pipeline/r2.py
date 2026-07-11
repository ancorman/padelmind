import os
import boto3
from botocore.config import Config

ACCOUNT_ID   = "5cea7760e2a9ac11cdeb84ea116ff839"
ENDPOINT_URL = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
PUBLIC_BASE  = "https://pub-04c202b65f234888bf415f2ec899d7f8.r2.dev"

VIDEOS_BUCKET  = "padelmind-videos"
OUTPUTS_BUCKET = "padelmind-outputs"


def _client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def download(r2_key: str, local_path: str):
    _client().download_file(VIDEOS_BUCKET, r2_key, local_path)


def upload(local_path: str, r2_key: str) -> str:
    _client().upload_file(local_path, OUTPUTS_BUCKET, r2_key)
    return f"{PUBLIC_BASE}/{r2_key}"


def upload_bytes(data: bytes, r2_key: str, content_type: str = "application/octet-stream") -> str:
    _client().put_object(Bucket=OUTPUTS_BUCKET, Key=r2_key, Body=data, ContentType=content_type)
    return f"{PUBLIC_BASE}/{r2_key}"
