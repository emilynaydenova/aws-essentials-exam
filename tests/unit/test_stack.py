"""
Unit tests do not interact with live AWS services but verify the CDK template generation.
"""
import os

import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from aws_cdk import App
from aws_essentials_exam.aws_essentials_exam_stack import AwsEssentialsExamStack

from aws_essentials_exam.aws_essentials_exam_stack import AwsEssentialsExamStack


def test_stack_resources_count():
    # Initialize the app and stack
    app = App()
    asset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../website"))
    lambda_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lambda_code"))
    stack = AwsEssentialsExamStack(app, "TestStack",asset_path=asset_path,lambda_path=lambda_path)
    template = assertions.Template.from_stack(stack)

    # Test for the S3 buckets
    template.resource_count_is("AWS::S3::Bucket", 2)

    # Test for the Lambda functions
    template.resource_count_is("AWS::Lambda::Function", 6)

    # Test for the DynamoDB table
    template.resource_count_is("AWS::DynamoDB::Table", 1)


    # Test for the API Gateway
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)

    # Test for the SNS topic
    template.resource_count_is("AWS::SNS::Topic", 1)

