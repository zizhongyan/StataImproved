"""Windows backend.

Two ways to reach Stata, chosen with the "windows_method" setting:

"window" (default): type the command into Stata's Command window with
window messages (see stata_window.py). Needs no setup, and Stata's lifetime
stays independent of Sublime Text. If no Stata is running, one is started.

"automation": Stata Automation (COM). Needs `StataXX.exe /Register` once
(as administrator). Caveat, measured with Stata 18: a Stata that an
Automation client is attached to exits as soon as the client releases it,
even one the user opened, without asking to save data; if Sublime Text exits
without releasing, Windows releases it about ten minutes later. Automation
is also a single-use server: every new object is a new Stata. So the object
is created once and kept on one dedicated thread (COM objects created in a
single-threaded apartment must be used from that thread), and the thread
outlives plugin reloads.
"""

import glob
import os
import queue
import re
import sys
import threading
import time
import types

import sublime

from . import stata_window, wincom

DEFAULT_PROGID = "stata.StataOLEApp"

# Survives plugin reloads (sys.modules is shared by the whole plugin_host).
# Job tuples (progid, command, report_error) are the contract between a
# running thread and newer plugin code, so keep that shape stable.
_HOLDER = "_stata_improved_windows_automation"

_EXECUTABLE = re.compile(r"^Stata(MP|SE|BE|IC)?(-64)?\.exe$", re.IGNORECASE)


class WindowsBackend(object):
	def __init__(self, settings, report_error):
		self._settings = settings
		self._report_error = report_error
		self._window_jobs = queue.Queue()
		self._window_thread = threading.Thread(target=self._window_worker, name="StataImproved-Window")
		self._window_thread.daemon = True
		self._window_thread.start()

	def send(self, command, activate=False):
		# `activate` is not supported: Windows does not let a background
		# process bring another application to the foreground reliably.
		if self._settings().get("windows_method", "window") == "automation":
			progid = self._settings().get("windows_progid") or DEFAULT_PROGID
			_automation_jobs().put((progid, command, self._report_error))
		else:
			self._window_jobs.put(command)

	def close(self):
		self._window_jobs.put(None)
		# The automation thread (if any) and the Stata it drives are kept on
		# purpose; see _HOLDER.

	def _window_worker(self):
		while True:
			command = self._window_jobs.get()
			if command is None:
				return
			try:
				stata_window.send(command, self._executable_to_start)
			except stata_window.StataWindowError as e:
				self._report_error(str(e))
			except Exception as e:
				self._report_error("Could not send the command to Stata:\n%s" % e)

	def _executable_to_start(self):
		sublime.set_timeout(lambda: sublime.status_message("Stata Improved Editor: starting Stata..."), 0)
		configured = self._settings().get("stata_path", "")
		executables = find_stata_executables(configured)
		if configured and not executables:
			raise stata_window.StataWindowError("\"stata_path\" in the settings does not point to an existing "
				"file: %s" % expand_path(configured))
		return executables[0] if executables else None


# --- "automation" method ------------------------------------------------------

def _automation_jobs():
	holder = sys.modules.get(_HOLDER)
	if holder is None or not holder.thread.is_alive():
		holder = types.ModuleType(_HOLDER)
		holder.jobs = queue.Queue()
		holder.thread = threading.Thread(target=_worker, args=(holder.jobs,), name="StataImproved-Automation")
		holder.thread.daemon = True
		holder.thread.start()
		sys.modules[_HOLDER] = holder
	return holder.jobs


def _worker(jobs):
	try:
		wincom.initialize()
	except wincom.COMError as e:
		print("Stata Improved Editor: CoInitializeEx: %s" % e)  # later calls report the real problem
	stata = None
	while True:
		progid, command, report_error = jobs.get()
		try:
			stata = _send(stata, progid, command)
		except wincom.COMError as e:
			report_error(_explain(e, progid))
		except Exception as e:
			report_error("Could not send the command to Stata:\n%s" % e)


def _send(stata, progid, command):
	if stata is not None:
		try:
			stata.call("DoCommandAsync", command)
			return stata
		except wincom.COMError as e:
			if e.hresult not in wincom.DISCONNECTED:
				raise
			# Stata was closed: connect to (or start) a new one below.
			try:
				stata.release()
			except (wincom.COMError, OSError):
				pass
	sublime.set_timeout(lambda: sublime.status_message("Stata Improved Editor: connecting to Stata..."), 0)
	stata = wincom.Dispatch(progid)
	_wait_until_ready(stata)
	stata.call("DoCommandAsync", command)
	return stata


def _wait_until_ready(stata, timeout=60):
	"""Wait until a freshly created Stata can take commands.

	A command sent right after the Automation object was created is silently
	dropped while Stata is still starting up (measured with Stata 18: lost
	every time, no error). UtilStataErrorCode is answered by Stata's main
	thread, so it only returns once Stata is ready (0.3 s), and it only reads
	_rc. Sending a synchronous command instead fails with RPC_E_SERVERFAULT,
	and polling UtilIsStataFree is not reliable."""
	deadline = time.time() + timeout
	while True:
		try:
			stata.call("UtilStataErrorCode")
			return
		except wincom.COMError:
			if time.time() >= deadline:
				raise
			time.sleep(0.2)


def _explain(error, progid):
	if error.hresult in wincom.NOT_REGISTERED:
		return ("Stata Automation (%s) is not registered on this computer.\n\n"
			"Run \"Stata Improved: Register Stata Automation (Windows, optional)\" from the Command Palette, "
			"or run your Stata executable with /Register from an administrator Command Prompt, e.g.\n\n"
			"\"C:\\Program Files\\Stata19\\StataMP-64.exe\" /Register\n\n"
			"Then send the code again. (Or remove \"windows_method\": \"automation\" from the settings.)") % progid
	if error.hresult == wincom.RPC_E_CALL_REJECTED:
		return "Stata is busy and rejected the command (is a dialog open in Stata?).\n\n%s" % error
	return "Could not send the command to Stata:\n%s" % error


# --- Stata executables -----------------------------------------------------------

def expand_path(path):
	"""A path from the settings, with ~ and %VARIABLES% expanded."""
	return os.path.expandvars(os.path.expanduser(path))


def find_stata_executables(configured=""):
	"""Stata executables on this computer, newest version first."""
	if configured:
		configured = expand_path(configured)
		return [configured] if os.path.isfile(configured) else []
	roots = set()
	for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
		if os.environ.get(variable):
			roots.add(os.environ[variable])
	roots.add(os.environ.get("SystemDrive", "C:") + "\\")
	found = set()
	for root in roots:
		for path in glob.glob(os.path.join(root, "Stata*", "*.exe")):
			if _EXECUTABLE.match(os.path.basename(path)):
				found.add(os.path.normcase(os.path.abspath(path)))

	def version(path):
		digits = re.findall(r"\d+", os.path.basename(os.path.dirname(path)))
		return int(digits[0]) if digits else 0
	return sorted(found, key=lambda path: (-version(path), path))


def register(executable):
	"""Run `executable /Register` elevated; Windows shows a UAC prompt.

	Returns False if it could not be started (e.g. the prompt was declined).
	"""
	import ctypes
	shell32 = ctypes.WinDLL("shell32")
	shell32.ShellExecuteW.restype = ctypes.c_void_p
	shell32.ShellExecuteW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
		ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
	result = shell32.ShellExecuteW(None, "runas", executable, "/Register", os.path.dirname(executable), 0)
	return (result or 0) > 32


def is_registered(progid=DEFAULT_PROGID):
	return wincom.is_registered(progid)
