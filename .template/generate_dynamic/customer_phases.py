"Tasks that might be run on the customers's machine"

from os import path

# where the customer code exists inside the apps
locations = {
	'android': 'development/android/assets/src',
	'ios': 'development/ios/*/assets/src',
	'chrome': 'development/chrome/src',
	'firefox': 'development/firefox/resources/f/data/src',
	'safari': 'development/forge.safariextension/src',
	'ie': 'development/ie/src',
	'web': 'development/web/src',
	'wp': 'development/wp/assets/src',
}

def copy_user_source_to_tempdir(ignore_patterns=None, tempdir=None):
	return [
		('all', None, 'copy_files', (), { 'from': 'src', 'to': tempdir, 'ignore_patterns': ignore_patterns }),
	]

def delete_tempdir(tempdir=None):
	return [
		('all', None, 'remove_files', (tempdir,),),
	]

def run_hook(hook=None, dir=None):
	return [
		('all', '', 'run_hook', (), { 'hook': hook, 'dir': dir }),
	]
def copy_user_source_to_template(ignore_patterns=None, src='src'):
	return [
		('android', None, 'copy_files', (), { 'from': src, 'to': locations["android"], 'ignore_patterns': ignore_patterns }),
		('ios', None, 'copy_files', (), { 'from': src, 'to': locations["ios"], 'ignore_patterns': ignore_patterns }),
		('chrome', None, 'copy_files', (), {'from': src, 'to': locations["chrome"], 'ignore_patterns': ignore_patterns }),
		('firefox', None, 'copy_files', (), {'from': src, 'to': locations["firefox"], 'ignore_patterns': ignore_patterns }),
		('safari', None, 'copy_files', (), {'from': src, 'to': locations["safari"], 'ignore_patterns': ignore_patterns }),
		('ie', None, 'copy_files', (), {'from': src, 'to': locations["ie"], 'ignore_patterns': ignore_patterns }),
		('web', None, 'copy_files', (), {'from': src, 'to': locations["web"], 'ignore_patterns': ignore_patterns }),
		('wp', None, 'copy_files', (), {'from': src, 'to': locations["wp"], 'ignore_patterns': ignore_patterns }),
	]
	
def include_platform_in_html(server=False):
	return [
		('android', None, 'find_and_replace_in_dir',
			(locations["android"],),
			{
				"find": "<head>",
				"replace": "<head><script src='file:///android_asset/forge/all.js'></script>"
			}
		),
		('ios', None, 'find_and_replace_in_dir',
			(locations["ios"],),
			{
				"find": "<head>",
				"replace": "<head><script src='%{back_to_parent}%forge/all.js'></script>"
			}
		),
		('firefox', None, 'find_and_replace_in_dir',
			(locations["firefox"],),
			{
				"find": "<head>",
				"replace": "<head><script src='%{back_to_parent}%forge/all.js'></script>"
			}
		),
		('chrome', None, 'find_and_replace_in_dir',
			(locations["chrome"],),
			{
				"find": "<head>",
				"replace": "<head><script src='/forge/all.js'></script>"
			}
		),
		('safari', None, 'find_and_replace_in_dir',
			(locations["safari"],),
			{
				"find": "<head>",
				"replace": "<head><script src='%{back_to_parent}%forge/all.js'></script>"
			}
		),
		('ie', None, 'find_and_replace_in_dir',
			(locations["ie"],),
			{
				"find": "<head>",
				"replace": "<head><script src='%{back_to_parent}%forge/all.js'></script>"
			}
		),
		('web', None, 'find_and_replace_in_dir',
			(locations["web"],),
			{
				"find": "<head>",
				"replace": "<head><script src='/_forge/all.js'></script>"
			}
		),
		#('wp', None, 'find_and_replace_in_dir',
		#	(locations["wp"],),
		#	{
		#		"find": "<script",  # TODO replace_regex? replace_html?
		#		"replace": "<script defer"
		#	}
		#),
		('wp', None, 'find_and_replace_in_dir',
			(locations["wp"],),
			{
				"find": "<head>",
				"replace": "<head><script src='/assets/forge/all.js'></script>"
			}
		),
		('wp', None, 'find_and_replace_in_dir',
			(locations["wp"],),
			{
				"find": "<head>",
				"replace": """<head><script>
					function window$forge$_receive(result) {
						try {
							window.forge._receive(JSON.parse(result));
						} catch (e) {
							forge.logging.error("window$forge$_receive -> " + e);
						}
					}
				</script>"""
			}
		),
	]

def wrap_activations(server=False):
	return [
		('firefox', None, 'wrap_activations',
			(locations["firefox"],),
		),
		('safari', None, 'wrap_activations',
			(locations["safari"],),
		),
	]

_icon_path_for_server = {
	"android": "android/template-app/res/",
	"safari": "forge.safariextension/",
	"firefox": "firefox/template-app/output/",
	"ios": "ios/",
	"wp": "wp/dist/"
}
_icon_path_for_customer = {
	"android": "development/android/res/",
	"safari": "development/forge.safariextension/",
	"firefox": "development/firefox/",
	"ios": "development/ios/*.app/",
	"wp": "development/wp/dist/"
}

def include_icons(server=False):
	icon_path = _icon_path_for_server if server else _icon_path_for_customer
	def icon(platform, sub_path):
		return path.join(icon_path[platform], sub_path)

	return [
		('android', None, 'populate_icons', ("android", [36, 48, 72])),
		('chrome', None, 'populate_icons', ("chrome", [16, 48, 128])),
		('firefox', None, 'populate_icons', ("firefox", [32, 64])),
		('ios', None, 'populate_icons', ("ios", [57, 72, 114])),
		('safari', None, 'populate_icons', ("safari", [32, 48, 64])),
		('wp', None, 'populate_icons', ("wp", [62, 99, 173])),

		('android', 'have_android_icons', 'copy_files', (), {
			'from': '${modules["icons"]["android"]["36"]}',
			'to': icon("android", 'drawable-ldpi/icon.png')}),
		('android', 'have_android_icons', 'copy_files', (), {
			'from': '${modules["icons"]["android"]["48"]}',
			'to': icon("android", 'drawable-mdpi/icon.png')}),
		('android', 'have_android_icons', 'copy_files', (), {
			'from': '${modules["icons"]["android"]["72"]}',
			'to': icon("android", "drawable-hdpi/icon.png")}),
		
		('safari', 'have_safari_icons', 'copy_files', (), {
			'from': '${modules["icons"]["safari"]["32"]}',
			'to': icon("safari", 'icon-32.png')}),
		('safari', 'have_safari_icons', 'copy_files', (), {
			'from': '${modules["icons"]["safari"]["48"]}',
			'to': icon("safari", 'icon-48.png')}),
		('safari', 'have_safari_icons', 'copy_files', (), {
			'from': '${modules["icons"]["safari"]["64"]}',
			'to': icon("safari", 'icon-64.png')}),
		
		('firefox', 'have_firefox_icons', 'copy_files', (), {
			'from': '${modules["icons"]["firefox"]["32"]}',
			'to': icon("firefox", 'icon.png')}),
		('firefox', 'have_firefox_icons', 'copy_files', (), {
			'from': '${modules["icons"]["firefox"]["64"]}',
			'to': icon("firefox", 'icon64.png')}),

		('ios', 'have_ios_icons', 'copy_files', (), {
			'from': '${modules["icons"]["ios"]["57"]}',
			'to': icon("ios", 'normal.png')}),
		('ios', 'have_ios_icons', 'copy_files', (), {
			'from': '${modules["icons"]["ios"]["72"]}',
			'to': icon("ios", 'ipad.png')}),
		('ios', 'have_ios_icons', 'copy_files', (), {
			'from': '${modules["icons"]["ios"]["114"]}',
			'to': icon("ios", 'retina.png')}),

		('wp', 'have_wp_icons', 'copy_files', (), {
			'from': '${modules["icons"]["wp"]["62"]}',
			'to': icon("wp", 'ApplicationIcon.png')}),
		('wp', 'have_wp_icons', 'copy_files', (), {
			'from': '${modules["icons"]["wp"]["99"]}',
			'to': icon("wp", 'Marketplace.png')}),
		('wp', 'have_wp_icons', 'copy_files', (), {
			'from': '${modules["icons"]["wp"]["173"]}',
			'to': icon("wp", 'Background.png')}),
			
		('ios', 'have_ios_launch', 'copy_files', (), {
			'from': '${modules["launchimage"]["iphone"]}',
			'to': icon("ios", "Default~iphone.png")}),
		('ios', 'have_ios_launch', 'copy_files', (), {
			'from': '${modules["launchimage"]["iphone-retina"]}',
			'to': icon("ios", "Default@2x~iphone.png")}),
		('ios', 'have_ios_launch', 'copy_files', (), {
			'from': '${modules["launchimage"]["ipad"]}',
			'to': icon("ios", "Default~ipad.png")}),
		('ios', 'have_ios_launch', 'copy_files', (), {
			'from': '${modules["launchimage"]["ipad-landscape"]}',
			'to': icon("ios", "Default-Landscape~ipad.png")}),

		('wp', 'have_wp_launch', 'copy_files', (), {
			'from': '${modules["launchimage"]["wp-landscape"]}',
			'to': icon("wp", "SplashScreenImage.jpg")}),
	]

def include_name():
	# TODO: Paths for server side builds?
	return [
		('android,firefox,safari', None, 'populate_xml_safe_name', ()),
		('chrome,ie,wp', None, 'populate_json_safe_name', ()),
		('android', '', 'find_and_replace', (
			'development/android/res/values/strings.xml',),
			{"find": "APP_NAME_HERE", "replace": "${xml_safe_name}"}
		),
		('ios', '', 'set_in_biplist', (
			'development/ios/*/Info.plist',),
			{"key": "CFBundleName", "value": "${name}"}
		),
		('ios', '', 'set_in_biplist', (
			'development/ios/*/Info.plist',),
			{"key": "CFBundleDisplayName", "value": "${name}"}
		),
		('chrome', '', 'find_and_replace', (
			'development/chrome/manifest.json',),
			{"find": "APP_NAME_HERE", "replace": "${json_safe_name}"}
		),
		('firefox', '', 'find_and_replace', (
			'development/firefox/install.rdf',),
			{"find": "APP_NAME_HERE", "replace": "${xml_safe_name}"}
		),
		('safari', '', 'find_and_replace', (
			'development/forge.safariextension/Info.plist',),
			{"find": "APP_NAME_HERE", "replace": "${xml_safe_name}"}
		),
		('ie', '', 'find_and_replace', (
			'development/ie/manifest.json',
			'development/ie/dist/setup-x86.nsi',
			'development/ie/dist/setup-x64.nsi',),
			{"find": "APP_NAME_HERE", "replace": "${json_safe_name}"}
		),
		('wp', '', 'find_and_replace', (
			'development/wp/Properties/WMAppManifest.xml',),
			{"find": "APP_NAME_HERE", "replace": "${json_safe_name}"}
		),
	]

def include_uuid():
	return [
		('android,firefox,safari,ios,ie', None, 'populate_package_names', ()),
		('android', '', 'find_and_replace', (
			 'development/android/res/values/strings.xml',
			 'development/android/AndroidManifest.xml',),
			 {"find": "PACKAGE_NAME_HERE", "replace": "${modules.package_names.android}"}
		),
		('firefox', '', 'find_and_replace', (
			 'development/firefox/install.rdf','development/firefox/harness-options.json',),
			 {"find": "PACKAGE_NAME_HERE", "replace": "${modules.package_names.firefox}"}
		),
		('safari', '', 'find_and_replace', (
			'development/forge.safariextension/Info.plist',),
			{"find": "PACKAGE_NAME_HERE", "replace": "${modules.package_names.safari}"}
		),
		('ios', '', 'set_in_biplist', (
			'development/ios/*/Info.plist',),
			{"key": "CFBundleIdentifier", "value": "${modules.package_names.ios}"}
		),
		('ie', '', 'find_and_replace', (
			'development/ie/manifest.json',),
			{"find": "UUID_HERE", "replace": "${uuid}"}
		),
		('ie', '', 'find_and_replace', (
			'development/ie/dist/setup-x86.nsi','development/ie/dist/setup-x64.nsi',),
			{"find": "MS_CLSID_HERE", "replace": "${modules.package_names.ie}"}
		),
	]

def include_author():
	return [
		('firefox', '', 'find_and_replace', (
			'development/firefox/install.rdf','development/firefox/harness-options.json',),
			{"find": "AUTHOR_HERE", "replace": "${author}"}
		),
		('safari', '', 'find_and_replace', (
			'development/forge.safariextension/Info.plist',),
			{"find": "AUTHOR_HERE", "replace": "${author}"}
		),
		('ie', '', 'find_and_replace', (
			'development/ie/manifest.json',
			'development/ie/dist/setup-x86.nsi','development/ie/dist/setup-x64.nsi',),
			{"find": "AUTHOR_HERE", "replace": "${author}"}
		),
	]

def include_description():
	return [
		('chrome', '', 'find_and_replace', (
			'development/chrome/manifest.json',),
			{"find": "DESCRIPTION_HERE", "replace": "${description}"}
		),
		('firefox', '', 'find_and_replace', (
			'development/firefox/install.rdf','development/firefox/harness-options.json',),
			{"find": "DESCRIPTION_HERE", "replace": "${description}"}
		),
		('safari', '', 'find_and_replace', (
			'development/forge.safariextension/Info.plist',),
			{"find": "DESCRIPTION_HERE", "replace": "${description}"}
		),
		('ie', '', 'find_and_replace', (
			'development/ie/manifest.json',
			'development/ie/dist/setup-x86.nsi','development/ie/dist/setup-x64.nsi',),
			{"find": "DESCRIPTION_HERE", "replace": "${author}"}
		),
	]


def resolve_urls():
	return [
		('all', None, 'resolve_urls', (
			'modules.activations.[].scripts.[]',
			'modules.activations.[].styles.[]',
			'modules.icons.*',
			'modules.launchimage.*',
			'modules.button.default_icon',
			'modules.button.default_popup',
			'modules.button.default_icons.*'
		)),
	]

def run_android_phase(build_type_dir, sdk, device, interactive, purge=False):
	return [
		('android', None, 'run_android', (build_type_dir, sdk, device, interactive, purge)),
	]

def run_ios_phase(device):
	return [
		('ios', None, 'run_ios', (device, )),
	]

def run_firefox_phase(build_type_dir):
	return [
		('firefox', None, 'run_firefox', (build_type_dir,)),
	]
	
def run_web_phase():
	return [
		('web', None, 'run_web'),
	]

def run_wp_phase(device):
	return [
		('wp', None, 'run_wp', (device, )),
	]

def run_chrome_phase():
	return [
		('chrome', None, 'run_chrome'),
	]

def package(build_type_dir):
	return [
		('android', None, 'package_android'),
		('ios', None, 'package_ios'),
		('web', None, 'package_web'),
		('wp', None, 'package_wp'),
		('chrome', None, 'package_chrome'),
	]

def make_installers():
	return [
		('ie', None, 'package_ie'),
	]

def check_javascript():
	return [
			('all', None, 'lint_javascript'),
	]

def check_local_config_schema():
	return [
			('all', None, 'check_local_config_schema')
	]

def migrate_config():
	return [
			('all', None, 'migrate_config'),
	]

def clean_phase():
	return [
			('android', None, 'clean_android'),
			('firefox', None, 'clean_firefox', ('development',)),
			('web', None, 'clean_web'),
			('wp',	None, 'clean_wp'),
	]
