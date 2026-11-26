import ctypes
import os
import re
import subprocess
import shutil
import sys
import tempfile
import threading
import time
import unittest

from fake_sublime import load_plugin, support


@unittest.skipUnless(sys.platform == "win32", "Windows only")
class WinComTest(unittest.TestCase):
	"""The ctypes IDispatch client against Automation objects every Windows has."""

	@classmethod
	def setUpClass(cls):
		load_plugin()
		cls.wincom = support("wincom")
		cls.wincom.initialize()

	def test_arguments_and_results_round_trip(self):
		d = self.wincom.Dispatch("Scripting.Dictionary")
		try:
			values = {"s": "é 中文 😀", "i": 42, "f": 2.5, "t": True, "empty": ""}
			for key, value in values.items():
				d.call("Add", key, value)
			self.assertEqual(d.call("Count"), len(values))
			for key, value in values.items():
				self.assertEqual(d.call("Item", key), value)
			self.assertIs(d.call("Exists", "missing"), False)
		finally:
			d.release()

	def test_errors(self):
		d = self.wincom.Dispatch("Scripting.Dictionary")
		d.call("Add", "k", 1)
		with self.assertRaises(self.wincom.COMError):
			d.call("Add", "k", 2)  # duplicate key: DISP_E_EXCEPTION
		with self.assertRaises(self.wincom.COMError) as unknown:
			d.call("NoSuchMethod")
		self.assertEqual(unknown.exception.hresult, 0x80020006)  # DISP_E_UNKNOWNNAME
		d.release()
		with self.assertRaises(ValueError):
			d.call("Count")

	def test_unknown_progid_is_not_registered(self):
		with self.assertRaises(self.wincom.COMError) as error:
			self.wincom.Dispatch("StataImproved.DoesNotExist")
		self.assertIn(error.exception.hresult, self.wincom.NOT_REGISTERED)
		self.assertFalse(self.wincom.is_registered("StataImproved.DoesNotExist"))
		self.assertTrue(self.wincom.is_registered("Scripting.Dictionary"))

	def test_many_calls(self):
		d = self.wincom.Dispatch("Scripting.Dictionary")
		for i in range(5000):
			d.call("Add", "key%d" % i, "v" * 100)
		self.assertEqual(d.call("Count"), 5000)
		d.release()


AUTOMATION = {"windows_method": "automation"}


class FakeStata(object):
	"""Stands in for wincom.Dispatch("stata.StataOLEApp")."""
	instances = []
	not_ready_probes = 0  # UtilStataErrorCode fails this many times first (Stata still starting)

	def __init__(self, progid):
		self.progid = progid
		self.commands = []
		self.closed = False
		self.probes = 0
		FakeStata.instances.append(self)

	def call(self, name, *args):
		if self.closed:
			raise FakeStata.wincom.COMError(0x800706BA, "RPC server unavailable")
		if name == "UtilStataErrorCode":  # the readiness probe; not a command
			self.probes += 1
			if self.probes <= self.not_ready_probes:
				raise FakeStata.wincom.COMError(0x80010105, "server fault")
			return 0
		self.commands.append((name,) + args)

	def release(self):
		self.released = True


@unittest.skipUnless(sys.platform == "win32", "Windows only")
class WindowsBackendTest(unittest.TestCase):
	def setUp(self):
		load_plugin()
		self.windows = support("backend_windows")
		self.wincom = support("wincom")
		FakeStata.wincom = self.wincom
		FakeStata.instances = []
		self.real_dispatch = self.wincom.Dispatch
		self.wincom.Dispatch = FakeStata
		sys.modules.pop(self.windows._HOLDER, None)

	def tearDown(self):
		self.wincom.Dispatch = self.real_dispatch
		sys.modules.pop(self.windows._HOLDER, None)

	def test_one_stata_is_reused(self):
		stata = self.windows._send(None, "stata.StataOLEApp", 'do "a.do"')
		self.assertIs(self.windows._send(stata, "stata.StataOLEApp", 'do "b.do"'), stata)
		self.assertEqual(len(FakeStata.instances), 1)
		self.assertEqual(stata.commands, [("DoCommandAsync", 'do "a.do"'), ("DoCommandAsync", 'do "b.do"')])

	def test_reconnects_after_stata_was_closed(self):
		stata = self.windows._send(None, "stata.StataOLEApp", "sum")
		stata.closed = True
		new = self.windows._send(stata, "stata.StataOLEApp", "sum")
		self.assertIsNot(new, stata)
		self.assertTrue(stata.released)
		self.assertEqual(new.commands, [("DoCommandAsync", "sum")])

	def test_other_errors_are_raised(self):
		class Busy(FakeStata):
			def call(self, name, *args):
				raise FakeStata.wincom.COMError(self.wincom.RPC_E_CALL_REJECTED, "busy")
		Busy.wincom = self.wincom
		with self.assertRaises(self.wincom.COMError) as error:
			self.windows._send(Busy("x"), "stata.StataOLEApp", "sum")
		self.assertIn("busy", self.windows._explain(error.exception, "stata.StataOLEApp"))

	def test_command_is_sent_only_after_stata_answers(self):
		# A command sent while Stata is still starting is silently dropped.
		class Slow(FakeStata):
			not_ready_probes = 3
		Slow.wincom = self.wincom
		self.wincom.Dispatch = Slow
		stata = self.windows._send(None, "stata.StataOLEApp", "sum")
		self.assertEqual(stata.probes, 4)
		self.assertEqual(stata.commands, [("DoCommandAsync", "sum")])

	def test_waiting_for_a_stata_that_never_answers_gives_up(self):
		class Never(FakeStata):
			not_ready_probes = 10 ** 9
		Never.wincom = self.wincom
		with self.assertRaises(self.wincom.COMError):
			self.windows._wait_until_ready(Never("x"), timeout=0.5)

	def test_not_registered_message_explains_setup(self):
		error = self.wincom.COMError(0x80040154, "Class not registered")
		message = self.windows._explain(error, "stata.StataOLEApp")
		self.assertIn("Register Stata Automation", message)
		self.assertIn("/Register", message)

	def test_worker_thread_sends_in_order_and_survives_reload(self):
		done = threading.Event()

		class Recording(FakeStata):
			def call(self, name, *args):
				FakeStata.call(self, name, *args)
				if args == ("last",):
					done.set()
		self.wincom.Dispatch = Recording
		errors = []
		backend = self.windows.WindowsBackend(lambda: AUTOMATION, errors.append)
		backend.send("first")
		# A plugin reload creates a new backend object; it must reuse the thread
		# (and so the same Stata).
		again = self.windows.WindowsBackend(lambda: AUTOMATION, errors.append)
		self.assertIs(self.windows._automation_jobs(), self.windows._automation_jobs())
		again.send("second")
		again.send("last")
		self.assertTrue(done.wait(10))
		self.assertEqual(errors, [])
		self.assertEqual(len(FakeStata.instances), 1)
		self.assertEqual([c[1] for c in FakeStata.instances[0].commands], ["first", "second", "last"])

	def test_worker_reports_errors(self):
		def not_registered(progid):
			raise self.wincom.COMError(0x800401F3, "Invalid class string")
		self.wincom.Dispatch = not_registered
		reported = threading.Event()
		errors = []

		def report(message):
			errors.append(message)
			reported.set()
		backend = self.windows.WindowsBackend(lambda: AUTOMATION, report)
		backend.send("sum")
		self.assertTrue(reported.wait(10))
		self.assertIn("not registered", errors[0])

	def test_find_stata_executables(self):
		root = tempfile.mkdtemp()
		try:
			for rel in ("Stata17\\StataSE-64.exe", "Stata19\\StataMP-64.exe", "Stata19\\unins000.exe",
					"Stata18\\StataBE-64.exe", "Other\\StataMP-64.exe"):
				path = os.path.join(root, rel)
				os.makedirs(os.path.dirname(path), exist_ok=True)
				open(path, "w").close()
			saved = dict(os.environ)
			try:
				for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
					os.environ.pop(variable, None)
				os.environ["ProgramFiles"] = root
				os.environ["SystemDrive"] = root
				found = [os.path.relpath(p, os.path.normcase(root)) for p in self.windows.find_stata_executables()]
			finally:
				os.environ.clear()
				os.environ.update(saved)
			self.assertEqual(found, [os.path.normcase(p) for p in
				("Stata19\\StataMP-64.exe", "Stata18\\StataBE-64.exe", "Stata17\\StataSE-64.exe")])
			configured = os.path.join(root, "Stata17", "StataSE-64.exe")
			self.assertEqual(self.windows.find_stata_executables(configured), [configured])
			self.assertEqual(self.windows.find_stata_executables(configured + ".missing"), [])
		finally:
			shutil.rmtree(root)


@unittest.skipUnless(sys.platform == "win32", "Windows only")
class WindowMethodTest(unittest.TestCase):
	def setUp(self):
		load_plugin()
		self.windows = support("backend_windows")
		self.stata_window = support("stata_window")

	def test_default_method_types_into_stata(self):
		sent = []
		done = threading.Event()

		def fake_send(command, find_executable):
			sent.append((command, find_executable()))
			done.set()
		self.stata_window.send = fake_send
		settings = {"stata_path": sys.executable}
		backend = self.windows.WindowsBackend(lambda: settings, self.fail)
		backend.send('do "a.do"')
		self.assertTrue(done.wait(10))
		backend.close()
		self.assertEqual(sent, [('do "a.do"', sys.executable)])

	def test_window_errors_are_reported(self):
		reported = threading.Event()
		errors = []

		def fail(command, find_executable):
			raise self.stata_window.StataWindowError("no Command window")
		self.stata_window.send = fail

		def report(message):
			errors.append(message)
			reported.set()
		backend = self.windows.WindowsBackend(lambda: {}, report)
		backend.send("sum")
		self.assertTrue(reported.wait(10))
		backend.close()
		self.assertEqual(errors, ["no Command window"])

	def test_command_window_is_the_docked_scintilla_never_the_do_file_editor(self):
		pick = self.stata_window.pick_command_window
		self.assertEqual(pick([(1, False), (2, True)]), 2)
		self.assertIsNone(pick([(1, False)]))  # the Do-file Editor's own window
		self.assertIsNone(pick([]))

	def test_char_codes_are_utf16_units(self):
		self.assertEqual(self.stata_window.char_codes('do "é"'), [100, 111, 32, 34, 0xE9, 34])
		self.assertEqual(self.stata_window.char_codes("\U0001F600"), [0xD83D, 0xDE00])

	# --- a minimized Stata loses typed non-ASCII characters ---

	def test_ascii_command_leaves_ascii_alone(self):
		ascii_command = self.stata_window.ascii_command
		self.assertEqual(ascii_command('do "C:/a b/x.do"'), 'do "C:/a b/x.do"')
		self.assertEqual(ascii_command("help \u00e9"), "help \u00e9")  # not a quoted file name: unchanged

	def test_ascii_command_spells_non_ascii_with_ustrunescape(self):
		ascii_command = self.stata_window.ascii_command
		self.assertEqual(ascii_command('do "C:/Users/\u5f20\u4e09/x.do"'),
			'do `"C:/Users/`=ustrunescape("\\u5f20\\u4e09")\'/x.do"\'')
		self.assertEqual(ascii_command('run "d/\u00e9a/\U0001F600.do"'),
			'run `"d/`=ustrunescape("\\u00e9")\'a/`=ustrunescape("\\U0001f600")\'.do"\'')
		for command in ('do "C:/Users/\u5f20\u4e09/x.do"', 'run "\u00e9/\U0001F600.do"'):
			self.assertTrue(all(ord(c) < 128 for c in ascii_command(command)))

	def typed_text(self, minimized, command):
		sw = self.stata_window
		typed = []
		sw.is_minimized = lambda hwnd: minimized
		sw._post = lambda hwnd, message, wparam, lparam: typed.append((message, wparam)) or 0
		sw.type_command(1, command)
		units = [wparam for message, wparam in typed if message == sw.WM_CHAR and wparam != sw.VK_RETURN]
		return bytes(bytearray(b for unit in units for b in (unit & 0xFF, unit >> 8))).decode("utf-16-le")

	def test_a_minimized_stata_is_only_typed_ascii(self):
		command = 'do "C:/Users/\u5f20\u4e09/x.do"'
		self.assertEqual(self.typed_text(True, command), self.stata_window.ascii_command(command))
		self.assertTrue(all(ord(c) < 128 for c in self.typed_text(True, command)))

	def test_a_normal_stata_is_typed_the_command_as_it_is(self):
		command = 'do "C:/Users/\u5f20\u4e09/x.do"'
		self.assertEqual(self.typed_text(False, command), command)

	# --- send(): which Stata gets the command, and when a new one is started ---

	def scenario(self, windows, pids, executable="C:/Stata/StataMP-64.exe", wait=0.3):
		"""Run stata_window.send() with scripted lookups; `windows` and `pids` are
		lists of successive answers (the last one repeats)."""
		sw = self.stata_window
		calls = {"typed": [], "started": []}
		answers = {"windows": list(windows), "pids": list(pids)}

		def next_answer(key):
			values = answers[key]
			return values.pop(0) if len(values) > 1 else values[0]
		sw.stata_windows = lambda: next_answer("windows")
		sw.stata_pids = lambda: next_answer("pids")
		sw.type_command = lambda hwnd, command: calls["typed"].append((hwnd, command))
		sw.start = lambda path: calls["started"].append(path) or 999
		try:
			sw.send("sum", lambda: executable, wait=wait)
			calls["error"] = None
		except sw.StataWindowError as e:
			calls["error"] = str(e)
		return calls

	def test_send_uses_the_topmost_stata_that_has_a_command_window(self):
		calls = self.scenario([[(10, None), (20, 200), (30, 300)]], [{10, 20, 30}])
		self.assertEqual(calls["typed"], [(200, "sum")])
		self.assertEqual(calls["started"], [])

	def test_send_starts_stata_when_none_runs(self):
		calls = self.scenario([[]], [set()])
		self.assertEqual(calls["started"], ["C:/Stata/StataMP-64.exe"])
		self.assertEqual(calls["typed"], [(999, "sum")])

	def test_send_waits_for_a_stata_that_is_still_starting(self):
		# The process exists but has no window yet: no second Stata must be started.
		calls = self.scenario([[], [], [(10, 100)]], [{10}])
		self.assertEqual(calls["started"], [])
		self.assertEqual(calls["typed"], [(100, "sum")])

	def test_send_waits_for_the_splash_window_to_get_a_command_window(self):
		calls = self.scenario([[(10, None)], [(10, None)], [(10, 100)]], [{10}])
		self.assertEqual(calls["started"], [])
		self.assertEqual(calls["typed"], [(100, "sum")])

	def test_send_starts_stata_when_only_windowless_processes_run(self):
		# e.g. a batch-mode Stata: no interactive Stata to type into.
		calls = self.scenario([[]], [{10}])
		self.assertEqual(calls["started"], ["C:/Stata/StataMP-64.exe"])

	def test_send_reports_a_stata_without_command_window(self):
		calls = self.scenario([[(10, None)]], [{10}])
		self.assertEqual(calls["started"], [])
		self.assertEqual(calls["typed"], [])
		self.assertIn("Command window was not found", calls["error"])
		self.assertIn("caveat", calls["error"])  # the automation fallback comes with its warning

	def test_send_without_executable_explains_stata_path(self):
		calls = self.scenario([[]], [set()], executable=None)
		self.assertIn("stata_path", calls["error"])
		self.assertEqual(calls["started"], [])

	def test_input_errors_are_explained(self):
		message = self.stata_window._post_error_message
		self.assertIn("administrator", message(5, 0, 100))
		self.assertIn("queue is full", message(1816, 50, 100))
		self.assertIn("Esc", message(1816, 50, 100))   # partial text may be left behind
		self.assertNotIn("Esc", message(1400, 0, 100))
		self.assertIn("error 1400", message(1400, 0, 100))

	def test_type_command_stops_at_the_first_failed_message(self):
		sw = self.stata_window
		posted = []

		def post(hwnd, message, wparam, lparam):
			posted.append((message, wparam))
			return 5 if len(posted) == 3 else 0
		sw._post = post
		with self.assertRaises(sw.StataWindowError) as error:
			sw.type_command(1, "sum")
		self.assertEqual(len(posted), 3)
		self.assertIn("administrator", str(error.exception))

	def test_process_listing_sees_processes_without_opening_them(self):
		sw = self.stata_window
		sw.EXECUTABLE = re.compile(r"^python.*\.exe$", re.IGNORECASE)
		self.assertIn(os.getpid(), sw.stata_pids())
		sw.EXECUTABLE = re.compile(r"^definitely-not-running\.exe$", re.IGNORECASE)
		self.assertEqual(sw.stata_pids(), set())

	def test_stata_path_setting_expands_variables_and_is_checked(self):
		os.environ["SI_TEST_STATA_DIR"] = os.path.dirname(sys.executable)
		path = "%SI_TEST_STATA_DIR%\\" + os.path.basename(sys.executable)
		self.assertEqual(self.windows.find_stata_executables(path), [self.windows.expand_path(path)])
		self.assertEqual(self.windows.find_stata_executables(path + ".missing"), [])
		errors = []
		reported = threading.Event()
		self.stata_window.send = lambda command, find_executable: find_executable()
		backend = self.windows.WindowsBackend(lambda: {"stata_path": path + ".missing"},
			lambda message: (errors.append(message), reported.set()))
		backend.send("sum")
		self.assertTrue(reported.wait(10))
		backend.close()
		self.assertIn("does not point to an existing file", errors[0])
		self.assertIn(".missing", errors[0])


@unittest.skipUnless(sys.platform == "win32" and os.environ.get("STATA_IMPROVED_REAL_STATA") == "1",
	"set STATA_IMPROVED_REAL_STATA=1 to start the real Stata")
class RealStataTest(unittest.TestCase):
	"""End to end with the Stata installed on this computer: start it, type a
	do-file command (path with a space and non-ASCII), check the do-file ran,
	and close the Stata this test started."""

	def test_do_file_runs_in_real_stata(self):
		load_plugin()
		windows = support("backend_windows")
		stata_window = support("stata_window")
		if stata_window.stata_windows():
			self.skipTest("close Stata first; this test starts its own")
		executables = windows.find_stata_executables()
		if not executables:
			self.skipTest("no Stata installed")
		folder = tempfile.mkdtemp(prefix="stata improved é ")
		marker = os.path.join(folder, "ran.txt")
		dofile = os.path.join(folder, "probe é.do")
		with open(dofile, "w", encoding="utf-8", newline="\n") as f:
			f.write('file open fh using "%s", write replace\nfile write fh "ran"\nfile close fh\n'
				% marker.replace("\\", "/"))
		try:
			stata_window.send('do "%s"' % dofile.replace("\\", "/"), lambda: executables[0])
			for _ in range(60):
				if os.path.exists(marker):
					break
				time.sleep(0.5)
			self.assertTrue(os.path.exists(marker), "the do-file did not run")
			# Now Stata is running: the next command goes to it (nothing is started).
			os.remove(marker)
			stata_window.send('do "%s"' % dofile.replace("\\", "/"), lambda: self.fail("started another Stata"))
			for _ in range(60):
				if os.path.exists(marker):
					break
				time.sleep(0.5)
			self.assertTrue(os.path.exists(marker), "the second do-file did not run")
			self.assertEqual(len(stata_window.stata_windows()), 1)
		finally:
			self.kill_stata(stata_window)
			shutil.rmtree(folder, ignore_errors=True)

	@staticmethod
	def kill_stata(stata_window):
		for pid in stata_window.stata_pids():
			subprocess.call(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		for process in stata_window._started:
			process.wait(30)

	def marker_do(self, folder, name):
		marker = os.path.join(folder, name + ".txt")
		dofile = os.path.join(folder, name + " é.do")
		with open(dofile, "w", encoding="utf-8", newline="\n") as f:
			f.write('file open fh using "%s", write replace\nfile write fh "ran"\nfile close fh\n'
				% marker.replace("\\", "/"))
		return 'do "%s"' % dofile.replace("\\", "/"), marker

	def test_command_sent_while_the_user_is_still_launching_stata_does_not_start_a_second(self):
		load_plugin()
		windows = support("backend_windows")
		stata_window = support("stata_window")
		if stata_window.stata_pids():
			self.skipTest("close Stata first; this test starts its own")
		executables = windows.find_stata_executables()
		if not executables:
			self.skipTest("no Stata installed")
		folder = tempfile.mkdtemp(prefix="stata improved race ")
		command, marker = self.marker_do(folder, "race")
		try:
			launched = subprocess.Popen([executables[0]], cwd=os.path.expanduser("~"))  # the user double-clicks Stata...
			stata_window.send(command, lambda: self.fail("started a second Stata"))  # ...and presses Ctrl+D at once
			for _ in range(60):
				if os.path.exists(marker):
					break
				time.sleep(0.5)
			self.assertTrue(os.path.exists(marker), "the do-file did not run")
			self.assertEqual(len(stata_window.stata_pids()), 1)
		finally:
			self.kill_stata(stata_window)
			launched.wait(30)
			shutil.rmtree(folder, ignore_errors=True)

	def test_a_minimized_stata_runs_consecutive_commands_with_a_non_ascii_path(self):
		# Regression: input to a minimized Stata was lost after the first command
		# when it contained non-ASCII characters, e.g. a Chinese user name in the
		# temp path.
		load_plugin()
		windows = support("backend_windows")
		stata_window = support("stata_window")
		if stata_window.stata_pids():
			self.skipTest("close Stata first; this test starts its own")
		executables = windows.find_stata_executables()
		if not executables:
			self.skipTest("no Stata installed")
		user32 = stata_window._user32
		user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
		folder = tempfile.mkdtemp(prefix="stata improved 中文é ")
		try:
			hwnd = stata_window.start(executables[0])
			time.sleep(1)
			user32.ShowWindow(user32.GetAncestor(hwnd, 2), 6)  # SW_MINIMIZE
			time.sleep(1)
			self.assertTrue(stata_window.is_minimized(hwnd))
			ran = []
			for index in range(4):
				command, marker = self.marker_do(folder, "min%d" % index)
				stata_window.send(command, lambda: self.fail("started another Stata"))
				for _ in range(40):
					if os.path.exists(marker):
						break
					time.sleep(0.25)
				ran.append(os.path.exists(marker))
			self.assertEqual(ran, [True] * 4)
			self.assertTrue(stata_window.is_minimized(hwnd), "Stata must stay minimized")
		finally:
			self.kill_stata(stata_window)
			shutil.rmtree(folder, ignore_errors=True)

	def test_chinese_code_and_path_round_trip_through_the_execution_layer(self):
		# The real chain a user triggers: code -> UTF-8 do-file in a temp folder
		# with a non-ASCII name -> typed into Stata -> executed; the code itself
		# contains non-ASCII text, which must arrive unchanged.
		plugin, sublime = load_plugin()
		execution = support("execution")
		stata_window = support("stata_window")
		if stata_window.stata_pids():
			self.skipTest("close Stata first; this test starts its own")
		if not support("backend_windows").find_stata_executables():
			self.skipTest("no Stata installed")
		folder = tempfile.mkdtemp(prefix="stata improved 中文é ")
		marker = os.path.join(folder, "round trip.txt")
		sublime.settings["temp_directory"] = os.path.join(folder, "临时")
		code = ('file open fh using "%s", write replace\nfile write fh "中文é"\nfile close fh\n'
			% marker.replace("\\", "/"))
		try:
			execution.execute(code, kind="selection")
			for _ in range(120):
				if os.path.exists(marker) and os.path.getsize(marker) > 0:
					break
				time.sleep(0.5)
			self.assertTrue(os.path.exists(marker), "the code did not run; messages: %s" % sublime.messages)
			with open(marker, "rb") as f:
				self.assertEqual(f.read().decode("utf-8"), "中文é")
		finally:
			execution.shutdown()
			self.kill_stata(stata_window)
			shutil.rmtree(folder, ignore_errors=True)

	def test_automation_first_command_is_not_lost(self):
		# Regression: a command sent right after the Automation object was created
		# used to be dropped silently while Stata was still starting.
		load_plugin()
		windows = support("backend_windows")
		stata_window = support("stata_window")
		wincom = support("wincom")
		if not wincom.is_registered(windows.DEFAULT_PROGID):
			self.skipTest("Stata Automation is not registered")
		if stata_window.stata_pids():
			self.skipTest("close Stata first; this test starts its own")
		folder = tempfile.mkdtemp(prefix="stata improved auto ")
		command, marker = self.marker_do(folder, "auto")
		sys.modules.pop(windows._HOLDER, None)
		errors = []
		backend = windows.WindowsBackend(lambda: {"windows_method": "automation"}, errors.append)
		try:
			backend.send(command)
			for _ in range(60):
				if os.path.exists(marker):
					break
				time.sleep(0.5)
			self.assertTrue(os.path.exists(marker), "the first command was lost; errors: %s" % errors)
		finally:
			self.kill_stata(stata_window)
			sys.modules.pop(windows._HOLDER, None)
			shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
	unittest.main()
