import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rzmetrics.settings")
