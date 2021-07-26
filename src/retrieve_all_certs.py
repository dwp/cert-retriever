import logging
import os
import socket
import sys

import boto3

import re

region = os.environ.get("REGION", "eu-west-2")
log_level = os.environ.get("LOG_LEVEL", "INFO")
environment = os.environ.get("ENVIRONMENT", "NOT_SET")
application = os.environ.get("APPLICATION", "NOT_SET")

dest_folder = os.environ["CERTS_DESTINATION_FOLDER"]
source_prefixes = os.environ["ADDITIONAL_CERTS_PREFIXES"].split(",")
bucket = os.environ["ADDITIONAL_CERTS_BUCKET"]


def setup_logging(logger_level, env, app):
    the_logger = logging.getLogger()
    for old_handler in the_logger.handlers:
        the_logger.removeHandler(old_handler)

    new_handler = logging.StreamHandler(sys.stdout)

    hostname = socket.gethostname()

    json_format = (
        '{ "timestamp": "%(asctime)s", "log_level": "%(levelname)s", "message": "%(message)s", '
        f'"environment": "{env}", "application": "{app}", '
        f'"module": "%(module)s", "process": "%(process)s", '
        f'"thread": "[%(thread)s]", "hostname": "{hostname}" }} '
    )

    new_handler.setFormatter(logging.Formatter(json_format))
    the_logger.addHandler(new_handler)
    new_level = logging.getLevelName(logger_level.upper())
    the_logger.setLevel(new_level)

    if the_logger.isEnabledFor(logging.DEBUG):
        boto3.set_stream_logger()
        the_logger.debug(f'Using boto3", "version": "{boto3.__version__}')

    return the_logger


logger = setup_logging(log_level, environment, application)


def get_cert_arns(acm_client):
    logger.info("Getting all certs from ACM...")
    return [
        {"arn": i["CertificateArn"], "domain": i["DomainName"]}
        for i in acm_client.list_certificates().get("CertificateSummaryList", [])
    ]


def get_cert_data(acm_client, arn):
    logger.info(f"Getting cert data for ARN: {arn}")
    return acm_client.get_certificate(CertificateArn=arn).get("Certificate")


def save_cert(domain_name, cert_data):
    logger.info(f"Attempting to write cert file with name: {domain_name}.pem")

    try:
        with open(os.path.join(dest_folder, f"{domain_name}.pem"), "w") as file:
            file.write(cert_data)

    except Exception as e:
        logger.error(e)
        return False

    return True


def get_additional_certs_keys(s3_client, bucket, prefixes: list):
    response = s3_client.list_objects(Bucket=bucket)
    certs_keys = []
    for el in prefixes:
        certs_keys = certs_keys + [
            {
                "key": i["Key"],
                "cert_name": i["Key"].replace(".pem", "").replace("/", "_"),
            }
            for i in response["Contents"]
            if re.match(el + "\/.*\.pem", i["Key"])
        ]
    return certs_keys


def get_additional_cert_data(s3_resource, key, bucket):
    bucket = s3_resource.Bucket(bucket)
    ob = bucket.Object(key)
    return ob.get()["Body"].read()


def main():
    acm = boto3.client("acm", region_name=region)
    s3_client = boto3.client("s3", region_name=region)
    s3_resource = boto3.resource("s3")
    cert_list = get_cert_arns(acm)

    for cert in cert_list:
        domain = cert.get("domain")
        data = get_cert_data(acm, cert.get("arn", ""))

        successful = save_cert(domain, data)

        if not successful:
            logger.error(f"Failed to save cert with domain: {domain}")
        else:
            logger.info(f"Successfully saved cert with domain: {domain}")

    cert_list_additional = get_additional_certs_keys(bucket, source_prefixes, s3_client)

    for cert in cert_list_additional:
        domain = cert.get("cert_name")
        key = cert.get("key")
        data = get_additional_cert_data(key, bucket, s3_resource)

        successful = save_cert(domain, data)

        if not successful:
            logger.error(f"Failed to save cert with domain: {domain}")
        else:
            logger.info(f"Successfully saved cert with domain: {domain}")
    logger.info(f"Finished fetching and saving certs")


if __name__ == "__main__":
    main()
