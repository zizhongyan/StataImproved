import unittest

from fake_sublime import View, load_plugin, support

MARK = "/*  ------- break line ------- (by Stata Improved Editor (piu_sign) )  */ "
OLD_MARK = "/*  ------- break line ------- (by the Stata editor for macOS (piu_sign) )  */ "


class CommandTest(unittest.TestCase):
	def setUp(self):
		self.plugin, self.sublime = load_plugin()
		self.sent = []
		execution = support("execution")
		execution.execute = lambda code, kind="selection", mode="do", activate=False, cwd=None: \
			self.sent.append((code, kind, mode, activate))
		self.cwds = []
		execution.execute = lambda code, kind="selection", mode="do", activate=False, cwd=None: \
			(self.sent.append((code, kind, mode, activate)), self.cwds.append(cwd))
		self.plugin.execution = execution

	def run_command(self, cls, text, file_name=None):
		view = View(text, file_name)
		cls(view).run(None)
		return view

	# --- macros and comments -------------------------------------------

	def test_local_on_word_and_one_letter_word(self):
		self.assertEqual(self.run_command(self.plugin.StataLocal, "gen x|y = 1").text, "gen `xy' = 1")
		self.assertEqual(self.run_command(self.plugin.StataLocal, "forvalues i| = 1/10").text, "forvalues `i' = 1/10")

	def test_macro_on_one_letter_word_does_not_crash(self):  # issue #37
		self.assertEqual(self.run_command(self.plugin.StataMacro, "x| = 1").text, "${x} = 1")
		self.assertEqual(self.run_command(self.plugin.StataMacro, "[${x}] = 1").text, "x = 1")

	def test_macro_between_spaces_changes_nothing(self):  # issue #37
		self.assertEqual(self.run_command(self.plugin.StataMacro, "a | b").text, "a  b")

	def test_macro_multiple_selections(self):
		self.assertEqual(self.run_command(self.plugin.StataMacro, "[a] [bb] [${c}]").text, "${a} ${bb} c")

	def test_toggle_selection_both_ways(self):
		self.assertEqual(self.run_command(self.plugin.StataToggle, "reg [y] x").text, "reg /* y */ x")
		self.assertEqual(self.run_command(self.plugin.StataToggle, "reg [/* y */] x").text, "reg y x")

	def test_toggle_without_selection_comments_line(self):  # issue #28
		view = self.run_command(self.plugin.StataToggle, "reg y| x")
		self.assertEqual(view.text, "reg y x")
		self.assertEqual(view.commands, [("toggle_comment", {"block": False})])

	# --- sending code ----------------------------------------------------

	def test_current_line_when_nothing_selected(self):
		self.run_command(self.plugin.lines_to_stataCommand, "sysuse auto\nreg pr|ice mpg\nsum")
		self.assertEqual(self.sent, [("reg price mpg\n", "selection", "do", False)])

	def test_selection_and_run_mode(self):
		self.run_command(self.plugin.LinesStataRun, "[sysuse auto\nreg price mpg]\nsum")
		self.assertEqual(self.sent, [("sysuse auto\nreg price mpg\n", "selection", "run", False)])

	def test_multiple_selections_are_separate_lines(self):
		self.run_command(self.plugin.lines_to_stataCommand, "[sum price] and [sum mpg]")
		self.assertEqual(self.sent[0][0], "sum price\nsum mpg\n")

	def test_two_carets_on_one_line_send_it_once(self):
		self.run_command(self.plugin.lines_to_stataCommand, "sum pri|ce mp|g\nreg y x|")
		self.assertEqual(self.sent[0][0], "sum price mpg\nreg y x\n")

	def test_send_whole_lines_setting(self):  # issue #25
		self.run_command(self.plugin.lines_to_stataCommand, "sum price\nreg pr[ice m]pg\nsum")
		self.assertEqual(self.sent[0][0], "ice m\n")
		self.sent = []
		self.sublime.settings["send_whole_lines"] = True
		self.run_command(self.plugin.lines_to_stataCommand, "sum price\nreg pr[ice m]pg\nsum")
		self.assertEqual(self.sent[0][0], "reg price mpg\n")

	def test_file_directory_is_passed(self):  # issue #20
		self.run_command(self.plugin.PiuSign, "sum|", file_name="/a/b/x.do")
		self.run_command(self.plugin.PiuSign, "sum|", file_name=None)
		self.assertEqual(self.cwds, ["/a/b", None])

	def test_empty_line_sends_nothing(self):
		self.run_command(self.plugin.lines_to_stataCommand, "sum\n|\nreg")
		self.assertEqual(self.sent, [])

	def test_unsaved_buffer(self):  # issue #38: file_name() is None
		self.run_command(self.plugin.PiuSign, "sysuse auto|", file_name=None)
		self.run_command(self.plugin.StataBro, "pri|ce", file_name=None)
		self.assertEqual([s[1] for s in self.sent], ["file", "browse"])

	def test_block_without_markers_sends_whole_file(self):
		self.run_command(self.plugin.PiuSign, "sysuse auto\nreg| price mpg")
		self.assertEqual(self.sent, [("sysuse auto\nreg price mpg\n", "file", "do", False)])

	def test_blocks(self):
		source = "sysuse auto\n" + MARK + "\nsum price\nsum mpg\n" + OLD_MARK + "\nreg price mpg\n"
		for caret_after, expected in (("sysuse", "sysuse auto\n"), ("sum price", "sum price\nsum mpg\n"),
				("reg price", "reg price mpg\n")):
			self.sent = []
			i = source.index(caret_after) + len(caret_after)
			view = self.run_command(self.plugin.PiuSign, source[:i] + "|" + source[i:])
			self.assertEqual(self.sent, [(expected, "block", "do", False)], caret_after)
			self.assertEqual(view.substr(view.sel()[0]).strip(), expected.strip())

	def test_empty_last_block_sends_nothing(self):
		self.run_command(self.plugin.PiuSign, "sum\n" + MARK + "\n|")
		self.assertEqual(self.sent, [])

	def test_help_and_browse(self):
		self.run_command(self.plugin.StataHelpCommand, "reg|ress y x")
		self.run_command(self.plugin.StataBro, "[price mpg\nweight]")
		self.assertEqual(self.sent, [("help regress\n", "help", "do", True),
			("browse price mpg weight\n", "browse", "do", True)])

	def test_help_without_word(self):
		self.run_command(self.plugin.StataHelpCommand, "reg | y")
		self.assertEqual(self.sent, [])

	def test_command_names_are_unchanged(self):
		# Key bindings and users' keymaps refer to these names.
		for name in ("StataLocal", "StataMacro", "StataToggle", "PiuSign", "lines_to_stataCommand",
				"StataHelpCommand", "StataBro", "InsertDatetimeCommand", "LinesStataRun", "StataCustomCommands"):
			self.assertTrue(hasattr(self.plugin, name), name)
		self.assertFalse(issubclass(self.plugin._WordToStata, self.plugin.sublime_plugin.TextCommand))


if __name__ == "__main__":
	unittest.main()
