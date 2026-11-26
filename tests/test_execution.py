import os
import shutil
import tempfile
import time
import unittest

from fake_sublime import load_plugin, support


class ExecutionTest(unittest.TestCase):
	def setUp(self):
		self.plugin, self.sublime = load_plugin()
		self.execution = support("execution")
		self.tmp = tempfile.mkdtemp(prefix="stata improved test ")  # a space, like many user names
		self.sublime.settings["temp_directory"] = self.tmp

	def tearDown(self):
		shutil.rmtree(self.tmp, ignore_errors=True)

	def test_default_temp_dir_is_inside_system_temp(self):  # issue #39
		del self.sublime.settings["temp_directory"]
		directory = self.execution.temp_dir()
		self.assertEqual(os.path.dirname(directory), tempfile.gettempdir())
		self.assertEqual(os.path.basename(directory), "StataImproved")

	def test_each_do_file_is_new_and_utf8(self):
		first = self.execution.write_do_file("di \"é 中文\"\n", "selection")
		second = self.execution.write_do_file("di 2\n", "selection")
		self.assertNotEqual(first, second)
		self.assertEqual(os.path.dirname(first), self.tmp)
		with open(first, "rb") as f:
			self.assertEqual(f.read(), "di \"é 中文\"\n".encode("utf-8"))

	def test_old_do_files_are_removed(self):
		old = os.path.join(self.tmp, "old.do")
		keep = os.path.join(self.tmp, "notes.txt")
		for path in (old, keep):
			open(path, "w").close()
			os.utime(path, (time.time() - 3 * 86400,) * 2)
		self.execution.write_do_file("di 1\n", "selection")
		self.assertFalse(os.path.exists(old))
		self.assertTrue(os.path.exists(keep))

	def test_path_argument(self):
		self.assertEqual(self.execution.stata_path_argument("C:\\Users\\A B\\x.do"), '"C:/Users/A B/x.do"')
		self.assertEqual(self.execution.stata_path_argument("/var/T/x.do"), '"/var/T/x.do"')

	def test_execute_sends_do_command_to_backend(self):
		sent = []

		class Backend(object):
			def send(self, command, activate=False):
				sent.append((command, activate))
		self.execution._backend = Backend()
		self.execution.execute("sum\n", kind="block", mode="run", activate=True)
		command, activate = sent[0]
		self.assertTrue(command.startswith('run "') and command.endswith('.do"'), command)
		path = command[5:-1]
		self.assertTrue(os.path.basename(path).startswith("block_"))
		with open(path) as f:
			self.assertEqual(f.read(), "sum\n")
		self.assertTrue(activate)

	def _sent_text(self, **kw):
		sent = []

		class Backend(object):
			def send(self, command, activate=False):
				sent.append(command)
		self.execution._backend = Backend()
		self.execution.execute("sum\n", **kw)
		command = sent[0]
		path = command[command.index('"') + 1:-1]
		with open(path) as f:
			return command, f.read()

	def test_cd_to_file_directory(self):  # issue #20
		self.assertEqual(self._sent_text(cwd="/a b/c")[1], "sum\n")
		self.sublime.settings["cd_to_file_directory"] = True
		self.assertEqual(self._sent_text(cwd="/a b/c")[1], 'cd "/a b/c"\nsum\n')
		self.assertEqual(self._sent_text()[1], "sum\n")

	def test_local_macros_persist(self):  # issue #3
		self.sublime.settings["local_macros_persist"] = True
		self.assertTrue(self._sent_text()[0].startswith('include "'))
		self.assertTrue(self._sent_text(mode="run")[0].startswith('quietly include "'))

	def test_unwritable_temp_directory_is_reported(self):
		blocker = os.path.join(self.tmp, "a file")
		open(blocker, "w").close()
		self.sublime.settings["temp_directory"] = os.path.join(blocker, "sub")
		self.execution.execute("sum\n")
		self.assertIn("temp_directory", self.sublime.messages[-1][1])

	def test_unsupported_platform(self):
		self.plugin, self.sublime = load_plugin(platform="linux")
		execution = support("execution")
		self.sublime.settings["temp_directory"] = self.tmp
		execution.execute("sum\n")
		self.assertIn("not on linux", self.sublime.messages[-1][1])

	def test_legacy_files_next_to_temp_dir_are_removed(self):
		legacy = tempfile.gettempdir() + "selectedlines_piupiu.do"
		try:
			open(legacy, "w").close()
		except OSError:
			self.skipTest("parent of the temp directory is not writable")
		self.plugin.plugin_loaded()
		self.assertFalse(os.path.exists(legacy))


class MacBackendTest(unittest.TestCase):
	def setUp(self):
		load_plugin(platform="osx")
		self.macos = support("backend_macos")
		self.settings = {}
		self.errors = []
		self.scripts = []
		self.macos._osascript = self.fake_osascript
		self.newest = 18
		self.backend = self.macos.MacBackend(lambda: self.settings, self.errors.append)

	def tearDown(self):
		self.backend.close()

	def send(self, *args, **kwargs):
		self.backend.send(*args, **kwargs)
		self.backend._jobs.join()

	def fake_osascript(self, script):
		self.scripts.append(script)
		if "return stata" in script:
			return str(self.newest)
		return ""

	def test_newest_version_is_detected_once(self):
		self.send('do "/tmp/a.do"')
		self.send('do "/tmp/b.do"')
		self.assertEqual(sum("return stata" in s for s in self.scripts), 1)
		self.assertIn('com.stata.stata30', self.scripts[0])  # future versions are probed too
		self.assertIn('tell application id "com.stata.stata18"', self.scripts[1])
		self.assertIn('DoCommandAsync "do \\"/tmp/a.do\\"" with addToReview', self.scripts[1])
		self.assertNotIn("activate", self.scripts[1])

	def test_pinned_version_and_activate(self):  # issue #34
		self.settings["stata_version"] = 17
		self.send("help regress", activate=True)
		self.assertEqual(len(self.scripts), 1)
		self.assertIn('tell application id "com.stata.stata17"\nactivate\n', self.scripts[0])
		self.assertNotIn("Viewer", self.scripts[0])

	def test_no_stata_found(self):
		self.newest = 0
		self.send("sum")
		self.assertIn("No version of Stata found", self.errors[0])

	def test_send_does_not_block_the_caller(self):
		import threading
		release = threading.Event()
		self.macos._osascript = lambda script: release.wait(10) and ""
		self.settings["stata_version"] = 18
		self.backend.send("sum")  # returns at once although osascript is still "running"
		self.assertFalse(release.is_set())
		release.set()
		self.backend._jobs.join()
		self.assertEqual(self.errors, [])

	def test_applescript_string_escaping(self):
		self.assertEqual(self.macos._applescript_string('a "b" \\c'), '"a \\"b\\" \\\\c"')


if __name__ == "__main__":
	unittest.main()
