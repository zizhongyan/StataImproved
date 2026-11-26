"""Integration checks that run inside a real Sublime Text.

tools/run_sublime_integration.py copies this file into Packages/User of a
portable Sublime Text, starts it, and reads the JSON results this plugin
writes before quitting Sublime Text. Nothing is sent to a real Stata: the
backend is replaced by a recorder, except for one Windows check that starts
the installed Stata and runs a do-file in it (the runner closes that Stata).
"""
import json
import os
import sys
import traceback

import sublime
import sublime_plugin

PACKAGE = "Stata Improved Editor"
SYNTAX = "Packages/%s/Stata.tmLanguage" % PACKAGE
RESULTS = os.path.join(os.path.dirname(sublime.packages_path()), "stata_improved_integration.json")
LOG = os.path.join(os.path.dirname(sublime.packages_path()), "stata_improved_integration.log")

results = []
state = {}


def log(message):
	with open(LOG, "a", encoding="utf-8") as f:
		f.write(message + "\n")


class _Tee(object):
	"""Copy console output (e.g. tracebacks) to the log file."""

	def __init__(self, stream):
		self.stream = stream

	def write(self, text):
		try:
			with open(LOG, "a", encoding="utf-8") as f:
				f.write(text)
		except OSError:
			pass
		return self.stream.write(text)

	def flush(self):
		self.stream.flush()


sys.stdout = _Tee(sys.stdout)
sys.stderr = _Tee(sys.stderr)
log("harness imported, python %s" % sys.version.split()[0])


def guarded(step):
	"""Run a step; an unexpected exception fails the run instead of hanging it."""
	def run():
		log("step " + step.__name__)
		try:
			step()
		except Exception:
			record("step %s" % step.__name__, False, traceback.format_exc())
			finish()
	return run


def record(name, ok, detail=""):
	results.append({"name": name, "ok": bool(ok), "detail": detail})


def check(name, function):
	try:
		detail = function()
		record(name, True, detail if detail is not None else "")
	except Exception:
		record(name, False, traceback.format_exc())


def plugin_loaded():
	sublime.set_timeout(guarded(step_start), 3000)


def plugin_module(name):
	import importlib
	return importlib.import_module("%s.%s" % (PACKAGE, name))


def new_view(text):
	view = sublime.active_window().new_file()
	view.set_scratch(True)
	view.assign_syntax(SYNTAX)
	view.run_command("append", {"characters": text})
	return view


def all_text(view):
	return view.substr(sublime.Region(0, view.size()))


def select(view, *regions):
	view.sel().clear()
	for region in regions:
		view.sel().add(sublime.Region(*region) if isinstance(region, tuple) else sublime.Region(region))


def expect(actual, expected):
	if actual != expected:
		raise AssertionError("expected %r, got %r" % (expected, actual))
	return repr(actual)


# --- steps (chained with set_timeout so Sublime can process in between) -----

def step_start():
	record("environment", True, {"sublime_version": sublime.version(), "platform": sublime.platform(),
		"harness_python": sys.version.split()[0]})

	def plugin_loaded_ok():
		module = plugin_module("StataImproved")
		support = plugin_module("stata_improved.execution")
		return {"plugin_file": module.__file__, "support": support.__name__}
	check("package plugin is loaded", plugin_loaded_ok)

	def command_names():
		names = set()
		for classes in sublime_plugin.all_command_classes:
			for cls in classes:
				if cls.__module__.startswith(PACKAGE + "."):
					names.add(cls.name(cls.__new__(cls)))
		expected = {"stata_local", "stata_macro", "stata_toggle", "piu_sign", "lines_to_stata",
			"lines_stata_run", "stata_help", "stata_bro", "insert_datetime", "stata_register_automation"}
		if names != expected:
			raise AssertionError("commands: %s" % sorted(names))
		return sorted(names)
	check("command names", command_names)

	def resources():
		checked = []
		for name in ("Default (Windows).sublime-keymap", "Default (OSX).sublime-keymap",
				"StataImproved.sublime-settings", "Default.sublime-commands", "Main.sublime-menu",
				"Stata.sublime-build", "messages.json", "markdown.sublime-completions"):
			sublime.decode_value(sublime.load_resource("Packages/%s/%s" % (PACKAGE, name)))
			checked.append(name)
		snippets = sublime.find_resources("*.sublime-snippet")
		ours = [s for s in snippets if s.startswith("Packages/%s/" % PACKAGE)]
		return {"json_files": len(checked), "snippets": len(ours)}
	check("package resources parse", resources)

	def settings():
		s = sublime.load_settings("StataImproved.sublime-settings")
		return expect((s.get("stata_version"), s.get("windows_progid")), ("auto", "stata.StataOLEApp"))
	check("settings load", settings)

	state["view"] = new_view("sysuse auto\nreg price mpg\n")
	sublime.set_timeout(guarded(step_editing), 1500)


def step_editing():
	view = state["view"]
	check("syntax scope", lambda: view.scope_name(0).split()[0] == "source.stata" or
		(_ for _ in ()).throw(AssertionError(view.scope_name(0))))

	def macro_one_letter():  # issue #37
		v = new_view("x = 1")
		select(v, (0, 1))
		v.run_command("stata_macro")
		first = all_text(v)
		select(v, (0, 4))
		v.run_command("stata_macro")
		return expect((first, all_text(v)), ("${x} = 1", "x = 1"))
	check("stata_macro on a one-letter word", macro_one_letter)

	def local_word_under_caret():
		v = new_view("forvalues i = 1/10")
		select(v, 11)
		v.run_command("stata_local")
		return expect(all_text(v), "forvalues `i' = 1/10")
	check("stata_local on the word under the caret", local_word_under_caret)

	def toggle_block_comment():
		v = new_view("reg price mpg")
		select(v, (4, 9))
		v.run_command("stata_toggle")
		first = all_text(v)
		select(v, (4, 15))
		v.run_command("stata_toggle")
		return expect((first, all_text(v)), ("reg /* price */ mpg", "reg price mpg"))
	check("stata_toggle with a selection", toggle_block_comment)

	def toggle_line_comment():  # issue #28, uses Comments.tmPreferences
		v = new_view("reg price mpg")
		select(v, 5)
		v.run_command("stata_toggle")
		return expect(all_text(v), "// reg price mpg")
	check("stata_toggle without selection comments the line", toggle_line_comment)

	def snippet():
		v = new_view("")
		v.run_command("insert_snippet", {"name": "Packages/%s/Foreach.sublime-snippet" % PACKAGE})
		text = all_text(v)
		if not text.strip().startswith("foreach"):
			raise AssertionError(repr(text))
		return repr(text[:40])
	check("snippet expands", snippet)
	sublime.set_timeout(guarded(step_execution), 500)


def step_execution():
	execution = plugin_module("stata_improved.execution")
	sent = []

	class Recorder(object):
		def send(self, command, activate=False):
			path = command.split(" ", 1)[1].strip('"')
			with open(path, encoding="utf-8") as f:
				sent.append((command.split(" ", 1)[0], f.read(), activate, path))

		def close(self):
			pass
	execution._backend = Recorder()

	def run_and_capture(text, sel, command):
		del sent[:]
		v = new_view(text)
		select(v, *sel)
		v.run_command(command)
		return sent[:]

	def current_line():
		got = run_and_capture("sysuse auto\nreg price mpg\n", [15], "lines_to_stata")
		return expect([(m, code) for m, code, _, _ in got], [("do", "reg price mpg\n")])
	check("lines_to_stata sends the current line", current_line)

	def run_quietly():
		got = run_and_capture("sum price\nsum mpg", [(0, 17)], "lines_stata_run")
		return expect([(m, code) for m, code, _, _ in got], [("run", "sum price\nsum mpg\n")])
	check("lines_stata_run sends the selection with run", run_quietly)

	def blocks():
		mark = "/*  ------- break line ------- (by Stata Improved Editor (piu_sign) )  */ "
		text = "sysuse auto\n" + mark + "\nsum price\n" + mark + "\nreg price mpg"
		last = run_and_capture(text, [len(text) - 2], "piu_sign")
		middle = run_and_capture(text, [text.index("sum price") + 2], "piu_sign")
		return expect([g[0][1] for g in (last, middle)], ["reg price mpg\n", "sum price\n"])
	check("piu_sign sends the block around the caret (incl. the last one)", blocks)

	def temp_files():
		got = run_and_capture("sum", [0], "lines_to_stata") + run_and_capture("sum", [0], "lines_to_stata")
		paths = [g[3] for g in got]
		import tempfile
		expected_dir = os.path.normcase(os.path.join(tempfile.gettempdir(), "StataImproved"))
		inside = all(os.path.normcase(os.path.dirname(os.path.normpath(p))) == expected_dir for p in paths)
		if not inside or paths[0] == paths[1]:
			raise AssertionError(paths)
		return paths
	check("temp do-files are unique and inside the temp dir", temp_files)

	def help_command():
		got = run_and_capture("regress y x", [3], "stata_help")
		return expect([(code, activate) for _, code, activate, _ in got], [("help regress\n", True)])
	check("stata_help", help_command)

	# Real backend for this platform. On Windows with Stata installed and not
	# running, the plugin starts Stata and types a do-file command into it;
	# the do-file writes a marker file. tools/run_sublime_integration.py then
	# checks that this Stata outlives Sublime Text and closes it.
	execution._backend = None
	errors = []
	state["errors"] = errors
	execution.report_error = errors.append
	if sublime.platform() != "windows":
		return finish()
	windows = plugin_module("stata_improved.backend_windows")
	stata_window = plugin_module("stata_improved.stata_window")
	if not windows.find_stata_executables() or stata_window.stata_windows():
		record("windows: code runs in the real Stata (skipped: no Stata installed, or Stata already running)", True)
		return guarded(step_wincom)()
	import tempfile
	folder = tempfile.mkdtemp(prefix="stata improved é ")
	state["marker"] = os.path.join(folder, "ran.txt")
	code = ('file open fh using "%s", write replace\nfile write fh "ran"\nfile close fh\n'
		% state["marker"].replace("\\", "/"))
	v = new_view(code)
	select(v, (0, v.size()))
	v.run_command("lines_to_stata")
	state["wait"] = 0
	sublime.set_timeout(guarded(step_wait_for_stata), 500)


def step_wait_for_stata():
	errors = state["errors"]
	ran = os.path.exists(state["marker"])
	if ran or errors or state["wait"] >= 120:
		record("windows: Sublime Text starts Stata and the code runs in it", ran and not errors,
			errors[0] if errors else "marker written after %.1f s" % (state["wait"] * 0.5))
		return guarded(step_wincom)()
	state["wait"] += 1
	sublime.set_timeout(guarded(step_wait_for_stata), 500)


def step_wincom():
	def dictionary_round_trip():
		wincom = plugin_module("stata_improved.wincom")
		wincom.initialize()
		d = wincom.Dispatch("Scripting.Dictionary")
		try:
			d.call("Add", "k", "é 中文")
			return expect((d.call("Item", "k"), d.call("Count")), ("é 中文", 1))
		finally:
			d.release()
	check("ctypes COM client inside the plugin host", dictionary_round_trip)
	finish()


def finish():
	with open(RESULTS, "w", encoding="utf-8") as f:
		json.dump(results, f, indent=1, ensure_ascii=False)
	for window in sublime.windows():
		for view in window.views():
			view.set_scratch(True)
	sublime.set_timeout(lambda: sublime.run_command("exit"), 300)
