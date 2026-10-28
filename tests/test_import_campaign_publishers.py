import json
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.import_campaign_publishers import (
    CreatorIQ,
    find_record,
    import_publishers,
    load_publisher_ids,
    main,
    redact,
)


def write_csv(directory: str, text: str) -> Path:
    path = Path(directory) / "publishers.csv"
    path.write_text(text, encoding="utf-8")
    return path


class LoadPublisherIdsTest(unittest.TestCase):
    def test_reads_publisher_id_column(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_csv(directory, "PublisherId\n34949708\n34949709\n")
            self.assertEqual(load_publisher_ids(path), [34949708, 34949709])

    def test_accepts_spaced_header_and_skips_duplicates(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_csv(directory, "Publisher Id,Name\n10,A\n10,A\n\n11,B\n")
            self.assertEqual(load_publisher_ids(path), [10, 11])

    def test_rejects_missing_column(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_csv(directory, "Name\nAda\n")
            with self.assertRaises(SystemExit):
                load_publisher_ids(path)

    def test_rejects_non_numeric_id(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_csv(directory, "PublisherId\nabc\n")
            with self.assertRaises(SystemExit):
                load_publisher_ids(path)


class RedactTest(unittest.TestCase):
    def test_redacts_secret(self) -> None:
        self.assertEqual(redact("key abc failed", "abc"), "key [redacted] failed")


class ImportPublishersTest(unittest.TestCase):
    def test_dry_run_does_not_assign(self) -> None:
        client = CreatorIQ("secret")
        calls: list[str] = []

        def request(method: str, path: str, body=None):
            calls.append(method)
            if path.endswith("/campaign/2991466"):
                return 200, {"Campaign": {"CampaignId": 2991466, "CampaignName": "Test Campaign"}}
            return 404, {"NotFoundHttpException": {"message": "Publisher with id `10` not found in campaign"}}

        with patch.object(client, "request", side_effect=request):
            name, results = import_publishers(client, 2991466, [10], "Accepted", dry_run=True)

        self.assertEqual(name, "Test Campaign")
        self.assertEqual(results, [{"publisher_id": 10, "result": "would_add", "detail": "status=Accepted"}])
        self.assertNotIn("POST", calls)

    def test_skips_publisher_already_on_campaign(self) -> None:
        client = CreatorIQ("secret")

        def request(method: str, path: str, body=None):
            if "publishers" in path:
                return 200, {
                    "CampaignPublisher": {
                        "PublisherId": 10,
                        "PublisherName": "Maura Coakley",
                        "Status": "Accepted",
                    }
                }
            return 200, {"Campaign": {"CampaignName": "Test Campaign"}}

        with patch.object(client, "request", side_effect=request):
            _, results = import_publishers(client, 2991466, [10], "Accepted")

        self.assertEqual(results[0]["result"], "already_on_campaign")
        self.assertIn("Maura Coakley", results[0]["detail"])

    def test_adds_and_verifies_publisher(self) -> None:
        client = CreatorIQ("secret")
        seen_post = {"done": False}

        def request(method: str, path: str, body=None):
            if method == "POST":
                seen_post["done"] = True
                self.assertEqual(body, {"publisherId": 10, "status": "Accepted"})
                return 201, {
                    "CampaignPublisher": {
                        "CampaignId": 2991466,
                        "PublisherId": 10,
                        "ErrorMessage": None,
                    }
                }
            if "publishers" in path:
                if seen_post["done"]:
                    return 200, {"PublisherId": 10, "PublisherName": "Ada", "Status": "Accepted"}
                return 404, {"message": "not found"}
            return 200, {"Campaign": {"CampaignName": "Test Campaign"}}

        with patch.object(client, "request", side_effect=request):
            _, results = import_publishers(client, 2991466, [10], "Accepted")

        self.assertEqual(results[0]["result"], "added")
        self.assertIn("Ada", results[0]["detail"])

    def test_failed_assignment_is_reported(self) -> None:
        client = CreatorIQ("secret")

        def request(method: str, path: str, body=None):
            if method == "POST":
                return 400, {"message": "publisher secret is invalid"}
            if "publishers" in path:
                return 404, {"message": "not found"}
            return 200, {"Campaign": {"CampaignName": "Test Campaign"}}

        with patch.object(client, "request", side_effect=request):
            _, results = import_publishers(client, 2991466, [10], "Invited")

        self.assertEqual(results[0]["result"], "failed")
        self.assertIn("[redacted]", results[0]["detail"])
        self.assertNotIn("secret", results[0]["detail"])


class RequestTest(unittest.TestCase):
    def test_http_error_body_is_parsed(self) -> None:
        client = CreatorIQ("secret")
        payload = json.dumps({"message": "nope"}).encode()

        def raise_http(*args, **kwargs):
            raise HTTPError(
                url="https://apis.creatoriq.com/x",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=BytesIO(payload),
            )

        with patch("scripts.import_campaign_publishers.urllib.request.urlopen", side_effect=raise_http):
            code, body = client.request("GET", "/crm/v1/api/campaign/1")

        self.assertEqual(code, 404)
        self.assertEqual(body["message"], "nope")


class MainTest(unittest.TestCase):
    def test_missing_key_exits(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_csv(directory, "PublisherId\n10\n")
            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(SystemExit):
                    main(["--campaign", "1", "--csv", str(path), "--dry-run"])

    def test_find_record_nested(self) -> None:
        payload = {"CampaignPublisher": {"PublisherId": 10, "Status": "Accepted"}}
        self.assertEqual(find_record(payload, 10)["Status"], "Accepted")
        self.assertIsNone(find_record(payload, 11))


if __name__ == "__main__":
    unittest.main()
