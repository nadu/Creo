from collections import namedtuple
import logging
import multiprocessing
import os
from os import path
import re
import shutil
from subprocess import PIPE, STDOUT
import threading
import sys
import tempfile
import time
import zipfile

import lib
from lib import temp_file, task, CouldNotLocate, ProgressBar
from utils import run_shell

LOG = logging.getLogger(__name__)

class AndroidError(lib.BASE_EXCEPTION):
	pass

# TODO: put jdk/jre info in here also, as they're often used together?
# tuple type for passing around information about where android tools are located
PathInfo = namedtuple('PathInfo', 'android adb aapt sdk')

def _create_path_info_from_sdk(sdk):
	"""Helper for constructing a PathInfo object from just the android SDK
	location"""
	return PathInfo(
		android=path.abspath(path.join(
			sdk,
			'tools',
			'android.bat' if sys.platform.startswith('win') else 'android'
		)),
		adb=path.abspath(path.join(sdk, 'platform-tools', 'adb')),
		aapt=path.abspath(path.join(sdk, 'platform-tools', 'aapt')),
		sdk=sdk,
	)

def _run_adb(cmd, timeout, path_info):
	runner = {
		"process": None,
		"std_out": None
	}
	def target():
		try:
			runner['process'] = lib.PopenWithoutNewConsole(cmd, stdout=PIPE, stderr=STDOUT)
		except Exception:
			LOG.error("problem finding the android debug bridge at: %s" % path_info.adb)
			# XXX: prompt to run the sdk manager, then retry?
			LOG.error("this probably means you need to run the Android SDK manager and download the Android platform-tools.")
			raise AndroidError

		runner['std_out'] = runner['process'].communicate()[0]

	thread = threading.Thread(target=target)
	thread.start()

	thread.join(timeout)
	if thread.is_alive():
		LOG.debug('ADB hung, terminating process')
		_restart_adb(path_info)
		thread.join()
	
	if runner['process'].returncode != 0:
		LOG.error('Communication with adb failed: %s' % (runner['std_out']))
		raise AndroidError
	
	return runner['std_out']

def _kill_adb():
	if sys.platform.startswith('win'):
		run_shell('taskkill', '/T', '/IM', 'adb.exe', fail_silently=True)
		run_shell('taskkill', '/T', '/F', '/IM', 'adb.exe', fail_silently=True)
	else:
		run_shell('killall', 'adb', fail_silently=True)
		run_shell('killall', '-9', 'adb', fail_silently=True)

def _restart_adb(path_info):
	"""Forcably kills any ADB processes running on the system and starts
	a new one detached from this process
	"""
	_kill_adb()
	
	run_detached([path_info.adb, 'start-server'], wait=True)

def _look_for_java():
	possible_jre_locations = [
		r"C:\Program Files\Java\jre7",
		r"C:\Program Files\Java\jre6",
		r"C:\Program Files (x86)\Java\jre7",
		r"C:\Program Files (x86)\Java\jre6",
	]

	return [directory for directory in possible_jre_locations if path.isdir(directory)]

def _download_sdk_for_windows(temp_d):
	archive_path = path.join(temp_d, "sdk.zip")
	lib.download_with_progress_bar('Downloading Android SDK',
			"https://trigger.io/redirect/android/windows", archive_path)


	LOG.info('Download complete, extracting SDK')
	zip_to_extract = zipfile.ZipFile(archive_path)
	zip_to_extract.extractall("C:\\")
	zip_to_extract.close()

	# TODO: should this really be hardcoded to C:\android-sdk-windows?
	# wasn't sure if we were allowing user to specify location..
	return _create_path_info_from_sdk("C:\\android-sdk-windows")

def _download_sdk_for_mac(temp_d):
	archive_path = path.join(temp_d, "sdk.zip")
	lib.download_with_progress_bar('Downloading Android SDK',
			"https://trigger.io/redirect/android/macosx", archive_path)

	LOG.info('Download complete, extracting SDK')
	zip_process = lib.PopenWithoutNewConsole(["unzip", archive_path, '-d', "/Applications"], stdout=PIPE, stderr=STDOUT)
	output = zip_process.communicate()[0]
	LOG.debug("unzip output")
	LOG.debug(output)

	return _create_path_info_from_sdk("/Applications/android-sdk-macosx/tools/android")

def _download_sdk_for_linux(temp_d):
	archive_path = path.join(temp_d, "sdk.tgz")
	lib.download_with_progress_bar('Downloading Android SDK',
			"https://trigger.io/redirect/android/linux", archive_path)

	LOG.info('Download complete, extracting SDK')
	if not path.isdir(path.expanduser("~/.forge")):
		os.mkdir(path.expanduser("~/.forge"))

	zip_process = lib.PopenWithoutNewConsole(["tar", "zxf", archive_path, "-C", path.expanduser("~/.forge")], stdout=PIPE, stderr=STDOUT)
	output = zip_process.communicate()[0]
	LOG.debug("unzip output")
	LOG.debug(output)

	return _create_path_info_from_sdk("~/.forge/android-sdk-linux/tools/android")

def _install_sdk_automatically():
	# Attempt download
	temp_d = tempfile.mkdtemp()
	try:
		LOG.info('Downloading Android SDK (about 30MB, may take some time)')
		if sys.platform.startswith('win'):
			path_info = _download_sdk_for_windows(temp_d)
		elif sys.platform.startswith('darwin'):
			path_info = _download_sdk_for_mac(temp_d)
		elif sys.platform.startswith('linux'):
			path_info = _download_sdk_for_linux(temp_d)

		_update_sdk(path_info)

		LOG.info('Android SDK update complete')
		return path_info
	except Exception, e:
		LOG.error(e)
		raise CouldNotLocate("Automatic SDK download failed, please install manually and specify with the --android.sdk flag")
	finally:
		shutil.rmtree(temp_d, ignore_errors=True)

def _update_sdk(path_info):
	LOG.info('Updating SDK and downloading required Android platform '
			'(about 90MB, may take some time)')
	
	APPROX_UPPER_BOUND_ON_ANDROID_OUTPUT = 60
	android_process = lib.PopenWithoutNewConsole(
		[path_info.android, "update", "sdk", "--no-ui", "--filter",
			"platform-tool,tool,android-8"],
		stdout=PIPE,
		stderr=STDOUT,
	)

	with ProgressBar('Installing Android SDK Components') as bar:
		finished = []

		def kill_adb_occasionally():
			"""When updating the android sdk, occasionally ADB will have a lock on
			some files causing the update to fail. Killing it here helps the update succeed.
			"""
			while not finished:
				time.sleep(5)
				try:
					_kill_adb()
				except Exception:
					pass
		adb_killing_thread = threading.Thread(target=kill_adb_occasionally)
		adb_killing_thread.daemon = True
		adb_killing_thread.start()

		for i, line in enumerate(iter(android_process.stdout.readline, '')):
			bar.progress(float(i) / APPROX_UPPER_BOUND_ON_ANDROID_OUTPUT)

		finished.append(True)

	
def _ask_user_if_should_install_sdk():
	if sys.platform.startswith('win'):
		sdk_path = "C:\\android-sdk-windows"
	elif sys.platform.startswith('linux'):
		sdk_path = path.expanduser("~/.forge/android-sdk-linux")
	elif sys.platform.startswith('darwin'):
		sdk_path = "/Applications/android-sdk-macosx"
	# TODO: else ask user where to install to?

	choice = lib.ask_multichoice(question_text='No Android SDK found on your system, you can either:', choices=[
		'Attempt to download and install the SDK automatically to {sdk_path}'.format(sdk_path=sdk_path),
		'Specify the location of an already existing Android SDK installation'
	])

	return choice == 1

def _prompt_user_to_attach_device(path_info):
	"""Ask user if they want to launch an AVD or attempt to find a device again."""
 
	choice = lib.ask_multichoice(question_text='No active Android device found, would you like to:', choices=[
		'Attempt to automatically launch the Android emulator',
		'Attempt to find the device again (choose this option after plugging in an Android device or launching the emulator)',
	])

	if choice != 1:
		return

	_create_avd_if_necessary(path_info)
	_launch_avd(path_info)

def _search_for_sdk(build):
	# Some sensible places to look for the Android SDK
	possible_sdk = [
		"C:/Program Files (x86)/Android/android-sdk/",
		"C:/Program Files/Android/android-sdk/",
		"C:/Android/android-sdk/",
		"C:/Android/android-sdk-windows/",
		"C:/android-sdk-windows/",
		"/Applications/android-sdk-macosx",
		path.expanduser("~/.forge/android-sdk-linux")
	]

	user_sdk = build.tool_config.get('android.sdk')

	if user_sdk:
		# if android SDK supplied by user, normalise the path and add
		# it to the list of places to look
		user_sdk = lib.expand_relative_path(build, user_sdk)
		possible_sdk.insert(0, user_sdk)

	for directory in possible_sdk:
		if path.isdir(directory):
			found_sdk = directory if directory.endswith('/') else directory + '/'
			return _create_path_info_from_sdk(found_sdk)

def _find_or_install_sdk(build):
	"""Searches for and returns the details of an Android SDK already existing
	on the operating system, otherwise presents the user with a choice to
	install one and returns the details of that after doing so.

	:param build: Contains information about the system, e.g. user specific SDK
	
	Returns a PathInfo object constructed using the SDK found or installed.
	"""
	already_installed = _search_for_sdk(build)
	
	if already_installed:
		return already_installed

	if _ask_user_if_should_install_sdk():
		return _install_sdk_automatically()
	else:
		raise AndroidError("Couldn't find Android SDK, please set this an "
				"option in your local config")

def _scrape_available_devices(text):
	"""Scrapes the output of the adb devices command into a list

	:param text: Full output of adb devices command to scrape
	"""
	lines = text.split('\n')
	available_devices = []

	for line in lines:
		words = line.split('\t')

		if len(words[0]) > 5 and words[0].find(" ") == -1:
			available_devices.append(words[0])

	return available_devices

def run_detached(args, wait=True):
	"""Run a process entirely detached from this one, and optionally wait
	for it to finish.

	:param args: list of shell arguments
	:param wait: don't return until the command completes
	"""
	if sys.platform.startswith('win'):
		if wait:
			os.system("cmd /c start /WAIT "
					"\"Detached Forge command - will automatically close\" "
					"\""+"\" \"".join(args)+"\"")
		else:
			os.system("cmd /c start "
					"\"Detached Forge command\" "
					"\""+"\" \"".join(args)+"\"")
	else:
		def run_in_shell(queue):
			'''will be invoked in by a separate process, to actually run the
			detached command'''
			# setsid detaches us completely from the caller
			os.setsid()

			# os.devnull is used to ensure that no [1] foo;
			# lines are shown in the commandline output
			with open(os.devnull) as devnull:
				proc = lib.PopenWithoutNewConsole(args, stdout=devnull, stderr=STDOUT)
			if wait:
				proc.wait()

			# signal that we're finished
			queue.put(True)

		# to get the "finished" signal
		queue = multiprocessing.Queue()

		# multiprocessing throws an error on start() if we spawn a process from
		# a daemon process but we don't care about this
		multiprocessing.current_process().daemon = False

		proc = multiprocessing.Process(target=run_in_shell, args=(queue, ))
		proc.daemon = True
		proc.start()
		# wait until the command completes
		queue.get()

def check_for_java():
	'Return True java exists on the path and can be invoked; False otherwise'
	with open(os.devnull, 'w') as devnull:
		try:
			proc = lib.PopenWithoutNewConsole(['java', '-version'], stdout=devnull, stderr=devnull)
			proc.communicate()[0]
			return proc.returncode == 0
		except:
			return False

def _create_avd(path_info):
	LOG.info('Creating AVD')
	args = [
		path_info.android,
		"create",
		"avd",
		"-n", "forge",
		"-t", "android-8",
		"--skin", "HVGA",
		"-p", path.join(path_info.sdk, 'forge-avd'),
		#"-a",
		"-c", "32M",
		"--force"
	]
	proc = lib.PopenWithoutNewConsole(args, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
	time.sleep(0.1)
	proc_std = proc.communicate(input='\n')[0]
	if proc.returncode != 0:
		LOG.error('failed: %s' % (proc_std))
		raise AndroidError
	LOG.debug('Output:\n'+proc_std)

def _launch_avd(path_info):
	run_detached(
			[path.join(path_info.sdk, "tools", "emulator"),
				"-avd", "forge"],
			wait=False)
	
	LOG.info("Started emulator, waiting for device to boot")
	_run_adb([path_info.adb, 'wait-for-device'], 120, path_info)
	# adb shell can return too quickly without a small sleep here.
	time.sleep(1)
	_run_adb([path_info.adb, "shell", "pm", "path", "android"], 120, path_info)

def _create_apk_with_aapt(out_apk_name, path_info, package_name, lib_path, dev_dir):
	LOG.info('Creating APK with aapt')

	run_shell(path_info.aapt,
		'p', # create APK package
		'-F', out_apk_name, # output name
		'-S', path.join(dev_dir, 'res'), # uncompressed resources folder
		'-M', path.join(dev_dir, 'AndroidManifest.xml'), # uncompressed xml manifest
		'-I', path.join(lib_path, 'android-platform.apk'), # Android platform to "compile" resources against
		'-A', path.join(dev_dir, 'assets'), # Assets folder to include
		'-0', '', # Don't compress any assets - Important for content provider access to assets
		'--rename-manifest-package', package_name, # Package name
		'-f', # Force overwrite
		path.join(dev_dir, 'output'), # Location of raw files (app binary)
		command_log_level=logging.DEBUG)

def _sign_zipf(lib_path, jre, keystore, storepass, keyalias, keypass, signed_zipf_name, zipf_name):
	args = [
		path.join(jre,'java'),
		'-jar',
		path.join(lib_path, 'apk-signer.jar'),
		'--keystore',
		keystore,
		'--storepass',
		storepass,
		'--keyalias',
		keyalias,
		'--keypass',
		keypass,
		'--out',
		signed_zipf_name,
		zipf_name
	]
	run_shell(*args)

def _sign_zipf_debug(lib_path, jre, zipf_name, signed_zipf_name):
	LOG.info('Signing APK with a debug key')

	return _sign_zipf(
		lib_path=lib_path,
		jre=jre,
		keystore=path.join(lib_path, 'debug.keystore'),
		storepass="android",
		keyalias="androiddebugkey",
		keypass="android",
		signed_zipf_name=signed_zipf_name,
		zipf_name=zipf_name,
	)

def _sign_zipf_release(lib_path, jre, zipf_name, signed_zipf_name, keystore, storepass, keyalias, keypass):
	LOG.info('Signing APK with your release key')
	return _sign_zipf(
		lib_path=lib_path,
		jre=jre,
		keystore=keystore,
		storepass=storepass,
		keyalias=keyalias,
		keypass=keypass,
		signed_zipf_name=signed_zipf_name,
		zipf_name=zipf_name,
	)
	
def _align_apk(path_info, signed_zipf_name, out_apk_name):
	LOG.info('Aligning apk')

	args = [path.join(path_info.sdk, 'tools', 'zipalign'), '-v', '4', signed_zipf_name, out_apk_name]
	run_shell(*args)

def _generate_package_name(build):
	if "package_names" not in build.config["modules"]:
		build.config["modules"]["package_names"] = {}
	if "android" not in build.config["modules"]["package_names"]:
		build.config["modules"]["package_names"]["android"] = "io.trigger.forge"+build.config["uuid"]
	return build.config["modules"]["package_names"]["android"]
	
def _follow_log(path_info, chosen_device):
	LOG.info('Clearing android log')

	args = [path_info.adb, '-s', chosen_device, 'logcat', '-c']
	run_shell(*args, command_log_level=logging.INFO)

	LOG.info('Showing android log')

	run_shell(path_info.adb, '-s', chosen_device, 'logcat', 'WebCore:D', 'Forge:D', '*:s', command_log_level=logging.INFO, check_for_interrupt=True)

def _create_avd_if_necessary(path_info):
	# Create avd
	LOG.info('Checking for previously created AVD')
	if path.isdir(path.join(path_info.sdk, 'forge-avd')):
		LOG.info('Existing AVD found')
	else:
		_create_avd(path_info)

def _get_available_devices(path_info, try_count=0):
	proc_std = _run_adb([path_info.adb, 'devices'], timeout=10, path_info=path_info)
		
	available_devices = _scrape_available_devices(proc_std)
	
	if not available_devices and try_count < 3:
		LOG.debug('No devices found, checking again')
		time.sleep(2)
		if try_count == 1:
			_restart_adb(path_info)
		return _get_available_devices(path_info, (try_count + 1))
	else:
		return available_devices

@task
def clean_android(build):
	pass

def _get_jre():
	result = ""
	if not check_for_java():
		jres = _look_for_java()
		if not jres:
			raise AndroidError("Java not found: Java must be installed and available in your path in order to run Android")
		result = path.join(jres[0], 'bin')
	return result

def create_apk(build, sdk, output_filename, interactive=True):
	'''
	:param output_filename: name of the file to which we'll write
	'''
	path_info = _find_or_install_sdk(build)
	jre = ""
 
	jre = _get_jre()

	lib_path = path.normpath(path.join('.template', 'lib'))
	dev_dir = path.normpath(path.join('development', 'android'))
	package_name = _generate_package_name(build)
	
	LOG.info('Creating Android .apk file')

	with temp_file() as zipf_name:
		# Compile XML files into APK
		_create_apk_with_aapt(zipf_name, path_info, package_name, lib_path, dev_dir)
		
		with temp_file() as signed_zipf_name:
			# Sign APK
			_sign_zipf_debug(lib_path, jre, zipf_name, signed_zipf_name)
			
			# Align APK
			_align_apk(path_info, signed_zipf_name, output_filename)

@task
def run_android(build, build_type_dir, sdk, device, interactive=True,
		purge=False):
	# TODO: remove sdk parameter from here and call sites, information is
	# contained in build.tool_config already

	# TODO: remove build_type_dir from method and call sites, doesn't seem to
	# be used anywhere

	# TODO: remove interactive parameter. this information is contained in the
	# build, but we should never use this anyway, as we can now interact with
	# the toolkit from here
	path_info = _find_or_install_sdk(build)

	LOG.info('Starting ADB if not running')
	run_detached([path_info.adb, 'start-server'], wait=True)

	LOG.info('Looking for Android device')
	
	available_devices = _get_available_devices(path_info)

	if not available_devices:
		_prompt_user_to_attach_device(path_info)

		return run_android(build, build_type_dir, sdk, device,
				interactive=interactive)

	if device:
		if device in available_devices:
			chosen_device = device
			LOG.info('Using specified android device %s' % chosen_device)
		else:
			LOG.error('No such device "%s"' % device)
			LOG.error('The available devices are:')
			LOG.error("\n".join(available_devices))
			raise AndroidError
	else:
		chosen_device = available_devices[0]
		LOG.info('No android device specified, defaulting to %s' % chosen_device)

	with temp_file() as out_apk_name:
		create_apk(build, sdk, out_apk_name, interactive=interactive)
		package_name = _generate_package_name(build)
		
		# If required remove previous installs from device
		if purge:
			_run_adb([path_info.adb, 'uninstall', package_name], 30, path_info)

		# Install APK to device
		LOG.info('Installing apk')
		proc_std = _run_adb([path_info.adb, '-s', chosen_device, 'install', '-r', out_apk_name], 60, path_info)
	LOG.debug(proc_std)

	# Start app on device
	proc_std = _run_adb([path_info.adb, '-s', chosen_device, 'shell', 'am', 'start', '-n', package_name+'/io.trigger.forge.android.template.LoadActivity'], 60, path_info)
	LOG.debug(proc_std)
	
	#follow log
	_follow_log(path_info, chosen_device)

def _create_output_directory(output):
	'output might be in some other directory which does not yet exist'
	directory = path.dirname(output)
	if not path.isdir(directory):
		os.makedirs(directory)

def _generate_path_to_output_apk(build):
	file_name = "{name}-{time}.apk".format(
		name=re.sub("[^a-zA-Z0-9]", "", build.config["name"].lower()),
		time=str(int(time.time()))
	)
	return path.normpath(path.join('release', 'android', file_name))
	
def _lookup_or_prompt_for_signing_info(build):
	"""Obtain the required details for signing an APK, first by checking local_config.json
	and then asking the user for anything missing.
	"""

	required_info = {
		'keystore': {
			'type': 'string',
			'_filepicker': True,
			'description': 'The location of your release keystore',
			'title': 'Keystore',
		},
		'storepass': {
			'type': 'string',
			'_password': True,
			'description': 'The password for your release keystore',
			'title': 'Keystore password',
		},
		'keyalias': {
			'type': 'string',
			'description': 'The alias of your release key',
			'title': 'Key alias',
		},
		'keypass': {
			'type': 'string',
			'_password': True,
			'description': 'The password for your release key',
			'title': 'Key password'
		}
	}

	known_info = {}
	unknown_info = {}

	# figure out which info we have in local_config.json and which we need to ask for
	for prop_name in required_info.keys():
		local_config_value = build.tool_config.get('android.profile.%s' % prop_name)

		if local_config_value:
			known_info[prop_name] = local_config_value
		else:
			unknown_info[prop_name] = required_info[prop_name]

	# if there's anything we need to ask for, ask for it
	if unknown_info:
		event_id = lib.current_call().emit('question', schema={
			'description': 'Enter details for signing your app',
			'properties': unknown_info
		})

		response = lib.current_call().wait_for_response(event_id)
		# TODO: save info submitted by user
		known_info.update(response['data'])

	return known_info
@task
def package_android(build):
	path_info = _find_or_install_sdk(build)

	lib_path = path.normpath(path.join('.template', 'lib'))
	dev_dir = path.normpath(path.join('development', 'android'))
	output = _generate_path_to_output_apk(build)
	signing_info = _lookup_or_prompt_for_signing_info(build)
	
	
	signing_info["keystore"] = lib.expand_relative_path(build,
			signing_info["keystore"])
	jre = _get_jre() or ""

	LOG.info('Creating Android .apk file')
	package_name = _generate_package_name(build)
	#zip
	with temp_file() as zipf_name:
		_create_apk_with_aapt(zipf_name, path_info, package_name, lib_path, dev_dir)

		with temp_file() as signed_zipf_name:
			#sign
			_sign_zipf_release(lib_path, jre, zipf_name, signed_zipf_name, **signing_info)

			# create output directory for APK if necessary
			_create_output_directory(output)

			#align
			_align_apk(path_info, signed_zipf_name, output)
			LOG.debug('removing zipfile and un-aligned APK')

			LOG.info("created APK: {output}".format(output=output))
			return output
