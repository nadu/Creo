
from lib import predicate
import sys

@predicate
def is_external(build):
	return bool(build.external)

@predicate
def do_package(build):
	return getattr(build, "package", False)

@predicate
def have_safari_icons(build):
	return "icons" in build.config["modules"] and \
		("32" in build.config["modules"]["icons"] or "32" in build.config["modules"]["icons"].get("safari", {})) and \
		("48" in build.config["modules"]["icons"] or "48" in build.config["modules"]["icons"].get("safari", {})) and \
		("64" in build.config["modules"]["icons"] or "64" in build.config["modules"]["icons"].get("safari", {}))

@predicate
def have_android_icons(build):
	return "icons" in build.config["modules"] and \
		("36" in build.config["modules"]["icons"] or "36" in build.config["modules"]["icons"].get("android", {})) and \
		("48" in build.config["modules"]["icons"] or "48" in build.config["modules"]["icons"].get("android", {})) and \
		("72" in build.config["modules"]["icons"] or "72" in build.config["modules"]["icons"].get("android", {}))

@predicate
def have_firefox_icons(build):
	return "icons" in build.config["modules"] and \
		("32" in build.config["modules"]["icons"] or "32" in build.config["modules"]["icons"].get("firefox", {})) and \
		("64" in build.config["modules"]["icons"] or "64" in build.config["modules"]["icons"].get("firefox", {}))

@predicate
def have_ios_icons(build):
	return "icons" in build.config["modules"] and \
		("57" in build.config["modules"]["icons"] or "57" in build.config["modules"]["icons"].get("ios", {})) and \
		("72" in build.config["modules"]["icons"] or "72" in build.config["modules"]["icons"].get("ios", {})) and \
		("114" in build.config["modules"]["icons"] or "114" in build.config["modules"]["icons"].get("ios", {}))

@predicate
def have_wp_icons(build):
	return "icons" in build.config["modules"] and \
		("62" in build.config["modules"]["icons"] or "62" in build.config["modules"]["icons"].get("wp", {})) and \
		("99" in build.config["modules"]["icons"] or "99" in build.config["modules"]["icons"].get("wp", {})) and \
		("173" in build.config["modules"]["icons"] or "173" in build.config["modules"]["icons"].get("wp", {}))

@predicate
def have_ios_launch(build):
	return "launchimage" in build.config["modules"] and \
		"iphone" in build.config["modules"]["launchimage"] and \
		"iphone-retina" in build.config["modules"]["launchimage"] and \
		"ipad" in build.config["modules"]["launchimage"] and \
		"ipad-landscape" in build.config["modules"]["launchimage"]

@predicate
def have_android_launch(build):
	return "launchimage" in build.config["modules"] and \
		"android" in build.config["modules"]["launchimage"] and \
		"android-landscape" in build.config["modules"]["launchimage"]

@predicate
def have_wp_launch(build):
	return "launchimage" in build.config["modules"] and \
		"wp" in build.config["modules"]["launchimage"] and \
		"wp-landscape" in build.config["modules"]["launchimage"]

@predicate
def include_gmail(build):
	return "gmail" in build.config["modules"]

@predicate
def include_jquery(build):
	return "jquery"in build.config["modules"]
				
def _disable_orientation_generic(build, device, orientation):
	if not 'orientations' in build.config["modules"]:
		return False
	
	if device in build.config["modules"]['orientations']:
		return not build.config["modules"]['orientations'][device] == orientation and not build.config["modules"]['orientations'][device] == 'any'
	elif 'default' in build.config["modules"]['orientations']:
		return not build.config["modules"]['orientations']['default'] == orientation and not build.config["modules"]['orientations']['default'] == 'any'
	else:
		return False

@predicate
def disable_orientation_iphone_portrait_up(build):
	return _disable_orientation_generic(build, 'iphone', 'portrait')
	
@predicate
def disable_orientation_iphone_portrait_down(build):
	return _disable_orientation_generic(build, 'iphone', 'portrait')

@predicate
def disable_orientation_iphone_landscape_left(build):
	return _disable_orientation_generic(build, 'iphone', 'landscape')

@predicate
def disable_orientation_iphone_landscape_right(build):
	return _disable_orientation_generic(build, 'iphone', 'landscape')

@predicate
def disable_orientation_ipad_portrait_up(build):
	return _disable_orientation_generic(build, 'ipad', 'portrait')
	
@predicate
def disable_orientation_ipad_portrait_down(build):
	return _disable_orientation_generic(build, 'ipad', 'portrait')

@predicate
def disable_orientation_ipad_landscape_left(build):
	return _disable_orientation_generic(build, 'ipad', 'landscape')

@predicate
def disable_orientation_ipad_landscape_right(build):
	return _disable_orientation_generic(build, 'ipad', 'landscape')

@predicate
def partner_parse_enabled(build):
	return "partners" in build.config and \
				"parse" in build.config["partners"] and \
				"applicationId" in build.config["partners"]["parse"] and \
				"clientKey" in build.config["partners"]["parse"]

@predicate
def partner_parse_disabled(build):
	return not partner_parse_enabled(build)

@predicate
def module_topbar_enabled(build):
	return "modules" in build.config and \
			"topbar" in build.config["modules"]

@predicate
def module_tabbar_enabled(build):
	return "modules" in build.config and \
			"tabbar" in build.config["modules"]

@predicate
def android_permission_location_not_required(build):
	return not "geolocation" in build.config["modules"]

@predicate
def android_permission_contacts_not_required(build):
	return not "contact" in build.config["modules"]

@predicate
def android_permission_vibrate_not_required(build):
	return not ("notification" in build.config["modules"] or ("partners" in build.config and "parse" in build.config["partners"]))

@predicate
def android_permission_boot_not_required(build):
	return not ("partners" in build.config and "parse" in build.config["partners"])

@predicate
def android_permission_storage_not_required(build):
	return not "file" in build.config["modules"]

@predicate
def ios_icon_prerendered(build):
	return "icons" in build.config["modules"] and \
		"ios" in build.config["modules"]["icons"] and \
		"prerendered" in build.config["modules"]["icons"]["ios"] and \
		build.config["modules"]["icons"]["ios"]["prerendered"]

@predicate
def ios_has_minimum_version(build):
	return "requirements" in build.config["modules"] and \
		"ios" in build.config["modules"]["requirements"] and \
		"minimum_version" in build.config["modules"]["requirements"]["ios"]

@predicate
def android_has_minimum_version(build):
	return "requirements" in build.config["modules"] and \
		"android" in build.config["modules"]["requirements"] and \
		"minimum_version" in build.config["modules"]["requirements"]["android"]

@predicate
def module_payments_enabled(build):
	return "payments" in build.config["modules"]

@predicate
def module_payments_disabled(build):
	return not module_payments_enabled(build)
