from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    RemovalPolicy, CfnOutput, Duration,
)
from constructs import Construct


class AwsEssentialsExamStack(Stack):

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