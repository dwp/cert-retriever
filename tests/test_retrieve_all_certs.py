import os
import re
import unittest
from unittest.mock import MagicMock

import boto3
from moto import mock_acm

dest_folder = os.path.join(os.getcwd(), "tests")
os.environ["CERTS_DESTINATION_FOLDER"] = dest_folder

from src import retrieve_all_certs

retrieve_all_certs.logger = MagicMock()

cert_pattern = re.compile(r"-+BEGIN CERTIFICATE-+[\n\s\S]+-+END CERTIFICATE-+\n")


@mock_acm
class RetrieveAllCertsTests(unittest.TestCase):

    def setUp(self):
        self.acm = boto3.client("acm", region_name="eu-west-2")

        self.test_arn = self.acm.request_certificate(DomainName="test.com")["CertificateArn"]
        self.acm.request_certificate(DomainName="test.test.com")
        self.acm.request_certificate(DomainName="test2.test.com")

        self.test_cert = self.acm.get_certificate(CertificateArn=self.test_arn)["Certificate"]

        self.filepaths_to_remove = []

    def tearDown(self):
        for filepath in self.filepaths_to_remove:
            os.remove(filepath)

    def test_get_cert_arns(self):
        certs = retrieve_all_certs.get_cert_arns(self.acm)

        for cert in certs:
            self.assertIn("arn:aws:acm:eu-west-2:123456789012:certificate/", cert["arn"])

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

    def test_main(self):
        retrieve_all_certs.main()

        for filename in ["test.com", "test.test.com", "test2.test.com"]:
            filepath = os.path.join(dest_folder, f"{filename}.pem")
            self.filepaths_to_remove.append(filepath)

            self.assertTrue(os.path.isfile(filepath))


if __name__ == '__main__':
    unittest.main()
