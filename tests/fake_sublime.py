"""A small stand-in for the `sublime` / `sublime_plugin` modules so the plugin
can be tested with a regular Python interpreter.

`load_plugin()` imports StataImproved.py as a sub-module of a package, the
way Sublime Text loads it ("<Package Name>.StataImproved").
"""

import importlib
import os
import re
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "StataImprovedUnderTest"

LITERAL = 1


class Region(object):
	def __init__(self, a, b=None):
		self.a = a
		self.b = a if b is None else b

	def begin(self):
		return min(self.a, self.b)

	def end(self):
		return max(self.a, self.b)

	def size(self):
		return self.end() - self.begin()

	def empty(self):
		return self.a == self.b

	def __len__(self):
		return self.size()

	def __eq__(self, other):
		return (self.a, self.b) == (other.a, other.b)

	def __hash__(self):
		return hash((self.a, self.b))

	def __repr__(self):
		return "Region(%d, %d)" % (self.a, self.b)


class Selection(list):
	def clear(self):
		del self[:]

	def add(self, region):
		self.append(region)
		self.sort(key=Region.begin)


class View(object):
	"""Only the View API the plugin uses. Carets are marked with | in `text`,
	selections with [ and ]."""

	def __init__(self, text, file_name=None):
		self._sel = Selection()
		plain = ""
		start = None
		for ch in text:
			if ch == "|":
				self._sel.add(Region(len(plain)))
			elif ch == "[":
				start = len(plain)
			elif ch == "]":
				self._sel.add(Region(start, len(plain)))
			else:
				plain += ch
		self.text = plain
		self._file_name = file_name
		self.commands = []

	def sel(self):
		return self._sel

	def size(self):
		return len(self.text)

	def substr(self, region):
		return self.text[region.begin():region.end()]

	def word(self, point):
		begin = end = point
		while begin > 0 and re.match(r"\w", self.text[begin - 1]):
			begin -= 1
		while end < len(self.text) and re.match(r"\w", self.text[end]):
			end += 1
		return Region(begin, end)

	def line(self, region):
		if not isinstance(region, Region):
			region = Region(region)
		begin = self.text.rfind("\n", 0, region.begin()) + 1
		end = self.text.find("\n", region.end())
		return Region(begin, len(self.text) if end < 0 else end)

	def full_line(self, region):
		line = self.line(region)
		return Region(line.begin(), min(line.end() + 1, len(self.text)))

	def find_all(self, pattern, flags=0):
		pattern = re.escape(pattern) if flags & LITERAL else pattern
		return [Region(m.start(), m.end()) for m in re.finditer(pattern, self.text)]

	def replace(self, edit, region, text):
		delta = len(text) - region.size()
		self.text = self.text[:region.begin()] + text + self.text[region.end():]
		for i, sel in enumerate(self._sel):
			if sel.begin() >= region.end():
				self._sel[i] = Region(sel.a + delta, sel.b + delta)

	def run_command(self, name, args=None):
		self.commands.append((name, args))

	def file_name(self):
		return self._file_name


class Settings(dict):
	def get(self, key, default=None):
		return dict.get(self, key, default)


def install(platform="windows"):
	"""Register fake `sublime` and `sublime_plugin` modules; returns `sublime`."""
	sublime = types.ModuleType("sublime")
	sublime.Region = Region
	sublime.LITERAL = LITERAL
	sublime.settings = Settings()
	sublime.messages = []
	sublime.load_settings = lambda name: sublime.settings
	sublime.platform = lambda: platform
	sublime.status_message = lambda message: sublime.messages.append(("status", message))
	sublime.error_message = lambda message: sublime.messages.append(("error", message))
	sublime.message_dialog = lambda message: sublime.messages.append(("dialog", message))
	sublime.set_timeout = lambda callback, delay=0: callback()
	sublime.set_timeout_async = lambda callback, delay=0: callback()

	sublime_plugin = types.ModuleType("sublime_plugin")

	class TextCommand(object):
		def __init__(self, view):
			self.view = view

	class WindowCommand(object):
		def __init__(self, window):
			self.window = window

	sublime_plugin.TextCommand = TextCommand
	sublime_plugin.WindowCommand = WindowCommand
	sys.modules["sublime"] = sublime
	sys.modules["sublime_plugin"] = sublime_plugin
	return sublime


def load_plugin(platform="windows"):
	"""Fresh import of the plugin (and its support package) on a fake Sublime."""
	sublime = install(platform)
	for name in list(sys.modules):
		if name == PACKAGE or name.startswith(PACKAGE + "."):
			del sys.modules[name]
	package = types.ModuleType(PACKAGE)
	package.__path__ = [ROOT]
	sys.modules[PACKAGE] = package
	plugin = importlib.import_module(PACKAGE + ".StataImproved")
	return plugin, sublime


def support(module):
	"""A module of the plugin's support package, e.g. support("text")."""
	return importlib.import_module(PACKAGE + ".stata_improved." + module)
