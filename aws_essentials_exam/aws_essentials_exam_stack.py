import os

from aws_cdk import (
    Stack,

    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigateway,
    aws_events_targets as targets,
    aws_events as events,
    aws_lambda as _lambda,
    RemovalPolicy, CfnOutput, Duration,
)
from constructs import Construct


class AwsEssentialsExamStack(Stack):
    client_mail = "hristo.zhelev@yahoo.com"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for static website hosting
        upload_files_bucket = s3.Bucket(
            self,
            "UploadFilesBucket",  # here are stored uploaded by the client files
            bucket_name='uploaded-by-client',
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Deploy HTML files to the S3 bucket
        s3_deployment.BucketDeployment(
            self,
             "DeployWebsiteContent",
            sources=[s3_deployment.Source.asset("website")],  # Folder containing HTML files
            destination_bucket=upload_files_bucket,
        )

        # Output the website URL
        CfnOutput(
            self,
            "WebsiteURL",
            value=upload_files_bucket.bucket_website_url,
            description="URL for the static website",
        )


        # DynamoDB table for storing file metadata
        metadata_table = dynamodb.Table(
            self,
            "FilesMetadataTable",
            table_name="MetadataTable",
            partition_key=dynamodb.Attribute(name="file_extension", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="upload_date", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # SNS Topic for notifications
        notification_topic = sns.Topic(self, "Received File Notification")

        # Add an email subscription (update with the client's email)
        notification_topic.add_subscription(subscriptions.EmailSubscription(self.client_mail))

        # Lambda function to process file uploads
        processing_function = _lambda.Function(
            self,
            "FileExtensionProcessingFunction",
            function_name='processing-function',
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler='processing_function.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("lambda_code")),  # Code location
            memory_size=512,  # Memory size in MB (optional)
            timeout=Duration.seconds(10),  # Timeout in seconds (optional)
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "BUCKET_NAME": upload_files_bucket.bucket_name,
                "TABLE_NAME": metadata_table.table_name,
                "TOPIC_ARN": notification_topic.topic_arn,
            },
        )

        # Grant permissions to the Lambda function
        upload_files_bucket.grant_read(processing_function)
        metadata_table.grant_write_data(processing_function)
        notification_topic.grant_publish(processing_function)

        # Set up S3 event notification to trigger the Lambda function
        upload_files_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(processing_function),
        )

        # Lambda Function to delete old files
        cleanup_function = _lambda.Function(
            self,
            "CleanupFunction",
            function_name='cleanup-function',
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="cleanup_function.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("lambda_code")),
            environment={
                "BUCKET_NAME": upload_files_bucket.bucket_name,
            },
        )

        # Grant permissions to the Lambda function
        upload_files_bucket.grant_read_write(cleanup_function)

        # EventBridge rule to trigger the Lambda function every 30 minutes
        event_rule = events.Rule(
            self,
            "CleanupRule",
            schedule=events.Schedule.rate(Duration.minutes(30)),
        )
        event_rule.add_target(targets.LambdaFunction(cleanup_function))

        # Lambda function for querying DynamoDB
        query_function = _lambda.Function(
            self,
            "QueryFunction",
            function_name="query-function",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="query_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda_code"),  # Path to your Lambda code
            environment={
                "TABLE_NAME": metadata_table.table_name,
            },
        )

        # Grant the Lambda function read permissions on the DynamoDB table
        metadata_table.grant_read_data(query_function)

        # API Gateway to expose the Lambda function
        api = apigateway.RestApi(
            self,
            "FileMetadataApi",
            rest_api_name="FileMetadata Service",
            description="API for querying file metadata.",
        )

        # Define API Gateway endpoint
        query_integration = apigateway.LambdaIntegration(query_function)

        # Add a resource and method for querying
        metadata_resource = api.root.add_resource("metadata")
        metadata_resource.add_method("GET", query_integration)  # HTTP GET method
