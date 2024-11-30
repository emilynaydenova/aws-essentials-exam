"""
This module defines the AWS Essentials Exam Stack.
"""
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
    aws_iam as iam,
    aws_events as events,
    aws_lambda as _lambda,
    RemovalPolicy, CfnOutput, Duration,
)
from constructs import Construct


class AwsEssentialsExamStack(Stack):
    """
    This class is responsible for AWS Stack functionality.
    """

    client_mail = "emilia_n2@yahoo.com"
    # Set default path if not provided


    def __init__(self, scope: Construct, construct_id: str,asset_path=None,lambda_path=None,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.asset_path = asset_path or os.path.abspath("website")
        self.lambda_path = lambda_path or os.path.abspath("lambda_code")

        # S3 bucket for static website hosting
        static_site_bucket = s3.Bucket(
            self,
            "StaticSiteBucket",
            bucket_name="exam-static-website-bucket",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Deploy the static website content
        s3_deployment.BucketDeployment(
            self,
            "DeployStaticSiteContent",
            sources=[s3_deployment.Source.asset(self.asset_path)],  # Folder containing HTML files
            destination_bucket=static_site_bucket,
        )

        # Output the static website URL
        CfnOutput(
            self,
            "StaticSiteURL",
            value=static_site_bucket.bucket_website_url,
            description="URL for the static website",
        )

        # --------------
        # S3 bucket for storing uploaded files
        upload_files_bucket = s3.Bucket(
            self,
            "UploadFilesBucket",
            bucket_name="uploaded-by-client",
            versioned=True,  # Optional: Enables versioning for better file management
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            # Automatically delete the bucket during stack cleanup
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,  # Deletes bucket objects automatically
            encryption=s3.BucketEncryption.S3_MANAGED,  # Enables encryption
        )

        # Grant permissions for uploads (e.g., via a web app or Lambda)
        upload_files_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:DeleteObject"],
                resources=[upload_files_bucket.arn_for_objects("*")],
                # Use specific IAM roles or users in production
                principals=[iam.AnyPrincipal()],
                conditions={
                    # Optional: Restrict uploads to requests with specific headers (like Referer)
                    # "StringEquals": {"aws:Referer": "your-site-url"}
                },
            )
        )

        # Output the S3 bucket name
        CfnOutput(
            self,
            "UploadFilesBucketName",
            value=upload_files_bucket.bucket_name,
            description="S3 Bucket Name for Uploading Files",
        )

        # Output the S3 bucket ARN
        CfnOutput(
            self,
            "UploadFilesBucketARN",
            value=upload_files_bucket.bucket_arn,
            description="S3 Bucket ARN for Uploading Files",
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
        notification_topic = sns.Topic(self, "Received File")

        # Add an email subscription (update with the client's email)
        notification_topic.add_subscription(subscriptions.EmailSubscription(self.client_mail))

        # Lambda function to process file uploads
        processing_function = _lambda.Function(
            self,
            "FileExtensionProcessingFunction",
            function_name='processing-function',
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler='processing_function.lambda_handler',
            code=_lambda.Code.from_asset(self.lambda_path),  # Code location
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
            code=_lambda.Code.from_asset(self.lambda_path),
            environment={
                "BUCKET_NAME": upload_files_bucket.bucket_name,
            },
        )

        # Grant permissions to the Lambda function
        upload_files_bucket.grant_read_write(cleanup_function)

        # EventBridge rule to trigger the Lambda function every 30 minutes
        # The first invocation of the rule starts approximately when the rule is created
        # or enabled.

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
            code=_lambda.Code.from_asset(self.lambda_path),  # Path to the Lambda code
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
            rest_api_name="FileMetadataService",
            description="API without authorization for querying file metadata.",
        )

        # Add a resource and method for querying
        metadata_resource = api.root.add_resource("metadata")
        metadata_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                query_function,
                integration_responses=[
                    apigateway.IntegrationResponse(status_code="200")
                ],
                request_parameters={
                    "integration.request.querystring.file_extension": "method.request.querystring.file_extension",
                }
            ),
            request_parameters={
                "method.request.querystring.file_extension": True,  # Required query parameter
            },
            authorization_type=apigateway.AuthorizationType.NONE
        )
