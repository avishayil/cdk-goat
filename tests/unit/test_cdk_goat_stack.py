"""CDK Stack test module."""

from unittest import TestCase

import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk.cdk_goat_service.cdk_goat_stack import CDKGoatStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_goat/cdk_goat_stack.py


class TestCDKGoatStack(TestCase):
    def setUp(self):
        # Create a CDK app and stack for testing
        self.app = core.App()
        self.stack = CDKGoatStack(self.app, "TestStack")
        self.template = assertions.Template.from_stack(self.stack)  # noqa: F841

    def test_s3_bucket_insecure(self):
        """Test case: does the synthesized stack have a public S3 bucket."""

        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": False,
                    "BlockPublicPolicy": False,
                    "IgnorePublicAcls": False,
                    "RestrictPublicBuckets": False,
                },
            },
        )

    def test_rds_instance_insecure(self):
        """Test case: does the synthesized stack have an RDS instance that is publicly accessible."""

        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "PubliclyAccessible": True,
                "EnableIAMDatabaseAuthentication": False,
                "StorageEncrypted": False,
            },
        )

    def test_ecs_service_insecure(self):
        """Test case: does the synthesized stack have an ECS service that is publicly accessible."""

        self.template.has_resource_properties(
            "AWS::ECS::Service",
            {
                "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                    "AwsvpcConfiguration": {
                        "AssignPublicIp": "ENABLED",
                    },
                },
            },
        )

    def test_elastic_load_balancer_insecure(self):
        """Test case: does the Elastic Load Balancer have insecure configurations."""

        self.template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {
                "Scheme": "internet-facing",
                "LoadBalancerAttributes": [
                    {"Key": "deletion_protection.enabled", "Value": "false"},
                    {
                        "Key": "routing.http.drop_invalid_header_fields.enabled",
                        "Value": "true",
                    },
                ],
            },
        )

    def test_security_group_insecure(self):
        """Test case: do security groups have insecure inbound rules."""

        self.template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "Allow traffic from development endpoints",
                        "FromPort": 80,
                        "IpProtocol": "tcp",
                        "ToPort": 80,
                    }
                ]
            },
        )
