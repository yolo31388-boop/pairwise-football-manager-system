"""Pytest compatibility shim.

The shipped test class uses ``self.assertIsNotNone`` without subclassing
``unittest.TestCase``. Rather than editing the test files, attach the
standard unittest assertion methods to plain pytest test classes at
collection time. This is a no-op for classes that already have them.
"""

import unittest


def pytest_collection_modifyitems(items):
    for item in items:
        cls = getattr(item, "cls", None)
        if cls is None or issubclass(cls, unittest.TestCase):
            continue
        for name in dir(unittest.TestCase):
            if name.startswith("assert") and not hasattr(cls, name):
                setattr(cls, name, getattr(unittest.TestCase, name))
