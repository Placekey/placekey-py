"""
Placekey API client tests.

pytest -m"not slow" placekey/tests/test_api.py
"""

import unittest
import os
import pytest
from placekey.api import PlacekeyAPI


class TestAPI(unittest.TestCase):
    """
    Tests for api.py
    """

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.getenv('PLACEKEY_API_KEY')

    def setUp(self):
        if not self.api_key:
            self.fail('The PLACEKEY_API_KEY environment variable must be set to run tests.')

        self.pk_api = PlacekeyAPI(
            api_key=self.api_key, user_agent_comment="placekey-py-tests")

    def test_init(self):
        """
        Test __init__
        """
        # user agent handling
        pass

    def test_lookup_placekey(self):
        """
        test lookup_placekey
        """
        # lat long
        # other info
        # strict
        # invalid query
        pass

    @pytest.mark.slow
    def test_lookup_placekey_slow(self):
        """
        Longer running rate-limit test for lookup_placekey
        """
        pass

    def test_lookup_batch(self):
        """
        Test lookup_batch
        """
        # lat long
        # other info
        # strict
        pass

    def test_lookup_placekeys(self):
        """
        Test lookup_placekeys
        """

        #1. Query id handling
        #2. Error interpolation
        #3. invalid query
        # mixed query types

        pass

    @pytest.mark.slow
    def test_lookup_placekeys_slow(self):
        """
        Longer running rate-limit test for lookup_placekeys
        """
        pass
