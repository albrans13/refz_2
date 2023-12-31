import os


class Config(object):
    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

    APP_ID = int(os.environ.get("APP_ID", 27114545))

    API_HASH = os.environ.get("API_HASH", "4d697dc98a6c882527aab3f72b25479d")
