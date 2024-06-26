import os
import sys
from aiohttp.web import run_app
from app.web.app import setup_app

if len(sys.argv)>1:
    if sys.argv[1] == "admin":
        MODE = "admin"
else:
    MODE = "bot"


config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_local.yml")
if not os.path.isfile(config_path):
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.yml")

if __name__ == "__main__":
    run_app(
        setup_app(config_path=config_path, mode=MODE)
    )