
import boto3
import os
import json
from datetime import datetime

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

def lambda_handler(event, context):
    bucket_name = os.environ["BUCKET_NAME"]
    table_name = os.environ["TABLE_NAME"]
    topic_arn = os.environ["TOPIC_ARN"]

    table = dynamodb.Table(table_name)

    for record in event["Records"]:
        # Parse S3 event details
        key = record["s3"]["object"]["key"]
        size = record["s3"]["object"]["size"]
        extension = key.split(".")[-1].lower()
        allowed_extensions = ["pdf", "jpg", "png"]

        if extension not in allowed_extensions:
            # Invalid extension, notify client
            sns.publish(
                TopicArn=topic_arn,
                Message=f"Invalid file uploaded: {key} (Extension: {extension})",
                Subject="File Upload Error",
            )
            continue

        # Valid file, store metadata in DynamoDB
        upload_date = datetime.now().isoformat()
        table.put_item(
            Item={
                "file_extension": extension,
                "upload_date": upload_date,
                "file_size": size,
                "file_name": key,
            }
        )

        # Notify client
        sns.publish(
            TopicArn=topic_arn,
            Message=f"File uploaded successfully: {key}\nSize: {size} bytes\nExtension: {extension}\nDate: {upload_date}",
            Subject="File Upload Success",
        )

    return {"statusCode": 200, "body": "Metadata stored successfully"}
