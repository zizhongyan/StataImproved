"""Platform independent execution API: turn code into a do-file and hand it to
the backend for the current platform."""

import os
import tempfile
import time

import sublime

SETTINGS_FILE = "StataImproved.sublime-settings"

# Do-files are sent asynchronously, so a file must outlive the call that
# queued it; files older than this are removed on the next write.
_MAX_TEMP_AGE = 24 * 60 * 60

# Fixed-name files written by versions <= 1.3.x next to (not inside) the
# temp directory, see issue #39.
_LEGACY_TEMP_FILES = ("BLOCK_piupiu.do", "selectedlines_piupiu.do", "HELP_piupiu.do", "BROWSE_piupiu.do")

_backend = None


def settings():
	return sublime.load_settings(SETTINGS_FILE)


def report_error(message):
	"""Show an error to the user; safe to call from any thread."""
	print("Stata Improved Editor: " + message)
	sublime.set_timeout(lambda: sublime.error_message("Stata Improved Editor\n\n" + message), 0)


def temp_dir():
	directory = settings().get("temp_directory") or os.path.join(tempfile.gettempdir(), "StataImproved")
	directory = os.path.expanduser(directory)
	if not os.path.isdir(directory):
		os.makedirs(directory)
	return directory


def write_do_file(code, kind):
	"""Write `code` to a new do-file and return its path.

	Every call gets its own file: commands are queued in Stata, so reusing one
	file would let a later selection overwrite one that has not run yet.
	"""
	directory = temp_dir()
	_remove_old_files(directory)
	fd, path = tempfile.mkstemp(prefix=kind + "_", suffix=".do", dir=directory)
	with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
		out.write(code)
	return path


def _remove_old_files(directory):
	cutoff = time.time() - _MAX_TEMP_AGE
	for name in os.listdir(directory):
		path = os.path.join(directory, name)
		try:
			if name.endswith(".do") and os.path.getmtime(path) < cutoff:
				os.remove(path)
		except OSError:
			pass


def remove_legacy_files():
	base = tempfile.gettempdir()
	for name in _LEGACY_TEMP_FILES:
		try:
			os.remove(base + name)
		except OSError:
			pass


def stata_path_argument(path):
	"""Quote a file path for use in a Stata command.

	Forward slashes work on every platform and avoid Stata treating a
	backslash before ` or $ as an escape character.
	"""
	return '"' + path.replace("\\", "/") + '"'


def backend():
	global _backend
	if _backend is None:
		platform = sublime.platform()
		if platform == "osx":
			from .backend_macos import MacBackend
			_backend = MacBackend(settings, report_error)
		elif platform == "windows":
			from .backend_windows import WindowsBackend
			_backend = WindowsBackend(settings, report_error)
		else:
			raise UnsupportedPlatform(platform)
	return _backend


def shutdown():
	global _backend
	if _backend is not None:
		_backend.close()
		_backend = None


class UnsupportedPlatform(Exception):
	pass


def execute(code, kind="selection", mode="do", activate=False, cwd=None):
	"""Write `code` to a do-file and let Stata `do` (or `run`) it.

	With the "cd_to_file_directory" setting, `cwd` (the folder of the file being
	edited) becomes Stata's working directory first (issue #20). With
	"local_macros_persist" the file is `include`d instead of `do`ne, so local
	macros survive from one send to the next (issue #3).
	"""
	if cwd and settings().get("cd_to_file_directory", False):
		code = "cd " + stata_path_argument(cwd) + "\n" + code
	try:
		path = write_do_file(code, kind)
	except OSError as e:
		report_error("Could not write the temporary do-file (see the \"temp_directory\" setting):\n%s" % e)
		return
	if settings().get("local_macros_persist", False):
		mode = "include" if mode == "do" else "quietly include"
	command = mode + " " + stata_path_argument(path)
	try:
		backend().send(command, activate=activate)
	except UnsupportedPlatform as e:
		report_error("Sending code to Stata is supported on macOS and Windows, not on %s yet." % e.args[0])
