from stargate.test_utils import Fixture
from nose.tools import *
from pyramid import testing
from unittest import TestCase


class TestMe(TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_config(self):
        self.assertTrue(self.config.settings is None)
