#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sublime_plugin
import sublime 
import codecs
import tempfile
import subprocess
import time
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
def get_stata_version():   # get_stata_version is modefied based on the Stata Enhanced - https://github.com/andrewheiss/SublimeStataEnhanced/
    cmd = """osascript<< END
                try
                    tell me to get application id "com.stata.stata14"
                    set stata to 14
                end try
                try
                    tell me to get application id "com.stata.stata13"
                    set stata to 13
                end try
                try
                    tell me to get application id "com.stata.stata12"
                    set stata to 12
                end try
                try
                    tell me to get application id "com.stata.stata11"
                    set stata to 11
                end try
                return stata
            END"""
    try:
        version = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        sublime.error_message("No version of Stata found.")
        raise Exception("No version of Stata found.") 
    version = version.decode("utf-8").strip()
    return((int(version), "com.stata.stata{}".format(version)))
class PiuSign(sublime_plugin.TextCommand):
	def run(self, edit):
		getme = list(map(lambda x: x.begin(), self.view.find_all('piu_sign'))) 
		selss = self.view.sel()
		for sel in selss:
			def findme(q_type, quotes):
				length, tos, froms = False, False, False
				if len(quotes) - self.view.substr(sel).count('piu_sign') >= 2:
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
				self.view.sel().add(sublime.Region(start-64, end+15))
			replace_region(touse2, touse3+1) 
		print(self.view.sel()) 
		selectedcode = ""
		sels = self.view.sel()
		for sel in sels:
			selectedcode = selectedcode + self.view.substr(sel)
		if len(selectedcode) == 0:
			selectedcode = self.view.substr(self.view.line(sel)) 
		selectedcode = selectedcode + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'BLOCK_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(selectedcode) 
		version, stata_app_id = get_stata_version()
		cmd = """osascript<< END
		 tell application id "{0}" 
		    DoCommandAsync "do {1}"  with addToReview
		 end tell 
		 END""".format(stata_app_id,dofile_path,"Viewer") 
		os.system(cmd) 
class lines_to_stataCommand(sublime_plugin.TextCommand): 
	def run(self, edit): 
		selectedcode = ""
		sels = self.view.sel()
		for sel in sels:
			selectedcode = selectedcode + self.view.substr(sel)
		if len(selectedcode) == 0:
			selectedcode = self.view.substr(self.view.line(sel)) 
		selectedcode = selectedcode + "\n"
		dofile_path =tempfile.gettempdir()+'selectedlines_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(selectedcode) 
		# cmd = "/Applications/Stata/StataSE.app/Contents/MacOS/StataSE 'do /Users/piupiu/Downloads/a'"
		# os.popen(cmd) 
		# cmd = """osascript -e 'tell application "StataSE" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Viewer") 
		# os.system(cmd) 
		version, stata_app_id = get_stata_version()
		cmd = """osascript<< END
		 tell application id "{0}"
		    DoCommandAsync "do {1}"  with addToReview
		 end tell
		 END""".format(stata_app_id,dofile_path) 
		print(cmd)
		print("stata_app_id")
		print(stata_app_id)
		os.system(cmd)
class StataHelpCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		self.view.run_command("expand_selection", {"to": "word"})
		sel = self.view.sel()[0]
		help_word = self.view.substr(sel)
		selectedcode = "help " + help_word  + "\n"    
		dofile_path =tempfile.gettempdir()+'HELP_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(selectedcode) 
		# cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Viewer") 
		version, stata_app_id = get_stata_version()
		cmd = """osascript<< END
		 tell application id "{0}"
		 	activate
		    DoCommandAsync "do {1}"  with addToReview
		 end tell
		 tell application "{2}"
		 	activate
		 end tell
		 END""".format(stata_app_id,dofile_path,"Viewer") 
		os.system(cmd) 
class StataBro(sublime_plugin.TextCommand):
	def run(self,edit):
		self.view.run_command("expand_selection", {"to": "word"})
		sel = self.view.sel()[0]
		help_word = self.view.substr(sel)
		selectedcode = "browse " + help_word  + "\n"   
		dofile_path = os.path.join(os.path.dirname(self.view.file_name()), 'from_sublime.do')
		dofile_path =tempfile.gettempdir()+'BROWSE_piupiu.do'
		with codecs.open(dofile_path, 'w', encoding='utf-8') as out:  
		    out.write(selectedcode) 
		# cmd = """osascript -e 'tell application "Finder" to open POSIX file "{0}"' -e 'tell application "{1}" to activate' &""".format(dofile_path, "Viewer") 
		version, stata_app_id = get_stata_version()
		cmd = """osascript<< END
		 tell application id "{0}"
		 	activate
		    DoCommandAsync "do {1}"  with addToReview
		 end tell
		 tell application "{2}"
		 	activate
		 end tell
		 END""".format(stata_app_id,dofile_path,"Viewer") 
		os.system(cmd)      
class InsertDatetimeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel();
        for s in sel:
            self.view.replace(edit, s, time.ctime())