import os
import re
import unittest
from unittest.mock import MagicMock
from mock import patch

import boto3
from moto import mock_acm
from moto import mock_s3

dest_folder = os.path.join(os.getcwd(), "tests")
os.environ["CERTS_DESTINATION_FOLDER"] = dest_folder


from src import retrieve_all_certs

retrieve_all_certs.logger = MagicMock()

cert_pattern = re.compile(r"-+BEGIN CERTIFICATE-+[\n\s\S]+-+END CERTIFICATE-+\n")

os.environ["ADDITIONAL_CERTS_PREFIXES"] = "prefixone,prefixtwo/folder"
os.environ["ADDITIONAL_CERTS_BUCKET"] = "ac-bucket"
certs_keys_expected = [
    {"key": "prefixone/abcd.pem", "cert_name": "prefixone_abcd"},
    {"key": "prefixone/abcd/abcd.pem", "cert_name": "prefixone_abcd_abcd"},
    {
        "key": "prefixtwo/folder/abcd/abcd.pem",
        "cert_name": "prefixtwo_folder_abcd_abcd",
    },
]

test_content = b"-----BEGIN (test) CERTIFICATE----- abcd -----END CERTIFICATE-----"


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
        source_prefixes = os.environ["ADDITIONAL_CERTS_PREFIXES"]
        self.source_prefixes = source_prefixes.split(",")
        self.bucket = os.environ["ADDITIONAL_CERTS_BUCKET"]
        try:
            self.s3_client.create_bucket(
                Bucket=self.bucket,
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )
        except:
            Exception

        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixone/abcd.pem", Body=test_content
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixtwo/folder/abcd/abcd.pem", Body=test_content
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="prefixone/abcd/abcd.pem", Body=test_content
        )
        self.s3_client.put_object(
            Bucket=self.bucket, Key="not/prefixone/abcd/abcd.pem", Body=test_content
        )

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

        actual = retrieve_all_certs.get_additional_certs_keys(
            self.s3_client, self.bucket, self.source_prefixes
        )
        self.assertEqual(certs_keys_expected, actual)

    def test_get_additional_cert_data(self):

        actual = retrieve_all_certs.get_additional_cert_data(
            self.s3_resource, certs_keys_expected[0]["key"], self.bucket
        )
        self.assertEqual(test_content, actual)

    @patch(
        "src.retrieve_all_certs.get_additional_certs_keys",
        return_value=certs_keys_expected,
    )
    @patch(
        "src.retrieve_all_certs.get_additional_cert_data",
        return_value=test_content,
    )
    def test_main(self, mock_get_additional_certs_keys, mock_get_additional_cert_data):

        retrieve_all_certs.main()

        for filename in [
            "test.com",
            "test.test.com",
            "test2.test.com",
            "prefixone_abcd",
            "prefixone_abcd_abcd",
            "prefixtwo_folder_abcd_abcd",
        ]:
            filepath = os.path.join(dest_folder, f"{filename}.pem")
            self.filepaths_to_remove.append(filepath)

            self.assertTrue(os.path.isfile(filepath))


if __name__ == "__main__":
    unittest.main()
