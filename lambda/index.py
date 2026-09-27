import json
import logging
import os
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3
import psycopg2

logger = logging.getLogger()
logger.setLevel(logging.INFO)
secrets = boto3.client("secretsmanager")
s3 = boto3.client("s3")


def get_database_credentials():
    secret = secrets.get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
    return json.loads(secret["SecretString"])


def handler(event, context):
    logger.info("Received S3 event: %s", json.dumps(event))
    credentials = get_database_credentials()
    masked_password = credentials["password"][:2] + "*" * (len(credentials["password"]) - 2)
    logger.info(
        "Retrieved DB credentials from Secrets Manager: username=%s dbname=%s password=%s",
        credentials["username"],
        credentials["dbname"],
        masked_password,
    )
    connection = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=5432,
        dbname=credentials["dbname"],
        user=credentials["username"],
        password=credentials["password"],
        connect_timeout=5,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS uploaded_documents (
                    id BIGSERIAL PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    upload_timestamp TIMESTAMPTZ NOT NULL
                )"""
            )
            for record in event.get("Records", []):
                object_data = record.get("s3", {}).get("object", {})
                object_key = unquote_plus(object_data.get("key", ""))
                file_name = object_key.split("/")[-1]
                metadata = s3.head_object(Bucket=os.environ["UPLOAD_BUCKET"], Key=object_key)
                content_type = metadata.get("ContentType", "application/octet-stream")
                cursor.execute(
                    "INSERT INTO uploaded_documents (file_name, content_type, upload_timestamp) VALUES (%s, %s, %s)",
                    (file_name, content_type, datetime.now(timezone.utc)),
                )
                logger.info("Recorded file_name=%s content_type=%s", file_name, content_type)
            cursor.execute("SELECT COUNT(*) FROM uploaded_documents")
            logger.info("Total rows in uploaded_documents: %s", cursor.fetchone()[0])
        connection.commit()
        return {"statusCode": 200, "body": json.dumps("Processed upload event")}
    finally:
        connection.close()