import os
import subprocess
from datetime import timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup
from dagster import MonthlyPartitionsDefinition, asset

SCRAPY_PROJECT_DIR = Path(__file__).parents[2] / "legora_scrapy"

partitions_def = MonthlyPartitionsDefinition(start_date="2025-01-01")


@asset(partitions_def=partitions_def, required_resource_keys={"minio", "mongo"})
def extract_decisions(context):
    """Scrape by monthly partition window."""
    partition_key = context.asset_partition_key_for_output()
    partition_dt = partitions_def.time_window_for_partition_key(partition_key)

    from_date = partition_dt.start.date()
    to_date = (partition_dt.end - timedelta(days=1)).date()

    scrapy_args = {}
    scrapy_args["from_date"] = from_date
    scrapy_args["to_date"] = to_date
    scrapy_args["partition_date"] = partition_key

    scrapy_settings = {"LOG_LEVEL": "INFO"}

    cmd = ["scrapy", "crawl", "decisions"]

    for k, v in scrapy_args.items():
        cmd += ["-a", f"{k}={v}"]

    for k, v in scrapy_settings.items():
        cmd += ["-s", f"{k}={v}"]

    context.log.info(f"Running: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd,
                            cwd=SCRAPY_PROJECT_DIR,
                            env=os.environ.copy(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            )

    for line in proc.stdout:
        line = line.strip()
        if line:
            context.log.info(line)

    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"Scrapy failed with exit code {proc.returncode}")


@asset(
    partitions_def=partitions_def,
    required_resource_keys={"minio", "mongo"},
    deps=["extract_decisions"],
)
def transform_decisions(context):
    """Transform decisions stored in MongoDB and MinIO into cleaned documents."""

    partition_key = context.asset_partition_key_for_output()

    mongo_client = context.resources.mongo.get_client()
    minio_client = context.resources.minio.get_client()

    mongo_db = mongo_client[context.resources.mongo.database]
    raw_collection = mongo_db["decisions_raw"]
    transformed_collection = mongo_db["decisions_transformed"]

    bucket = "legora"
    landing_prefix = Path("workplacerelations/landing_zone/full")
    output_prefix = Path("workplacerelations/processed")

    cursor = raw_collection.find(
        {"partition_date": partition_key}, no_cursor_timeout=True).batch_size(1000)

    try:
        for doc in cursor:
            decision_id = doc["_id"].strip()

            for f in doc.get("files", []):
                file_path = Path(f["path"])
                ext = file_path.suffix.lower().lstrip(".")

                landing_key = str(landing_prefix / file_path.name)
                identifier_name = f"{decision_id}.{ext}"
                new_key = str(output_prefix / identifier_name)

                if ext in ["pdf"]:
                    minio_client.copy_object(
                        CopySource={"Bucket": bucket, "Key": landing_key},
                        Bucket=bucket,
                        Key=new_key
                    )
                    file_hash = f["checksum"]
                elif ext in ["html"]:
                    obj = minio_client.get_object(
                        Bucket=bucket, Key=landing_key)
                    file_text = obj["Body"].read().decode("utf-8")
                    obj["Body"].close()

                    soup = BeautifulSoup(file_text, "html.parser")
                    content_div = soup.select_one("div.content")

                    if content_div:
                        html_content = str(content_div)
                        file_hash = sha256(
                            html_content.encode("utf-8")).hexdigest()
                    else:
                        context.log.warning(
                            f"No content div found for {file_path}, keeping raw HTML")
                        html_content = file_text
                        file_hash = f["checksum"]

                    minio_client.put_object(
                        Bucket=bucket,
                        Key=new_key,
                        Body=BytesIO(html_content.encode("utf-8")),
                        ContentType="text/html",
                    )
                else:
                    context.log.warning(
                        f"Skipping unknown file type: {file_path}")
                    continue

                transformed_doc = {
                    "_id": decision_id,
                    "partition_date": partition_key,
                    "link": doc["link"],
                    "date": doc["date"],
                    "ref_no": doc.get("ref_no"),
                    "parties": doc.get("parties"),
                    "file_path": new_key,
                    "file_hash": file_hash,
                    "file_ext": ext,
                }

                transformed_collection.update_one(
                    {"_id": decision_id, "partition_date": partition_key},
                    {"$set": transformed_doc},
                    upsert=True
                )

                context.log.info(f"Transformed {file_path} -> {new_key}")

    finally:
        cursor.close()
