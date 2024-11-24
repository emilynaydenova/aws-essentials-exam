import boto3
import os
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = os.environ['uploaded-by-client']
    retention_period = timedelta(minutes=30)

    # List objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            obj_time = obj['LastModified']
            if datetime.now(timezone.utc) - obj_time > retention_period:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
    return {"statusCode": 200, "body": "Cleanup successfully"}
