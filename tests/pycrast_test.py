import sys
sys.path.append('../')

from pycrast.pycrast import *


class TestSanitize:
	def test_normal(self):
		"""Tests that normal text is preserved"""
		assert sanitize('test') == 'test'
		assert sanitize('foo_bar') == 'foo_bar'

	def test_spaces(self):
		assert sanitize('Lots of spaces in this sentence') == 'Lotsofspacesinthissentence'

	def test_unicode(self):
		assert sanitize(u'Test\xE2 Post Please Ignore') == "TestPostPleaseIgnore"

def test_saveload(tmpdir):
	test_apps = ["test.exe", "cool.test.net"]
	test_data = {app: Application(app) for app in test_apps}
	test_file = str(tmpdir.join('test.dat'))

	pickle_apps(filename=test_file, obj=test_data)
	new_test_data = load_pickle(filename=test_file)
	assert test_data == new_test_data