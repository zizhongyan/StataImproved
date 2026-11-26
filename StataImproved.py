#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stata Improved Editor: edit Stata do-files in Sublime Text and send them
to Stata (macOS via AppleScript, Windows by typing into Stata's Command window
or, optionally, via Stata Automation).

Command names (stata_local, lines_to_stata, piu_sign, ...) are part of the
public interface: key bindings, menus and users' own keymaps refer to them.
"""
import os
import time

import sublime
import sublime_plugin

from .stata_improved import custom_commands, execution, text


def plugin_loaded():
	execution.remove_legacy_files()
	names = execution.settings().get("custom_commands") or []
	if names:
		try:
			custom_commands.apply(names)
		except (OSError, ValueError) as e:
			print("Stata Improved Editor: could not update the syntax highlighting: %s" % e)


def plugin_unloaded():
	execution.shutdown()


def _selected_or_word_regions(view):
	"""Selections, with an empty selection replaced by the word around it."""
	regions = []
	for sel in view.sel():
		region = view.word(sel.a) if sel.empty() else sel
		if view.substr(region).strip():
			regions.append(region)
	return regions


def _file_directory(view):
	"""Folder of the file in `view`, None for an unsaved buffer."""
	name = view.file_name()
	return os.path.dirname(name) if name else None


def _replace_each(view, edit, regions, transform):
	for region in reversed(regions):
		view.replace(edit, region, transform(view.substr(region)))


class StataLocal(sublime_plugin.TextCommand):
	def run(self, edit):
		_replace_each(self.view, edit, _selected_or_word_regions(self.view), text.local_macro)


class StataMacro(sublime_plugin.TextCommand):
	def run(self, edit):
		_replace_each(self.view, edit, _selected_or_word_regions(self.view), text.toggle_global_macro)


class StataToggle(sublime_plugin.TextCommand):
	def run(self, edit):
		selected = [sel for sel in self.view.sel() if not sel.empty()]
		if not selected:
			# Nothing selected: comment the line(s) with // (issue #28).
			self.view.run_command("toggle_comment", {"block": False})
			return
		_replace_each(self.view, edit, selected, text.toggle_block_comment)


class lines_to_stataCommand(sublime_plugin.TextCommand):
	"""Do the selected code, or the current line if nothing is selected."""
	mode = "do"

	def run(self, edit):
		regions = []
		whole_lines = execution.settings().get("send_whole_lines", False)
		for sel in self.view.sel():
			region = self.view.line(sel) if sel.empty() or whole_lines else sel
			# Two carets on one line must not send that line twice.
			if region not in regions:
				regions.append(region)
		chunks = [self.view.substr(region) for region in regions]
		if not "".join(chunks).strip():
			sublime.status_message("Stata Improved Editor: nothing to send")
			return
		execution.execute(text.as_code(chunks), kind="selection", mode=self.mode,
			cwd=_file_directory(self.view))


class LinesStataRun(lines_to_stataCommand):
	"""Like lines_to_stata, but `run` the code (no output echoed)."""
	mode = "run"


class PiuSign(sublime_plugin.TextCommand):
	"""Do the block around the caret; blocks are separated by break lines.
	Without break lines, do the whole file."""

	def run(self, edit):
		view = self.view
		markers = sorted(set((line.begin(), line.end()) for line in
			(view.full_line(r) for r in view.find_all(text.BLOCK_MARKER, sublime.LITERAL))))
		if not markers:
			code = view.substr(sublime.Region(0, view.size()))
			if code.strip():
				execution.execute(text.as_code([code]), kind="file", cwd=_file_directory(view))
			return
		blocks = sorted(set(text.block_bounds(markers, sel.begin(), view.size()) for sel in view.sel()))
		chunks = [view.substr(sublime.Region(begin, end)) for begin, end in blocks]
		# Select what is sent so the user can see which block ran.
		view.sel().clear()
		for begin, end in blocks:
			view.sel().add(sublime.Region(begin, end))
		if not "".join(chunks).strip():
			sublime.status_message("Stata Improved Editor: this block is empty")
			return
		execution.execute(text.as_code(chunks), kind="block", cwd=_file_directory(view))


class _WordToStata(object):
	"""Mixin (not a command itself): send `<stata_command> <selected word(s)>`."""
	stata_command = None

	def run(self, edit):
		sel = self.view.sel()[0]
		region = self.view.word(sel.a) if sel.empty() else sel
		argument = " ".join(self.view.substr(region).split())
		if not argument:
			sublime.status_message("Stata Improved Editor: select a word first")
			return
		execution.execute(self.stata_command + " " + argument + "\n", kind=self.stata_command, activate=True)


class StataHelpCommand(_WordToStata, sublime_plugin.TextCommand):
	"""Open Stata's help for the selected command."""
	stata_command = "help"


class StataBro(_WordToStata, sublime_plugin.TextCommand):
	"""Open the Data Browser for the selected variable(s)."""
	stata_command = "browse"


class InsertDatetimeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for s in self.view.sel():
			self.view.replace(edit, s, time.ctime())


class StataCustomCommands(sublime_plugin.WindowCommand):
	"""Ask for extra commands to highlight, remember them in the settings."""

	def run(self):
		current = " ".join(execution.settings().get("custom_commands") or [])
		self.window.show_input_panel("Commands to highlight (separated by spaces):", current,
			self.done, None, None)

	def done(self, value):
		names = text.valid_command_names(value.split())
		settings = execution.settings()
		settings.set("custom_commands", names)
		sublime.save_settings(execution.SETTINGS_FILE)
		try:
			custom_commands.apply(names)
		except (OSError, ValueError) as e:
			execution.report_error("Could not update the syntax highlighting:\n%s" % e)
			return
		sublime.status_message("Stata Improved Editor: highlighting %d extra command(s); "
			"reopen the file if the colors do not change" % len(names))


class StataRegisterAutomationCommand(sublime_plugin.WindowCommand):
	"""Windows: register Stata Automation (runs `Stata.exe /Register` elevated)."""

	def is_visible(self):
		return sublime.platform() == "windows"

	def run(self):
		from .stata_improved import backend_windows
		executables = backend_windows.find_stata_executables(execution.settings().get("stata_path", ""))
		if not executables:
			execution.report_error("No Stata executable was found. Set \"stata_path\" in "
				"Preferences > Package Settings > Stata Improved Editor > Settings.")
		elif len(executables) == 1:
			self.register(executables[0])
		else:
			self.window.show_quick_panel(executables,
				lambda index: index >= 0 and self.register(executables[index]))

	def register(self, executable):
		from .stata_improved import backend_windows
		if not backend_windows.register(executable):
			execution.report_error("Could not run %s /Register (was the administrator prompt declined?)." % executable)
			return
		progid = execution.settings().get("windows_progid") or backend_windows.DEFAULT_PROGID
		sublime.status_message("Stata Improved Editor: registering Stata Automation...")

		def check(attempt=1):
			if backend_windows.is_registered(progid):
				sublime.message_dialog("Stata Automation is registered.\n\n%s\n\n"
					"It is only used with \"windows_method\": \"automation\" in the settings; by default "
					"code is typed into Stata's Command window, which needs no registration." % executable)
			elif attempt < 15:
				sublime.set_timeout_async(lambda: check(attempt + 1), 1000)
			else:
				execution.report_error("Stata Automation is still not registered. Try running\n\n"
					"\"%s\" /Register\n\nfrom an administrator Command Prompt." % executable)
		sublime.set_timeout_async(check, 1000)
