import boto3
import dagster as dg
from dagster import ConfigurableResource
from pymongo import MongoClient


class MinioResource(ConfigurableResource):
    access_key: str
    secret_key: str
    endpoint_url: str
    region_name: str = "us-east-1"

    def get_client(self):
        """Return a boto3 S3 client for MinIO."""
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
        )


class MongoResource(ConfigurableResource):
    uri: str
    database: str

    def get_client(self) -> MongoClient:
        """Return a raw MongoDB client."""
        return MongoClient(self.uri)


minio_resource = MinioResource(
    access_key=dg.EnvVar("MINIO_ACCESS_KEY"),
    secret_key=dg.EnvVar("MINIO_SECRET_KEY"),
    endpoint_url=dg.EnvVar("MINIO_ENDPOINT_URL"))

mongodb_resource = MongoResource(uri=dg.EnvVar(
    "MONGO_URI"), database=dg.EnvVar("MONGO_DATABASE"))


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "minio": minio_resource,
            "mongo": mongodb_resource
        }
    )
