import os
import subprocess
import sys
import unittest


class SettingsEnvironmentTests(unittest.TestCase):
    def run_settings_import(self, **overrides):
        environment = os.environ.copy()
        for key in ("DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS", "DB_ENGINE"):
            environment.pop(key, None)
        environment.update(overrides)
        return subprocess.run(
            [sys.executable, "-c", "import config.settings; print(config.settings.DATABASES['default']['ENGINE'])"],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

    def test_production_settings_reject_missing_secret_and_hosts(self):
        missing_secret = self.run_settings_import(
            DJANGO_DEBUG="False",
            DJANGO_ALLOWED_HOSTS="sgr.example.cl",
        )
        self.assertNotEqual(missing_secret.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", missing_secret.stderr)

        missing_hosts = self.run_settings_import(
            DJANGO_DEBUG="False",
            DJANGO_SECRET_KEY="test-only-secret",
        )
        self.assertNotEqual(missing_hosts.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", missing_hosts.stderr)

    def test_development_settings_use_sqlite_by_default(self):
        result = self.run_settings_import(DJANGO_DEBUG="True")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("django.db.backends.sqlite3", result.stdout)


if __name__ == "__main__":
    unittest.main()
