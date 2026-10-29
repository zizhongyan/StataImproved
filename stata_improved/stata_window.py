"""Windows: type a command into Stata's Command window with window messages.

This does not use Stata Automation (COM) on purpose: a Stata that an
Automation client is attached to exits as soon as the client lets go of it
(e.g. when Sublime Text exits), even when the user opened it and has unsaved
data. Window messages leave Stata's lifetime alone.

The Command window is a Scintilla control in a docking pane of Stata's main
window. The command is sent to it as Esc (Stata clears the Command window),
WM_CHAR per UTF-16 unit, and Enter. Stata does not need the focus and may be
busy: commands then queue up like typed ones. Checked with Stata 18 only.
The Do-file Editor is a separate top-level window that also holds a
Scintilla; it is never used.

The messages are sent with SendMessageTimeout, not posted: measured with
Stata 18, input posted to a MINIMIZED Stata is dropped after the first
command (1 of 12 commands ran), while it is delivered reliably when sent
(12 of 12); for a normal window both ways work (12 of 12).
"""

import ctypes
import os
import re
import subprocess
import time
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
_user32.EnumChildWindows.argtypes = [wintypes.HWND, _WNDENUMPROC, wintypes.LPARAM]
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.GetParent.argtypes = [wintypes.HWND]
_user32.GetParent.restype = wintypes.HWND
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetAncestor.restype = wintypes.HWND
_user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
	wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
_user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t
_user32.WaitForInputIdle.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_user32.WaitForInputIdle.restype = wintypes.DWORD
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
_kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE


class _PROCESSENTRY32W(ctypes.Structure):
	_fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
		("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
		("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
		("szExeFile", ctypes.c_wchar * 260)]


_kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
_kernel32.Process32FirstW.restype = wintypes.BOOL
_kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
_kernel32.Process32NextW.restype = wintypes.BOOL

WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x0100, 0x0101, 0x0102
VK_RETURN, VK_ESCAPE = 0x0D, 0x1B
SCI_GETREADONLY = 2140
_SMTO_ABORTIFHUNG = 0x0002
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_SYNCHRONIZE = 0x00100000
_CREATE_BREAKAWAY_FROM_JOB = 0x01000000
_TH32CS_SNAPPROCESS = 0x00000002
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_ERROR_ACCESS_DENIED = 5
_ERROR_ELEVATION_REQUIRED = 740
_ERROR_NOT_ENOUGH_QUOTA = 1816
_ERROR_TIMEOUT = 1460
_SEND_TIMEOUT_MS = 3000
_GA_ROOT = 2

EXECUTABLE = re.compile(r"^Stata(MP|SE|BE|IC)?(-64)?\.exe$", re.IGNORECASE)

# Stata processes started here: they are meant to outlive the plugin, and are
# never waited for.
_started = []


class StataWindowError(Exception):
	pass


def _class_name(hwnd):
	buffer = ctypes.create_unicode_buffer(256)
	_user32.GetClassNameW(hwnd, buffer, 256)
	return buffer.value


def _process_id(hwnd):
	pid = wintypes.DWORD()
	_user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
	return pid.value


def stata_pids():
	"""Process ids of all running Stata processes, whatever their window state.

	Toolhelp needs no process handle, so this also sees a Stata that runs with
	administrator rights."""
	snapshot = _kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
	if snapshot is None or snapshot == _INVALID_HANDLE:
		return set()
	try:
		entry = _PROCESSENTRY32W()
		entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
		found = set()
		more = _kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
		while more:
			if EXECUTABLE.match(entry.szExeFile):
				found.add(entry.th32ProcessID)
			more = _kernel32.Process32NextW(snapshot, ctypes.byref(entry))
		return found
	finally:
		_kernel32.CloseHandle(snapshot)


def _children(hwnd):
	found = []

	def collect(child, _):
		found.append(child)
		return True
	_user32.EnumChildWindows(hwnd, _WNDENUMPROC(collect), 0)
	return found


def _in_docking_pane(hwnd):
	parent = _user32.GetParent(hwnd)
	while parent:
		if _class_name(parent).startswith("XTPDockingPane"):
			return True
		parent = _user32.GetParent(parent)
	return False


def _is_writable(hwnd):
	"""False only for a Scintilla that answers that it is read-only. Stata 18's
	Command window answers 0, idle and busy. A control that does not answer
	(busy or hung) is not excluded: its input queues up anyway."""
	readonly = ctypes.c_size_t()
	if not _user32.SendMessageTimeoutW(hwnd, SCI_GETREADONLY, 0, 0, _SMTO_ABORTIFHUNG, 200, ctypes.byref(readonly)):
		return True
	return readonly.value == 0


def pick_command_window(candidates):
	"""The Command window among the Scintilla controls of one top-level Stata
	window, given as (hwnd, usable) pairs: usable means a writable control in a
	docking pane. The Do-file Editor (its own top-level window, also
	Scintilla) is not, and must never receive the command."""
	for hwnd, usable in candidates:
		if usable:
			return hwnd
	return None


def stata_windows():
	"""(pid, Command window or None) for each running Stata that has a visible
	window, topmost first. EnumWindows lists top-level windows in z-order, so
	this is the Stata used last; a minimized Stata comes after the others."""
	pids = stata_pids()
	if not pids:
		return []
	order = []
	command_window = {}

	def visit(hwnd, _):
		try:
			if _user32.IsWindowVisible(hwnd):
				pid = _process_id(hwnd)
				if pid in pids:
					if pid not in command_window:
						order.append(pid)
						command_window[pid] = None
					if command_window[pid] is None:
						command_window[pid] = pick_command_window([
							(child, _in_docking_pane(child) and _is_writable(child))
							for child in _children(hwnd) if _class_name(child) == "Scintilla"])
		except Exception:
			pass  # an exception must never reach the native enumeration loop
		return True
	_user32.EnumWindows(_WNDENUMPROC(visit), 0)
	return [(pid, command_window[pid]) for pid in order]


def char_codes(text):
	"""UTF-16 code units, as WM_CHAR expects them (surrogate pairs split)."""
	data = text.encode("utf-16-le")
	return [data[i] | (data[i + 1] << 8) for i in range(0, len(data), 2)]


def _is_ascii(text):
	return all(ord(char) < 128 for char in text)


def is_minimized(hwnd):
	root = _user32.GetAncestor(hwnd, _GA_ROOT)
	return bool(root and _user32.IsIconic(root))


_QUOTED_FILE = re.compile(r'^(\w+) "(.*)"$')


def ascii_command(command):
	"""Spell `command`, a do/run command with a quoted file name, with ASCII
	characters only.

	A MINIMIZED Stata loses typed non-ASCII characters (measured with Stata 18:
	with a path containing e-acute or Chinese characters 1 of 5 commands ran, with
	an ASCII path 5 of 5; a normal window handles both). So every non-ASCII
	character of the file name becomes a ustrunescape() macro expression that
	Stata expands itself (Stata 14 and later), e.g.
	    do "C:/Users/<two Chinese characters>/x.do"
	becomes
	    do `"C:/Users/`=ustrunescape("\\u5f20\\u4e09")'/x.do"'
	Anything that is not such a command is returned unchanged."""
	match = _QUOTED_FILE.match(command)
	if not match or _is_ascii(command):
		return command
	pieces = []
	pending = []

	def flush():
		if pending:
			escapes = "".join(("\\u%04x" if ord(char) < 0x10000 else "\\U%08x") % ord(char) for char in pending)
			pieces.append("`=ustrunescape(\"%s\")'" % escapes)
			del pending[:]
	for char in match.group(2):
		if ord(char) < 128:
			flush()
			pieces.append(char)
		else:
			pending.append(char)
	flush()
	return "%s `\"%s\"'" % (match.group(1), "".join(pieces))


def _post(hwnd, message, wparam, lparam):
	"""Deliver one message to Stata's Command window; returns 0, or the Windows
	error code if it could not be delivered (see the module docstring for why
	this is SendMessageTimeout and not PostMessage)."""
	result = ctypes.c_size_t()
	ctypes.set_last_error(0)
	if _user32.SendMessageTimeoutW(hwnd, message, wparam, lparam, _SMTO_ABORTIFHUNG, _SEND_TIMEOUT_MS,
			ctypes.byref(result)):
		return 0
	return ctypes.get_last_error() or _ERROR_TIMEOUT


def _post_error_message(error, done, total):
	if error == _ERROR_ACCESS_DENIED:
		return ("Stata runs with administrator rights, so Sublime Text may not send input to it. Start Stata "
			"normally (not as administrator), or run Sublime Text as administrator too.")
	if error == _ERROR_NOT_ENOUGH_QUOTA:
		reason = "Stata's input queue is full (too many commands are waiting; is a dialog open in Stata?)."
	elif error == _ERROR_TIMEOUT:
		reason = "Stata did not respond within %d s (is a dialog open in Stata, or is it hung?)." % (_SEND_TIMEOUT_MS // 1000)
	else:
		reason = "Stata's Command window did not accept the input (Windows error %d)." % error
	if done:
		reason += " The Command window may now hold part of the command: press Esc in it."
	return reason


def type_command(hwnd, command):
	if not _is_ascii(command) and is_minimized(hwnd):
		command = ascii_command(command)
	messages = [(WM_KEYDOWN, VK_ESCAPE, 0x00010001), (WM_KEYUP, VK_ESCAPE, 0xC0010001)]
	messages += [(WM_CHAR, code, 1) for code in char_codes(command)]
	messages += [(WM_KEYDOWN, VK_RETURN, 0x001C0001), (WM_CHAR, VK_RETURN, 0x001C0001),
		(WM_KEYUP, VK_RETURN, 0xC01C0001)]
	for done, (message, wparam, lparam) in enumerate(messages):
		error = _post(hwnd, message, wparam, lparam)
		if error:
			raise StataWindowError(_post_error_message(error, done, len(messages)))


def start(executable, timeout=90):
	"""Start Stata like a user would; return its Command window."""
	deadline = time.time() + timeout
	home = os.path.expanduser("~")
	documents = os.path.join(home, "Documents")
	cwd = documents if os.path.isdir(documents) else home
	try:
		# Keep Stata out of Sublime Text's job object, so it does not end with it.
		process = subprocess.Popen([executable], cwd=cwd, close_fds=True, creationflags=_CREATE_BREAKAWAY_FROM_JOB)
	except OSError as e:
		if getattr(e, "winerror", None) == _ERROR_ELEVATION_REQUIRED:
			raise StataWindowError("Stata (%s) is set to run as administrator, so it cannot be started from "
				"Sublime Text. Start it yourself; the next command goes to it." % executable)
		try:
			process = subprocess.Popen([executable], cwd=cwd, close_fds=True)  # the job forbids breakaway
		except OSError as e2:
			raise StataWindowError("Could not start Stata (%s): %s" % (executable, e2))
	_started.append(process)
	handle = _kernel32.OpenProcess(_SYNCHRONIZE | _PROCESS_QUERY_LIMITED_INFORMATION, False, process.pid)
	if handle:
		_user32.WaitForInputIdle(handle, max(1, int((deadline - time.time()) * 1000)))
		_kernel32.CloseHandle(handle)
	while time.time() < deadline:
		for pid, hwnd in stata_windows():
			if pid == process.pid and hwnd:
				time.sleep(0.5)  # let Stata finish setting up the window
				return hwnd
		if process.poll() is not None:
			raise StataWindowError("Stata exited right after it was started (%s)." % executable)
		time.sleep(0.25)
	raise StataWindowError("Stata was started, but its Command window did not appear within %d s." % timeout)


def send(command, find_executable, wait=20):
	"""Type `command` into the Command window of the Stata that was used last;
	start Stata first (the executable comes from `find_executable()`) if none
	is running.

	A Stata that is still starting (a process without a Command window yet) is
	waited for up to `wait` seconds rather than answered with a second Stata."""
	deadline = time.time() + wait
	while True:
		windows = stata_windows()
		for _, hwnd in windows:
			if hwnd:
				type_command(hwnd, command)
				return
		if not stata_pids():
			break
		if time.time() >= deadline:
			if windows:
				raise StataWindowError("Stata is running, but its Command window was not found. Only Stata 18 "
					"has been verified; another version may lay out its window differently. As a fallback "
					"set \"windows_method\": \"automation\" in the settings (read the caveat about it in the "
					"README first: Stata then closes when Sublime Text lets go of it).")
			break  # only Stata processes without any window (e.g. batch mode): start an interactive one
		time.sleep(0.25)
	executable = find_executable()
	if not executable:
		raise StataWindowError("No running Stata was found and no Stata executable to start. Start Stata, "
			"or set \"stata_path\" in the settings.")
	type_command(start(executable), command)
