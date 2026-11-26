"""Highlight additional Stata commands (issue #35).

The grammar is a static file, so the commands from the "custom_commands"
setting are written into a copy of Stata.tmLanguage inside the Packages folder,
which Sublime Text prefers over the one in the installed package.
"""

import os

import sublime

from . import text

GRAMMAR_FILE = "Stata.tmLanguage"


def _package_name():
	return __package__.split(".")[0]


def _override_path():
	return os.path.join(sublime.packages_path(), _package_name(), GRAMMAR_FILE)


def apply(names):
	"""Make exactly `names` the extra highlighted commands."""
	names = text.valid_command_names(names)
	path = _override_path()
	grammar = sublime.load_resource("Packages/%s/%s" % (_package_name(), GRAMMAR_FILE))
	grammar = text.add_commands_to_grammar(grammar, names)
	current = None
	if os.path.isfile(path):
		with open(path, encoding="utf-8") as f:
			current = f.read()
	if current == grammar:
		return
	if not names and current is not None and text.CUSTOM_MARKER not in current:
		return  # a grammar the user placed there; leave it alone
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8", newline="\n") as out:
		out.write(grammar)
