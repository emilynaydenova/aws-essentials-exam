import os

from aws_cdk import (
    Stack,

    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_s3_notifications as s3_notifications,
    aws_lambda as _lambda,
    RemovalPolicy, CfnOutput, Duration,
)
from constructs import Construct


class AwsEssentialsExamStack(Stack):
    client_mail = "emilia_n2@yahoo.com"

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
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler='lambda_function.lambda_handler',
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
