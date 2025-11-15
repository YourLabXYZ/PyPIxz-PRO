import logging
logger = logging.getLogger("main")

import yaml
from logging.config import dictConfig

from src.pypixz_pro import *

with open(f"logging.yaml" , "r") as file:
    config_file = yaml.safe_load(file)
    dictConfig(config_file)

logger.setLevel(logging.DEBUG)

install_requirements("requirements-test.txt", "main")

