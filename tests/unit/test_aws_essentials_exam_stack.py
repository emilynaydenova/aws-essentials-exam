import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_essentials_exam.aws_essentials_exam_stack import AwsEssentialsExamStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_essentials_exam/aws_essentials_exam_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsEssentialsExamStack(app, "aws_essentials_exam")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })



def test_stack():
    app = core.App()
    stack = AwsEssentialsExamStack(app, "aws_essentials_exam")
    template = app.synth().get_stack_by_name("aws_essentials_exam").template
    assert "AWS::S3::Bucket" in template["Resources"]