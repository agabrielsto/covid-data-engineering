
import os

import boto3
from dotenv import load_dotenv
from botocore.config import Config

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configura a conexão com o armazenamento S3
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"}
    )
)

def test_connection():
    try:
        response = s3.list_buckets()

        print("Conexão com o SILO realizada com sucesso!")
        print("\nBuckets encontrados:")

        for bucket in response["Buckets"]:
            print(f"- {bucket['Name']}")

    except Exception as error:
        print(f"Erro ao conectar com o SILO: {error}")


if __name__ == "__main__":
    test_connection()
