from os import path
import os
import logging

from lib import task

LOG = logging.getLogger(__name__)

@task
def run_chrome(build):
	msg = """Currently it is not possible to launch a Chrome extension via this interface.
The required steps are:

	1) Go to chrome:extensions in the Chrome browser
	2) Make sure "developer mode" is on (top right corner)')
	3) Use "Load unpacked extension" and browse to {cwd}/development/chrome""".format(cwd=path.abspath(os.getcwd()))

	LOG.info(msg)

@task
def package_chrome(build):
	msg = """Currently it is not possible to package a Chrome extension via this interface.
The required steps are:

	1) Go to chrome:extensions in the Chrome browser
	2) Make sure "developer mode" is on (top right corner)')
	3) Use "Load unpacked extension" and browse to {cwd}/development/chrome
	4) Use the "pack extension" action

More information on packaging Chrome extensions can be found here:
	http://code.google.com/chrome/extensions/packaging.html
	""".format(cwd=path.abspath(os.getcwd()))

	LOG.info(msg)
