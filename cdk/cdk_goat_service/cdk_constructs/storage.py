"""Storage CDK construct module."""

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StorageConstruct(Construct):
    """Storage CDK construct class."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix=None,
    ):
        """Construct initialization."""
        super().__init__(scope, id)

        storage_bucket = s3.Bucket(
            self,
            "AppBucket",
            block_public_access=s3.BlockPublicAccess(
                block_public_policy=False,
                block_public_acls=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            public_read_access=True,
        )

        cdk.CfnOutput(self, "UploadsBucketName", value=storage_bucket.bucket_name)

        self.storage_bucket = storage_bucket
