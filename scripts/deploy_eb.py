"""Upload and deploy the private source bundle using the existing AWS setup."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

import boto3

from build_eb_bundle import ROOT, build

APPLICATION = "regen-organics-analytics-app"
ENVIRONMENT = "regen-app-test"
REGION = "us-east-1"


def deploy(profile: str) -> None:
    session = boto3.Session(profile_name=profile, region_name=REGION)
    eb = session.client("elasticbeanstalk")
    label = "regen-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bucket = eb.create_storage_location()["S3Bucket"]
    key = f"{APPLICATION}/{label}.zip"
    with tempfile.TemporaryDirectory(prefix="regen-eb-") as directory:
        bundle = Path(directory) / "app.zip"
        build(bundle)
        session.client("s3").upload_file(
            str(bundle), bucket, key, ExtraArgs={"ServerSideEncryption": "AES256"}
        )
    eb.create_application_version(
        ApplicationName=APPLICATION,
        VersionLabel=label,
        SourceBundle={"S3Bucket": bucket, "S3Key": key},
        Description="Web, Celery, Redis and Nginx; verified runtime dependencies",
        Process=True,
    )
    environments = eb.describe_environments(
        ApplicationName=APPLICATION, EnvironmentNames=[ENVIRONMENT]
    )["Environments"]
    if environments:
        result = eb.update_environment(EnvironmentName=ENVIRONMENT, VersionLabel=label)
    else:
        stack = next(
            s for s in eb.list_available_solution_stacks()["SolutionStacks"]
            if "Amazon Linux 2023" in s and s.endswith(" running Docker")
        )
        options = json.loads((ROOT / "deploy/environment-options.json").read_text())
        result = eb.create_environment(
            ApplicationName=APPLICATION, EnvironmentName=ENVIRONMENT,
            SolutionStackName=stack, VersionLabel=label, OptionSettings=options,
        )
    print(json.dumps({k: result.get(k) for k in (
        "EnvironmentName", "EnvironmentId", "Status", "VersionLabel", "CNAME"
    )}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="eb-cli")
    deploy(parser.parse_args().profile)
