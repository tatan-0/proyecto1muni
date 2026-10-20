import os
import subprocess
import sys
import unittest


class SettingsEnvironmentTests(unittest.TestCase):
    def run_settings_import(self, **overrides):
        environment = os.environ.copy()
        keys = (
            "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS", "DB_ENGINE",
            "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT",
        )
        for key in keys:
            environment.pop(key, None)
        environment.update(overrides)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import config.settings; print(config.settings.DATABASES['default']['ENGINE']); "
                "print(config.settings.STORAGES['staticfiles']['BACKEND']); "
                "print(config.settings.MIDDLEWARE); "
                "print(getattr(config.settings, 'SECURE_PROXY_SSL_HEADER', None)); "
                "print(config.settings.SECURE_REDIRECT_EXEMPT)",
            ],
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

    def test_production_settings_load_with_proxy_configuration(self):
        result = self.run_settings_import(
            DJANGO_DEBUG="False",
            DJANGO_SECRET_KEY="test-only-secret-long-enough-for-settings-import",
            DJANGO_ALLOWED_HOSTS="sgr.example.cl",
            DB_ENGINE="mysql",
            DB_NAME="sgr_test",
            DB_USER="sgr_user",
            DB_PASSWORD="test-only-password",
            DB_HOST="db.example.test",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HTTP_X_FORWARDED_PROTO", result.stdout)
        self.assertIn("health/", result.stdout)

    def test_production_settings_reject_missing_or_sqlite_database_engine(self):
        for engine in (None, "sqlite"):
            with self.subTest(engine=engine):
                overrides = {
                    "DJANGO_DEBUG": "False",
                    "DJANGO_SECRET_KEY": "test-only-secret-long-enough-for-settings-import",
                    "DJANGO_ALLOWED_HOSTS": "sgr.example.cl",
                }
                if engine is not None:
                    overrides["DB_ENGINE"] = engine
                result = self.run_settings_import(**overrides)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DB_ENGINE=mysql", result.stderr)

    def test_mysql_settings_reject_missing_connection_variables(self):
        result = self.run_settings_import(DB_ENGINE="mysql")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DB_HOST", result.stderr)

    def test_static_files_use_compressed_manifest_storage_and_whitenoise(self):
        result = self.run_settings_import(DJANGO_DEBUG="True")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("whitenoise.storage.CompressedManifestStaticFilesStorage", result.stdout)
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", result.stdout)

    def test_development_settings_use_sqlite_by_default(self):
        result = self.run_settings_import(DJANGO_DEBUG="True")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("django.db.backends.sqlite3", result.stdout)

if __name__ == "__main__":
    unittest.main()
