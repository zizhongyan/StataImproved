#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sublime_plugin
import sublime 
import codecs
import tempfile
class lines_to_stataCommand(sublime_plugin.TextCommand): 
	def run(self, edit): 
		all_text = ""
		sels = self.view.sel()
		for sel in sels:
			all_text = all_text + self.view.substr(sel)
		if len(all_text) == 0:
			all_text = self.view.substr(self.view.line(sel)) 
		all_text = all_text + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'selectedlines_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(all_text) 
		cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Sublime Text") 
		os.system(cmd) 
class StataHelpCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		self.view.run_command("expand_selection", {"to": "word"})
		sel = self.view.sel()[0]
		help_word = self.view.substr(sel)
		all_text = "help " + help_word  + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'HELP_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(all_text) 
		cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Viewer") 
		os.system(cmd)   
class StataBro(sublime_plugin.TextCommand):
	def run(self,edit):
		self.view.run_command("expand_selection", {"to": "word"})
		sel = self.view.sel()[0]
		help_word = self.view.substr(sel)
		all_text = "browse " + help_word  + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'BROWSE_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(all_text) 
		cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Viewer") 
		os.system(cmd)   
class PiuSign(sublime_plugin.TextCommand):
	def run(self, edit):
		getme = list(map(lambda x: x.begin(), self.view.find_all('Piu_Sign'))) 
		selss = self.view.sel()
		for sel in selss:
			def findme(q_type, quotes):
				length, tos, froms = False, False, False
				if len(quotes) - self.view.substr(sel).count('Piu_Sign') >= 2:
					starts = list(filter(lambda x: x < sel.begin(), quotes))
					ends = list(filter(lambda x: x >= sel.end(), quotes)) 
					if starts: tos = starts[-1]
					if ends: froms = ends[0]
					if starts and ends: length = froms - tos
				return length, tos, froms 
			touse1, touse2, touse3 = findme('Piu_Sign', getme)  
			def replace_region(start, end):
				if sel.size() < end-start-2:
					start += 1; end -= 1
				self.view.sel().subtract(sel)
				self.view.sel().add(sublime.Region(start-5, end+71))
			replace_region(touse2, touse3+1) 
		print(self.view.sel()) 
		all_text = ""
		sels = self.view.sel()
		for sel in sels:
			all_text = all_text + self.view.substr(sel)
		if len(all_text) == 0:
			all_text = self.view.substr(self.view.line(sel)) 
		all_text = all_text + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'BLOCK_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(all_text) 
		cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Sublime Text") 
		os.system(cmd)  
class StataLocal(sublime_plugin.TextCommand):
	def run(self,edit):
		sels = self.view.sel()
		for sel in sels:
			if len(sel) == 0:
				word_sel = self.view.word(sel.a)
			else:
				word_sel = sel
			word_str = self.view.substr(word_sel)
			word_str = "`"+word_str+"'"
			self.view.replace(edit,word_sel,word_str)
class StataMacro(sublime_plugin.TextCommand):
	def run(self,edit):
		sels = self.view.sel()
		for sel in sels:
			if len(sel) == 0:
				word_sel = self.view.word(sel.a)
			else:
				word_sel = sel
			word_str = self.view.substr(word_sel)
			word_str = "${"+word_str+"}"
			self.view.replace(edit,word_sel,word_str)

