# XXX should consolidate this with lib
import logging
from os import path
import subprocess
import StringIO
import hashlib
import json
import sys
import os
import stat
import time
import threading

import lib

from genshi.template import NewTextTemplate

LOG = logging.getLogger(__name__)

class ShellError(lib.BASE_EXCEPTION):
	def __init__(self, message, output):
		self.message = message
		self.output = output

	def __str__(self):
		return "%s: %s" % (self.message, self.output)

# # # # # # # # # # # # # # # # # # # 
#
# Data transform
# TODO XPath or similar?
#
# # # # # # # # # # # # # # # # # # # 
def transform(data, node_steps, fn):
	'''Mutate an arbitrary nested dictionary/array combination with the given function.
	
	``node_steps`` is dot-separated instructions on how to arrive at the data node
	which needs changing::
	
		array_name.[]
		dictionary.key_name
		dictionary.*			   // all keys in a dictionary

	:param data: a nested dictionary / array combination
	:type data: ``dict``
	:param node_steps: dot-separated data path, e.g. my_dict.[].*.target_key
	:param fn: mutating function - will be passed the data found at the end
		``node_steps``, and should return the desired new value
	'''
	obj = data.copy()
	list(_handle_all(obj, node_steps.split('.'), fn))
	return obj

def _yield_plain(obj, name):
	'If obj is a dictionary, yield an attribute'
	if hasattr(obj, '__contains__') and name in obj:
		yield obj[name]
def _yield_array(obj):
	'Yield all elements of an array'
	assert hasattr(obj, '__iter__'), 'Expecting an array, got %s' % obj
	for thing in obj:
		yield thing
def _yield_asterisk(obj):
	'Yield all values in a dictionary'
	if hasattr(obj, 'iteritems'):
		for _, value in obj.iteritems():
			yield value
def _yield_any(obj, name):
	'Yield a value, or array or dictionary values'
	if name == '*':
		return _yield_asterisk(obj)
	elif name == '[]':
		return _yield_array(obj)
	else:
		return _yield_plain(obj, name)

def recurse_dict(dictionary, fn):
	'''
	if the property isn't a string, recurse till it is
	'''
	for key, value in dictionary.iteritems():
		if hasattr(value, 'iteritems'):
			recurse_dict(value, fn)
		else:
			dictionary[key] = fn(value)

def _handle_all(obj, steps, fn):
	if len(steps) > 1:
		for value in _yield_any(obj, steps[0]):
			for x in _handle_all(value, steps[1:], fn):
				yield x
	else:
		step = steps[0]
		if step == '*':
			assert hasattr(obj, 'iteritems'), 'Expecting a dictionary, got %s' % obj
			recurse_dict(obj, fn)
		elif step == '[]':
			assert hasattr(obj, '__iter__'), 'Expecting an array, got %s' % obj
			for i, x in enumerate(obj):
				obj[i] = fn(x)
		else:
			if hasattr(obj, '__contains__') and step in obj:
				obj[step] = fn(obj[step])
	
# # # # # # # # # # # # # # # # # # # 
#
# End data transform
#
# # # # # # # # # # # # # # # # # # # 

def render_string(config, in_s):
	'''Render a Genshi template as a string
	
	:param config: data dictionary
	:param in_s: genshi template
	'''
	tmpl = NewTextTemplate(in_s)

	# older versions of python don't allow unicode keyword arguments
	# so we have to encode the keys (for best compatibility in the client side tools)
	config = _encode_unicode_keys(config)
	return tmpl.generate(**config).render('text')

def _encode_unicode_keys(dictionary):
	'''Returns a new dictionary constructed from the given one, but with the keys encoded as strings.
	:param dictionary: dictionary to encode the keys for

	(For use with old versions of python that can't use unicode keys for keyword arguments)'''

	new_items = [(str(k), v) for k, v in dictionary.items()]
	return dict(new_items)

def _resolve_url(config, url, prefix):
	'''Prefix non-absolute URLs with the path to the user's code'''
	if hasattr(url, "startswith"):
		# string
		if url.startswith('http://') or \
				url.startswith('https://') or \
				url.startswith(prefix):
			return url
		else:
			return prefix + url if url.startswith('/') else prefix + '/' + url
	else:
		# summat else
		return url

class RunnerState(object):
	pass

def run_shell(*args, **kw):
	check_for_interrupt = kw.get('check_for_interrupt', False)
	fail_silently = kw.get('fail_silently', False)
	command_log_level = kw.get("command_log_level", logging.DEBUG)
	filter = kw.get("filter", False)

	state = RunnerState()
	state.done = False
	state.output = StringIO.StringIO()
	state.proc = None

	def runner():
		LOG.debug('Running: {cmd}'.format(cmd=subprocess.list2cmdline(args)))
		state.proc = lib.PopenWithoutNewConsole(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=kw.get('env'))

		for line in iter(state.proc.stdout.readline, ''):
			if not filter or filter(line):
				state.output.write(line)
				LOG.log(command_log_level, line.rstrip('\r\n'))

		state.done = True

	if check_for_interrupt:
		try:
			call = lib.current_call()
			runner_thread = threading.Thread(target=runner)
			runner_thread.daemon = True
			runner_thread.start()

			while not state.done:
				time.sleep(1)
				call.assert_not_interrupted()
		finally:
			# if interrupted, kill child process
			if state.proc and not state.done:
				lib.progressive_kill(state.proc.pid)

	else:
		runner()

	if state.proc.wait() != 0:
		if fail_silently:
			LOG.debug('Failed to run %s, but was told to carry on anyway' % subprocess.list2cmdline(args))
		else:
			raise ShellError(
				message="Failed when running {command}".format(command=args[0]),
				output=state.output.getvalue()
			)

	return state.output.getvalue()

def path_to_lib():
	return path.abspath(path.join(
		__file__,
		path.pardir,
		path.pardir,
		'lib',
	))

def ensure_lib_available(build, file):
	lib_dir = path.join(path.dirname(build.source_dir), '.lib')
	hash_path = path.join(path.dirname(build.source_dir), '.template', 'lib', 'hash.json')
	if not path.exists(lib_dir):
		os.makedirs(lib_dir)
		
	# Hide directory on windows
	if sys.platform == 'win32':
		try:
			lib.PopenWithoutNewConsole(['attrib', '+h', lib_dir]).wait()
		except Exception:
			# don't care if we fail to hide the templates dir
			pass
	
	hashes = None
	if path.exists(hash_path):
		with open(hash_path, 'r') as hash_file:
			hashes = json.load(hash_file)
	
	file_path = path.join(lib_dir, file)
	if path.exists(file_path) and file in hashes:
		# Check hash
		with open(file_path, 'rb') as cur_file:
			hash = hashlib.md5(cur_file.read()).hexdigest()
			if hash == hashes[file]:
				# File exists and is correct
				build.log.debug("File: %s, already downloaded and correct." % file)
				return file_path

	# File doesn't exist, or has the wrong hash or has no known hash - download
	build.log.info("Downloading lib file: %s, this will only happen when a new file is available." % file)
	
	from forge.remote import Remote
	from forge import build_config
	config = build_config.load()
	remote = Remote(config)

	remote._get_file("https://%s/lib-static/%s/%s" % (remote.hostname, build.config['platform_version'], file), file_path)
	
	# Make file executable.
	os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
	
	return file_path

