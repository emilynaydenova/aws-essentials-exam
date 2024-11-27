from datetime import datetime

import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)


def convert_bytes_to_units(byte_value):
    """
    Convert a decimal value (in bytes) into KB, MB, GB, etc.

    :param byte_value: Value in bytes (integer or float)
    :return: A string representing the size in a readable format
    """
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    size = float(byte_value)
    unit_index = 0

    # Divide by 1024 to move to the next unit
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def lambda_handler(event, context):
    # Parse query parameters
    query_params = event.get("queryStringParameters", {})
    file_extension = query_params.get("file_extension", None)

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
        output = ["Query results: "]
        for item in items:
            size = convert_bytes_to_units(item['file_size'])
            upload_date =  datetime.fromisoformat(item['upload_date']).strftime('%d.%m.%Y at %H:%M')
            output.append(
                f"- {item['file_name']} with size {size} and uploaded on {upload_date}")
        return {
            "statusCode": 200,
            "body": f"{'\n'.join(output)}",
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error querying DynamoDB: {str(e)}",
        }
