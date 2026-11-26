import os
import plistlib
import re
import unittest

from fake_sublime import load_plugin, support

load_plugin()
text = support("text")


class TextTransformTest(unittest.TestCase):
	def test_local_macro(self):
		self.assertEqual(text.local_macro("x"), "`x'")

	def test_global_macro_toggles(self):
		self.assertEqual(text.toggle_global_macro("x"), "${x}")  # issue #37: one letter
		self.assertEqual(text.toggle_global_macro("${x}"), "x")
		self.assertEqual(text.toggle_global_macro("${xy}"), "xy")
		self.assertEqual(text.toggle_global_macro("$"), "${$}")
		self.assertEqual(text.toggle_global_macro(""), "${}")

	def test_block_comment_toggles(self):
		self.assertEqual(text.toggle_block_comment("x"), "/* x */")  # issue #37
		self.assertEqual(text.toggle_block_comment("/* x */"), "x")
		self.assertEqual(text.toggle_block_comment("/*x*/"), "x")
		self.assertEqual(text.toggle_block_comment("/**/"), "")
		self.assertEqual(text.toggle_block_comment("/*/"), "/* /*/ */")
		self.assertEqual(text.toggle_block_comment(""), "/*  */")

	def test_as_code_terminates_last_line(self):
		self.assertEqual(text.as_code(["reg y x"]), "reg y x\n")
		self.assertEqual(text.as_code(["a\n", "b"]), "a\nb\n")


class BlockBoundsTest(unittest.TestCase):
	# 0         1         2
	# 0123456789012345678901234
	# a\nMARK\nb\nc\nMARK\nd\n
	markers = [(2, 7), (11, 16)]

	def test_no_markers_is_whole_file(self):
		self.assertEqual(text.block_bounds([], 3, 10), (0, 10))

	def test_first_block(self):
		self.assertEqual(text.block_bounds(self.markers, 0, 18), (0, 2))

	def test_middle_block(self):
		self.assertEqual(text.block_bounds(self.markers, 8, 18), (7, 11))

	def test_last_block_after_final_marker(self):
		self.assertEqual(text.block_bounds(self.markers, 17, 18), (16, 18))

	def test_caret_on_marker_belongs_to_next_block(self):
		self.assertEqual(text.block_bounds(self.markers, 3, 18), (7, 11))


class GrammarTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Stata.tmLanguage")
		with open(path, encoding="utf-8") as f:
			cls.grammar = f.read()

	def rules(self, grammar):
		return {p.get("name"): p for p in plistlib.loads(grammar.encode("utf-8"))["patterns"]}

	def test_macros_share_a_scope_that_is_not_a_string(self):  # issue #9
		rules = self.rules(self.grammar)
		self.assertIn("variable.other.macro.local.stata", rules)
		self.assertNotIn("string.quoted.single.stata", rules)
		globals_rule = re.compile(rules["variable.other.macro.global.stata"]["match"])
		for word in ("$x", "$data", "${x}", "${long_name}"):
			self.assertEqual(globals_rule.search(word).group(0), word)

	def test_add_custom_commands(self):  # issue #35
		extra = text.add_commands_to_grammar(self.grammar, ["esttab", "reghdfe", "bad name", "esttab"])
		rule = self.rules(extra)["constant.language.stata"]["match"]
		regex = re.compile(rule)
		for word in ("esttab", "reghdfe", "collin"):
			self.assertTrue(regex.search("  " + word + " y x"), word)
		self.assertFalse(regex.search("esttabx"))
		self.assertFalse(re.compile(self.rules(self.grammar)["constant.language.stata"]["match"]).search("esttab"))

	def test_custom_commands_are_replaced_not_accumulated(self):
		once = text.add_commands_to_grammar(self.grammar, ["esttab"])
		twice = text.add_commands_to_grammar(once, ["reghdfe"])
		rule = self.rules(twice)["constant.language.stata"]["match"]
		self.assertIn("reghdfe", rule)
		self.assertNotIn("esttab", rule)
		self.assertEqual(text.add_commands_to_grammar(twice, []), self.grammar)

	def test_command_names(self):
		self.assertEqual(text.valid_command_names(["a", "b c", "1x", "_ok", "a", " d "]), ["a", "_ok", "d"])


if __name__ == "__main__":
	unittest.main()
