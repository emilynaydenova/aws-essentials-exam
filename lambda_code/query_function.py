import boto3
import os
from boto3.dynamodb.conditions import Key
from urllib.parse import parse_qs

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["MetadataTable"]
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    # Parse query parameters
    query_params = event.get("queryStringParameters", {})
    file_extension = query_params.get("file_extension")

    if not file_extension:
        return {
            "statusCode": 400,
            "body": "Missing 'file_extension' query parameter.",
        }

    # Query DynamoDB for the given file extension
    try:
        response = table.query(
            KeyConditionExpression=Key("file_extension").eq(file_extension)
        )
        items = response.get("Items", [])
        return {
            "statusCode": 200,
            "body": f"Query results: {items}",
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error querying DynamoDB: {str(e)}",
        }