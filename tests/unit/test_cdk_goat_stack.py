"""CDK Stack test module.

These tests intentionally assert that the synthesized CloudFormation template
contains the DELIBERATELY INSECURE configurations that make CDK Goat a useful
training target. They are guardrails that lock in the intended vulnerable
design: if a refactor accidentally "fixes" one of these misconfigurations, the
corresponding test will fail. Do not "harden" the constructs to make these
tests pass differently.
"""

from unittest import TestCase

import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk.assertions import Match

from cdk.cdk_goat_service.cdk_goat_stack import CDKGoatStack


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

    def test_database_security_group_open_ingress(self):
        """Test case: DB security group exposes PostgreSQL (5432) to the world."""

        self.template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            Match.object_like(
                {
                    "SecurityGroupIngress": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "CidrIp": "0.0.0.0/0",
                                    "FromPort": 5432,
                                    "ToPort": 5432,
                                    "IpProtocol": "tcp",
                                }
                            )
                        ]
                    )
                }
            ),
        )

    def test_public_subnets_auto_assign_public_ip(self):
        """Test case: public subnets auto-assign public IPs on launch."""

        self.template.has_resource_properties(
            "AWS::EC2::Subnet",
            Match.object_like({"MapPublicIpOnLaunch": True}),
        )

    def test_s3_bucket_policy_allows_public_read(self):
        """Test case: bucket policy grants anonymous s3:GetObject (public read)."""

        self.template.has_resource_properties(
            "AWS::S3::BucketPolicy",
            Match.object_like(
                {
                    "PolicyDocument": Match.object_like(
                        {
                            "Statement": Match.array_with(
                                [
                                    Match.object_like(
                                        {
                                            "Action": "s3:GetObject",
                                            "Effect": "Allow",
                                        }
                                    )
                                ]
                            )
                        }
                    )
                }
            ),
        )

    def test_iam_task_role_wildcard_resources(self):
        """Test case: ECS task role grants actions on wildcard ("*") resources."""

        self.template.has_resource_properties(
            "AWS::IAM::Role",
            Match.object_like(
                {
                    "Policies": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "PolicyName": "GenericECSTask",
                                    "PolicyDocument": Match.object_like(
                                        {
                                            "Statement": Match.array_with(
                                                [
                                                    Match.object_like(
                                                        {
                                                            "Effect": "Allow",
                                                            "Resource": "*",
                                                        }
                                                    )
                                                ]
                                            )
                                        }
                                    ),
                                }
                            )
                        ]
                    )
                }
            ),
        )

    def test_ecs_service_execute_command_enabled(self):
        """Test case: ECS service has enable_execute_command turned on."""

        self.template.has_resource_properties(
            "AWS::ECS::Service",
            Match.object_like({"EnableExecuteCommand": True}),
        )

    def test_expected_vulnerable_resource_counts(self):
        """Test case: the stack synthesizes the expected single vulnerable resources."""

        self.template.resource_count_is("AWS::S3::Bucket", 1)
        self.template.resource_count_is("AWS::RDS::DBInstance", 1)
        self.template.resource_count_is("AWS::ECS::Service", 1)
        self.template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
