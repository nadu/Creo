from contextlib import contextmanager
from functools import wraps
import os
import shutil
from os import error, listdir
from os.path import join, isdir, islink
import tempfile
import subprocess
import sys
import logging
import traceback
import signal

import chardet
import requests

LOG = logging.getLogger(__name__)

# set up BASE_EXCEPTION early - it's relied upon by other imports
# use ForgeError if we're on the client, so it can catch us
try:
	from forge import ForgeError
	BASE_EXCEPTION = ForgeError
except ImportError:
	BASE_EXCEPTION = Exception

from build import Build

class CouldNotLocate(BASE_EXCEPTION):
	pass

def task(function):
	Build.tasks[function.func_name] = function
	
	@wraps(function)
	def wrapper(*args, **kw):
		return function(*args, **kw)
	return wrapper
	
def predicate(function):
	Build.predicates[function.func_name] = function
	
	@wraps(function)
	def wrapper(*args, **kw):
		return function(*args, **kw)
	return wrapper
	
# modified os.walk() function from Python 2.4 standard library
def walk_with_depth(top, topdown=True, onerror=None, deeplevel=0): # fix 0
	"""Modified directory tree generator.

	For each directory in the directory tree rooted at top (including top
	itself, but excluding '.' and '..'), yields a 4-tuple

		dirpath, dirnames, filenames, deeplevel

	dirpath is a string, the path to the directory.  dirnames is a list of
	the names of the subdirectories in dirpath (excluding '.' and '..').
	filenames is a list of the names of the non-directory files in dirpath.
	Note that the names in the lists are just names, with no path components.
	To get a full path (which begins with top) to a file or directory in
	dirpath, do os.path.join(dirpath, name). 

	----------------------------------------------------------------------
	+ deeplevel is 0-based deep level from top directory
	----------------------------------------------------------------------
	...

	"""

	try:
		names = listdir(top)
	except error, err:
		if onerror is not None:
			onerror(err)
		return

	dirs, nondirs = [], []
	for name in names:
		if isdir(join(top, name)):
			dirs.append(name)
		else:
			nondirs.append(name)

	if topdown:
		yield top, dirs, nondirs, deeplevel # fix 1
	for name in dirs:
		path = join(top, name)
		if not islink(path):
			for x in walk_with_depth(path, topdown, onerror, deeplevel+1): # fix 2
				yield x
	if not topdown:
		yield top, dirs, nondirs, deeplevel # fix 3


@contextmanager
def cd(target_dir):
	'Change directory to :param:`target_dir` as a context manager - i.e. rip off Fabric'
	old_dir = os.getcwd()
	try:
		os.chdir(target_dir)
		yield target_dir
	finally:
		os.chdir(old_dir)

@contextmanager
def temp_file():
	'Return a path to save a temporary file to and delete afterwards'
	file = tempfile.mkstemp()
	try:
		os.close(file[0])
		os.remove(file[1])
		yield file[1]
	finally:
		if os.path.isfile(file[1]):
			os.remove(file[1])
			
@contextmanager
def temp_dir():
	'Return a path to a temporary directory and delete afterwards'
	dir = tempfile.mkdtemp()
	try:
		yield dir
	finally:
		shutil.rmtree(dir)

def read_file_as_str(filename):
	with open(filename, 'rb') as in_file:
		file_contents = in_file.read()

	try:
		unicode_res = file_contents.decode('utf8', errors='strict')
	except UnicodeDecodeError:
		char_result = chardet.detect(file_contents)
		encoding = char_result.get('encoding', 'utf8')
		encoding = 'utf8' if encoding is None else encoding
		unicode_res = file_contents.decode(encoding)
	return unicode_res

# TODO: this is duplicated in build tools, we should figure out a way to share
# the code between generate_dynamic and build tools sensibly
class PopenWithoutNewConsole(subprocess.Popen):
	"""Wrapper around Popen that adds the appropriate options to prevent launching
	a new console window everytime we want to launch a subprocess.
	"""
	_old_popen = subprocess.Popen

	def __init__(self, *args, **kwargs):
		if sys.platform.startswith("win") and 'startupinfo' not in kwargs:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			startupinfo.wShowWindow = subprocess.SW_HIDE
			kwargs['startupinfo'] = startupinfo

		self._old_popen.__init__(self, *args, **kwargs)


def expand_relative_path(build, *possibly_relative_path):
	"""Expands a path relative to the original working directory a build started in.

	Example usage:

	>> build.orig_wd
	'/home/monk/my-app'

	>> lib.expand_relative_path(build, '.template/lib', 'apksigner.jar')
	'/home/monk/my-app/.template/lib/apksigner.jar'

	>> lib.expand_relative_path(build, '/absolute/path/to/stuff')
	'/absolute/path/to/stuff'

	>> lib.expand_relative_path(build, '../release.keystore')
	'/home/release.keystore'
	"""
	return os.path.normpath(os.path.join(build.orig_wd, *possibly_relative_path))


def ask_multichoice(question_text, choices, radio=True):
	"""Ask a multichoice question and block until we get a response"""
	while True:
		field_name = 'answer'
		call = current_call()

		event_id = call.emit('question', schema={
			'title': question_text,
			'properties': {
				field_name: {
					'type': 'string',
					'enum': choices,
					'title': 'Choice',
					'_radio': radio,
				}
			}
		})

		response = call.wait_for_response(event_id)
		
		if response.get('data') is None:
			raise BASE_EXCEPTION("User aborted")
		response_data = response['data']

		if field_name not in response_data:
			LOG.warning("Invalid response, expected field: %s" % field_name)
			continue
		answer = response_data[field_name]

		try:
			choice = choices.index(answer) + 1
		except ValueError:
			LOG.debug("User gave invalid response")
			continue
		return choice


class ProgressBar(object):
	"""Helper context manager to emit progress events. e.g.

	with ProgressBar('Downloading Android SDK'):
		time.sleep('2')
		bar.progress(0.25) # 25% complete
		time.sleep('2')
		bar.progress(0.5) # 50% complete

	# 100% complete if finishes without exception

	*N.B* any logging occuring during the progress bar will mess up
	how it looks in the commandline, might be able to resolve this later
	by erasing the progress bar, printing the log output then printing the progress bar.
	"""
	def __init__(self, message):
		self._message = message
		self._call = current_call()

	def __enter__(self):
		self._call.emit('progressStart', message=self._message)
		return self

	def progress(self, fraction):
		self._call.emit('progress', fraction=fraction, message=self._message)

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type is not None:
			self.progress(1)
		self._call.emit('progressEnd', message=self._message)

def import_async():
	'If in client-side environment, import async from forge. Mock, otherwise'
	try:
		from forge import async
	except ImportError:
		import mock
		async = mock.Mock()
	return async

def current_call():
	return import_async().current_call()

def download_with_progress_bar(progress_bar_title, url, destination_path):
	"""Download something from a given URL, emitting progress events if possible
	"""
	download_response = requests.get(url)
	content_length = download_response.headers.get('content-length')

	with ProgressBar(progress_bar_title) as bar:
		with open(destination_path, 'wb') as destination_file:
			bytes_written = 0
			for chunk in download_response.iter_content(chunk_size=102400):
				if content_length:
					content_length = int(content_length)
					destination_file.write(chunk)
					bytes_written += len(chunk)
					fraction_complete = float(bytes_written) / content_length
					bar.progress(fraction_complete)


def set_dotted_attribute(build, attribute_name, value):
	"""Save a local_config value given in dotted form to the local_config.json for the current build.

	Example use::
		set_dotted_attribute(build, 'android.profiles.DEFAULT.sdk', '/opt/android-sdk-linux')
	"""
	# TODO: would be good to not have to import the build_config module here, maybe emit an event instead?
	from forge import build_config

	LOG.info('Saving %s as %s in local_config.json' % (value, attribute_name))
	with cd(build.orig_wd):
		local_config = build_config.load_local()
		current_level = local_config
		crumbs = attribute_name.split('.')
		for k in crumbs[:-1]:
			if k not in current_level:
				current_level[k] = {}
			current_level = current_level[k]
		current_level[crumbs[-1]] = value

		build_config.save_local(local_config)

def progressive_kill(pid):
	if sys.platform.startswith("win"):
		commands_to_try = ['TASKKILL /PID {pid}', 'TASKKILL /F /PID {pid}']
		with open(os.devnull) as devnull:
			for command in commands_to_try:
				kill_proc = subprocess.Popen(command.format(pid=pid), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				out = kill_proc.communicate()[0]
				if kill_proc.poll() == 0:
					LOG.debug("{command} succeeded".format(command=command))
					return
				else:
					LOG.debug("{command} failed".format(command=command))
					LOG.debug(out)

	else:
		signals_to_try = ['SIGINT', 'SIGTERM', 'SIGKILL']
		
		for signal_name in signals_to_try:
			signal_num = getattr(signal, signal_name)
			try:
				os.kill(pid, signal_num)
				LOG.debug("{signal_name} succeeded".format(signal_name=signal_name))
				return
			except Exception as e:
				LOG.debug("{signal_name} failed".format(signal_name=signal_name))
				LOG.debug(traceback.format_exc(e))
