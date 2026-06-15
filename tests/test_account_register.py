import tempfile
import unittest
from pathlib import Path

from agent.account_register import AccountRegister


class AccountRegisterTests(unittest.TestCase):
    def test_upsert_records_non_secret_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            register = AccountRegister(Path(tmp))
            record = register.upsert(
                service="GitHub",
                email="josephfredrickson@live.com",
                purpose="public-good contributions",
                login_url="https://github.com/Joe-You-Know",
                notes="No token stored here.",
            )
            self.assertIn("not stored in repo", record["password_storage"])
            data = register.list_accounts()
            self.assertEqual(data["accounts"][0]["service"], "GitHub")
            self.assertNotIn("password", data["accounts"][0])


if __name__ == "__main__":
    unittest.main()
