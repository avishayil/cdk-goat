"""Main module for CDK application."""

# !/usr/bin/env python3

import aws_cdk as cdk

from cdk.cdk_goat_service.cdk_goat_stack import CDKGoatStack

app = cdk.App()

CDKGoatStack(
    app,
    "CDKGoatStack",
)

app.synth()
