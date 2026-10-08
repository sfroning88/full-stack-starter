"""
Author: Sean Froning
Created Date: 10.7.2026
Operations for MyClass
"""

from ..core import logging
from ..models import MyClass

logger = logging.get_logger(__name__)


class MyService:
    """Print contents of my message"""

    @staticmethod
    def print_message(my_class: MyClass) -> None:
        print(my_class.message)
