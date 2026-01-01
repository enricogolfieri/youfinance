"""Test for Financial Modeling Prep CEO fetching"""

import sys
import os

"""Load the parent directory to import modules"""
# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import logger

logger.init("TEST")


def unit_test(name):
    """Decorator for unit tests"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Running unit test: {name}")
            result = func(*args, **kwargs)
            if result:
                logger.info(f"Unit test '{name}' passed")
            else:
                logger.error(f"Unit test '{name}' failed")
            if not result:
                print(f"❌ Unit test '{name}' failed")
            else:
                print(f"✅ Unit test '{name}' passed")

        return wrapper

    return decorator
