#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_essentials_exam.aws_essentials_exam_stack import AwsEssentialsExamStack

app = cdk.App()
AwsEssentialsExamStack(app,"AwsEssentialsExamStack",
                       env=cdk.Environment(account='038462785074', region='eu-central-1'),
                       )

app.synth()
