import os
import re
import unittest
from unittest.mock import MagicMock

import boto3
from moto import mock_acm
from moto import mock_s3

dest_folder = os.path.join(os.getcwd(), "tests")
os.environ["CERTS_DESTINATION_FOLDER"] = dest_folder
os.environ["ADDITIONAL_CERTS_PREFIXES"] = "prefixone,prefixtwo"
os.environ["ADDITIONAL_CERTS_BUCKET"] = "ac_bucket"


from src import retrieve_all_certs

retrieve_all_certs.logger = MagicMock()

cert_pattern = re.compile(r"-+BEGIN CERTIFICATE-+[\n\s\S]+-+END CERTIFICATE-+\n")


@mock_acm
@mock_s3
class RetrieveAllCertsTests(unittest.TestCase):
    def setUp(self):

        self.acm = boto3.client("acm", region_name="eu-west-2")
        self.s3_client = boto3.client("s3", region_name="eu-west-2")
        self.s3_resource = boto3.resource("s3", region_name="eu-west-2")

        self.test_arn = self.acm.request_certificate(DomainName="test.com")[
            "CertificateArn"
        ]
        self.acm.request_certificate(DomainName="test.test.com")
        self.acm.request_certificate(DomainName="test2.test.com")

        self.test_cert = self.acm.get_certificate(CertificateArn=self.test_arn)[
            "Certificate"
        ]

        self.filepaths_to_remove = []
        self.source_prefixes = os.environ["ADDITIONAL_CERTS_PREFIXES"].split(",")
        self.bucket = os.environ["ADDITIONAL_CERTS_BUCKET"]

    def tearDown(self):
        for filepath in self.filepaths_to_remove:
            os.remove(filepath)

    def test_get_cert_arns(self):
        certs = retrieve_all_certs.get_cert_arns(self.acm)

        for cert in certs:
            self.assertIn(
                "arn:aws:acm:eu-west-2:123456789012:certificate/", cert["arn"]
            )

        self.assertEqual(certs[0]["domain"], "test.com")

    def test_get_cert_data(self):
        cert = retrieve_all_certs.get_cert_data(self.acm, self.test_arn)
        self.assertTrue(cert_pattern.fullmatch(cert))

    def test_save_cert(self):
        domain_name = "test.domain.com"

        was_successful = retrieve_all_certs.save_cert(domain_name, self.test_cert)

        self.assertTrue(was_successful)

        filepath = os.path.join(dest_folder, f"{domain_name}.pem")
        self.filepaths_to_remove.append(filepath)

        with open(filepath, "r") as file:
            self.assertEqual(file.read(), self.test_cert)

    def test_get_additional_certs_keys(self):

        self.s3_client.create_bucket(
            Bucket=self.bucket,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        some_data = b"-----BEGIN (test) CERTIFICATE----- abcd -----END CERTIFICATE-----"
        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixone/abcd.pem", Body=some_data
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixtwo/abcd/abcd.pem", Body=some_data
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixone/abcd/abcd.pem", Body=some_data
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="not/prefixone/abcd/abcd.pem", Body=some_data
        )
        expected = [
            {"key": "prefixone/abcd.pem", "cert_name": "prefixone_abcd"},
            {"key": "prefixone/abcd/abcd.pem", "cert_name": "prefixone_abcd_abcd"},
            {"key": "prefixtwo/abcd/abcd.pem", "cert_name": "prefixtwo_abcd_abcd"},
        ]
        actual = retrieve_all_certs.get_additional_certs_keys(
            self.s3_client, self.bucket, self.source_prefixes
        )
        self.assertEqual(expected, actual)

    def test_main(self):
        retrieve_all_certs.main()

        for filename in ["test.com", "test.test.com", "test2.test.com"]:
            filepath = os.path.join(dest_folder, f"{filename}.pem")
            self.filepaths_to_remove.append(filepath)

            self.assertTrue(os.path.isfile(filepath))


if __name__ == "__main__":
    unittest.main()
