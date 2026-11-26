# Stata Improved Editor for Sublime Text (macOS & Windows)

Stata Improved Editor is a polished Sublime Text plugin built to deliver a highly productive Stata do-file workflow on macOS and Windows.

It supports Stata 13–19 (including StataNow) and Sublime Text 4 (and 3), with streamlined shortcuts for sending code to Stata, cell-style execution, snippets/templates, comment toggles, and Stata/Mata syntax highlighting.

> **Note:** To get started, please install [Sublime Text](https://www.sublimetext.com/download). After installing (or updating) this package, please **restart Sublime Text** so that all commands and key bindings load correctly.

* Available via [Package Control](https://packagecontrol.io/packages/Stata%20Improved%20Editor) since **16 Jan 2017**.
* Maintained by [Zizhong Yan](mailto:helloyzz@gmail.com). Last updated: **1 Jan 2026**. Feedback is welcome.


## 🎼 News 🎼 
**v2.0.0**: **Sublime Text 4** (Python 3.14 plugin host) and **Windows** support. On Windows, code is typed into Stata's Command window; no setup needed (see [Windows setup](#windows-setup)). Key bindings now only apply in Stata files; `$` alone types `$` again; <kbd>CMD</kbd>+<kbd>/</kbd> without a selection comments the line with `//`; the Stata version can be pinned in the settings. Fixes for one-letter words, unsaved files and temporary files (#37, #38, #39).

**v1.3.19 (01/Jan/26)**: Full support for **Stata 19** and  **StataNow** is made.  

**v1.3.17 (29/Apr/23)**: Full support for **Stata 18** is made.  

**v1.3.10 (11/May/21)**: Full support for **Stata 17** as well (in progress). Now one can select any word, press `$` to make it as ${word}. And select ${word}, press `$` to make it as word. Select any word, press <kbd>CMD</kbd> +<kbd>/</kbd> to make the selected word toggled. And press <kbd>CMD</kbd> +<kbd>/</kbd>  again to make toggled word  to original word.  


## 🏆 Main Features
#### 1, Execute the selected do-file 
#### 2, Split the do-file into cells, and execute a block of do-file (just like what you do in Matlab) !!
#### 3, Automated way to write Comments toggle, create a Fancy Section Header, and a To Do List.
#### 4, Automatic template for i) writting common used commands, ii) for loops, iii) writing program.(We are updating/incorprating more templates/snippets for Stata commands.)
#### 5, Select any **word**, press <kbd>\`</kbd>, it will become '**word**'. 
#### 6, Select any **word**, press <kbd>$</kbd>, it will become **${word}**. 
#### 7, Select any **word**, press <kbd>cmd</kbd>+<kbd>/</kbd>, it will become **/* word */**. 
#### 8, Select any command, press <kbd>F1</kbd> to see its help file. 
#### 9, Select any variable(s), press <kbd>F2</kbd> to see the data browser. 
#### 10, Press <kbd>F5</kbd>, insert the current date and time in the code.
#### 11, Stata and MATA Syntax-highlighting  
#### 12, Stata 15 Markdown Document support.

## 💿 Installations 
Firstly you need to install [Sublime Text](https://www.sublimetext.com/download) (Sublime Text 4 is recommended; Sublime Text 3 still works).

### Installation via packge control. (easiest and recommended🏅)
The installation is very simple as this package has been accepted by the [Sublime Text package manager](https://packagecontrol.io). There are 3 steps:

* Open Sublime Text, from the main application menu, navigate to `Tools`, open the `Command Palette` (shortcut: <kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on macOS, <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd> on Windows)
* Select `Package Control: Install Package`
* Search `Stata Improved Editor` and hit <kbd>Enter</kbd> to complete installation.

If you could not find the package control in your Sublime Text, you will need to install it in advance. To install it, please go to [this webpage](https://packagecontrol.io/installation). 

Note that though the trial version of Sublime Text is untimed and unlimited, the license need be purchased. 

### Manual installation
Open Sublime Text, click the Preferences-> Browse Packages-> Then you will reach the `Packages` folder (e.g. `~/Library/Application Support/Sublime Text/Packages` on macOS, `%APPDATA%\Sublime Text\Packages` on Windows). Download [this Stata plugin from here](https://github.com/zizhongyan/StataImproved/archive/master.zip), and unpack the zip fil into that folder, and rename it as "Stata Improved Editor". 

### macOS setup
Nothing to configure in Stata itself: install Stata (13 or later) and open it once. The first time you send code, macOS asks whether Sublime Text may control Stata (`System Settings > Privacy & Security > Automation`); allow it. Then open a `.do` file, select some lines (or none, for the current line) and press <kbd>CTRL</kbd>+<kbd>d</kbd>. If you have several Stata versions installed, pick one with `"stata_version"`.

### Windows setup
Nothing to set up: the plugin types the code into Stata's Command window (Stata may be minimized or busy; it does not need the focus). If no Stata is running, the newest installed Stata is started. If Stata is installed in an unusual folder, set `"stata_path"` in `Preferences > Package Settings > Stata Improved Editor > Settings`.

Notes for Windows:
* This was developed and verified with **Stata 18** (MP, Chinese user interface). Other versions should work, but the plugin relies on how Stata lays out its main window; if it cannot find the Command window it tells you so.
* A user name with non-ASCII characters (e.g. Chinese) is fine. Only if Stata is **minimized** *and* the temporary folder's path contains non-ASCII characters, the plugin needs Stata 14 or later. (To avoid that entirely, set `"temp_directory"` to a folder with an ASCII-only path.)
* If Stata runs as administrator, Sublime Text has to run as administrator too (Windows blocks input to a higher-privileged program).

Alternatively, `"windows_method": "automation"` uses [Stata Automation](https://www.stata.com/automation/) (run `Stata Improved: Register Stata Automation (Windows, optional)` once). Be aware that Stata then closes when Sublime Text lets go of it (some minutes after Sublime Text exits), without asking to save your data.


## 🎷 Usage 
### ⌨️ Key bindings
All key bindings only apply in Stata files (`.do`, `.ado`).

| Action | macOS | Windows |
|---|---|---|
| Do selection / current line | <kbd>CTRL</kbd>+<kbd>d</kbd> or <kbd>CMD</kbd>+<kbd>Enter</kbd> | <kbd>CTRL</kbd>+<kbd>d</kbd> or <kbd>CTRL</kbd>+<kbd>Enter</kbd> |
| Run selection / current line quietly | <kbd>CTRL</kbd>+<kbd>r</kbd> | <kbd>CTRL</kbd>+<kbd>r</kbd> |
| Do the block around the cursor (or the whole file) | <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> | <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> |
| Insert a break line | <kbd>CTRL</kbd>+<kbd>s</kbd> | <kbd>CTRL</kbd>+<kbd>k</kbd>, <kbd>CTRL</kbd>+<kbd>s</kbd> |
| Help for the selected command | <kbd>F1</kbd> | <kbd>F1</kbd> |
| Data Browser for the selected variables | <kbd>F2</kbd> or <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>b</kbd> | <kbd>F2</kbd> |
| Toggle `/* */` (selection) or `//` (line) | <kbd>CMD</kbd>+<kbd>/</kbd> | <kbd>CTRL</kbd>+<kbd>/</kbd> |
| Word under the cursor → `` `word' `` | <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>\`</kbd> (selected text: <kbd>\`</kbd>) | <kbd>ALT</kbd>+<kbd>\`</kbd> |
| Insert date and time | <kbd>F5</kbd> | <kbd>F5</kbd> |

On Windows, <kbd>CTRL</kbd>+<kbd>d</kbd>, <kbd>CTRL</kbd>+<kbd>r</kbd> and <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> follow Stata's own Do-file Editor, so in Stata files they replace Sublime's *Quick Add Next*, *Goto Symbol* and *Duplicate Line*. Change them in `Preferences > Package Settings > Stata Improved Editor > Key Bindings`.

On macOS, <kbd>CMD</kbd>+<kbd>\`</kbd> is left to the system (switch windows), and <kbd>F2</kbd> is also Sublime's *Next Bookmark*: to get that back in Stata files add `{ "keys": ["f2"], "command": "next_bookmark" }` to your own key bindings, or use <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>b</kbd> for the Data Browser. To drop the `replace` template, delete `replace.sublime-snippet` or override its trigger.

New optional settings: `cd_to_file_directory` (make the file's folder Stata's working directory), `send_whole_lines` (send whole lines even if only part is selected) and `local_macros_persist` (keep local macros between sends).

Further tips:
* **Multi-select** (e.g. every occurrence of a variable) is a Sublime Text feature: select the word and press <kbd>CMD</kbd>+<kbd>d</kbd> repeatedly (<kbd>CTRL</kbd>+<kbd>d</kbd> on Windows/Linux, which this package uses in Stata files, so use <kbd>ALT</kbd>+<kbd>F3</kbd> there to select all occurrences).
* **Highlight more commands**: run `Stata Improved: Highlight Additional Commands` from the Command Palette and enter e.g. `esttab reghdfe` (kept in the `custom_commands` setting).
* **Macros** have their own color scope (`variable.other.macro`) for both `` `local' `` and `$global`/`${global}`, so a color scheme can show them alike.
* **Your own snippets**: save a `.sublime-snippet` file in `Packages/User` with `<scope>source.stata</scope>` and a `<tabTrigger>`, then type the trigger and press <kbd>Tab</kbd>. A snippet that appears in the completions list but does nothing usually has broken XML, e.g. a doubled closing tag such as `</scope>scope>`.

### 🎷Code Execution
<kbd>CTRL</kbd>+<kbd>d</kbd> -- Execute (do) selected codes. 
As opposite to "do" the code by <kbd>CTRL</kbd>+<kbd>d</kbd>, <kbd>CTRL</kbd>+<kbd>r</kbd> can "run" the code quietly in Stata. 

Note that if no code is selected, the current line of the code will be sent to Stata. 

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu1.gif" width="680">

### 🎷Matlab Style Execution for a Block
Say, you have the following do-file:
 
<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu2.png" width="680">

1) The "break line" can be simply inserted by <kbd>CTRL</kbd>+<kbd>s</kbd> (Windows: <kbd>CTRL</kbd>+<kbd>k</kbd>, <kbd>CTRL</kbd>+<kbd>s</kbd>).

2) Put the cursor within a block, click  <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd>  to execute this block.

### 🎷Run the whole do-file (NEW)
If there is no code blocks are defined by the aforementioned "break line", clicking <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> could execute the whole script.

### 🎷Section Header, Comments toggle, and To Do List.
Type `comm-s`, you will have a section header:

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu4.gif" width="550">

🏊 you might also try `comm-subsec` to trigger a sub-section header.

Type `comm-l`, you will insert a line of comments:

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu3.gif" width="550">

Type `comm-t`, you will insert to do list:

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu5.gif" width="550">


Remember to press <kbd>TAB</kbd> to fill up these templates!!!

### 🎷For loops template
Type `for...`, you will trigger a auto-completed for loop template, such as:

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu6.gif" width="550">

Remember to press <kbd>TAB</kbd> to fill up this template.

### 🎷Write a program 
Type `prog...`, you will trigger:

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu7.gif" width="550">

Press <kbd>TAB</kbd> define the name of the program.




### 🎷Commands auto-completion
We are updating/incorprating more templates/snippets for Stata commands.

Current, there are a few auto-completions. For instance, when type `merge`, you will trigger

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu8.gif" width="550">

Again, press <kbd>TAB</kbd> to fill up this template.

### 🎷Macros - Local and Global
Select any word, press <kbd>\`</kbd> to make it as 'word'. 

Select any word, press `$` to make it as ${word}. And select ${word} press `$` to make it as word.

🏊New: If you did not select any word but put the cursor in a word, then pressing `CMD+`<kbd>\`</kbd> can also make it as 'word'.

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu9.gif" width="550">

### 🎷Toggle comments
Select any word, press <kbd>CMD</kbd> +<kbd>/</kbd> to make the selected word toggled.

And press <kbd>CMD</kbd> +<kbd>/</kbd>  again to make toggled word  to original word.


<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu10.gif" width="550">


### 🎷Help File 
 Select any command, press <kbd>F1</kbd>  to see the help file. 

### 🎷Data Browser
Select any variable(s), press <kbd>F2</kbd>  to see the data browser.

### 🎷DEMO (YouTube)
https://www.youtube.com/watch?v=4vvsk8lG6fY&t=389s

## Multiple Instances of Stata
**macOS:** If you openned multiple instances of Stata, please note that this plugin will send the code to your MOST RECENTLY OPENNED Stata session. 

If different versions of Stata are installed in your Mac (e.g. both Stata 14 and Stata 15), the plugin will send code to the most updated version of Stata (i.e. Stata 15). To use another version, set e.g. `"stata_version": 17` in `Preferences > Package Settings > Stata Improved Editor > Settings`.

**Windows:** code goes to the Stata window that is on top of the others, i.e. the one you used most recently (a minimized Stata counts last). If no Stata is running, the newest installed Stata is started (or the one set in `"stata_path"`). If you start Stata yourself and send code right away, the plugin waits for that Stata instead of starting a second one.


 
 
## Background information:
1, This plugin is motivated by the article ["Some notes on text editors for Stata users"](http://fmwww.bc.edu/repec/bocode/t/textEditors.html#vim) By Nicolas J. Cox, and some part of the code is motivated and modified based on following packages: [StataEditor](https://github.com/mattiasnordin/) for the auto-completion, and [StataEnhanced by Andrew Heiss] (https://github.com/andrewheiss/) for the AppleScript.
).

This plugin basically creates a temporary do-file, which is then sent to the Stata to execute. Temporary do-files are kept in a `StataImproved` folder inside the system temp directory and removed after a day.


2, This package supports macOS (AppleScript) and Windows (typing into Stata's Command window; optionally Stata Automation). Linux is not supported yet.
 
        
3, This plugin has been tested on macOS Monterey and (Windows 11, Sublime Text 4 build 4215) with Stata 18; it is meant to support Stata 13-19 (StataNow) SE/MP/IC.


## 🎼 Update history 🎼 
**v2.0.0**: **Sublime Text 4** and **Windows** support; key bindings scoped to Stata files; fixes #3 (`local_macros_persist`), #9, #19, #20 (`cd_to_file_directory`), #21, #24, #25 (`send_whole_lines`), #27, #28 (and its duplicate #32), #29, #30, #34, #35, #37, #38, #39; docs for #14, #26, #31.

**v1.3.19 (01/Jan/26)**: Full support for **Stata 19** and  **StataNow** is made.  

**v1.3.17 (29/Apr/23)**: Full support for **Stata 18** is made.  

**v1.3.10 (11/May/21)**: Full support for **Stata 17** as well (in progress). Now one can select any word, press `$` to make it as ${word}. And select ${word}, press `$` to make it as word. Select any word, press <kbd>CMD</kbd> +<kbd>/</kbd> to make the selected word toggled. And press <kbd>CMD</kbd> +<kbd>/</kbd>  again to make toggled word  to original word.  

**v1.3.9 (12/Sep/20)**: Full support for **macOS Catalina** & **Stata 13, 14, 15 and 16 SE/MP/IC**.  

**v1.3.7 (01/Aug/19)**: Full support for **Stata 13, 14, 15 and 16 SE/MP/IC**.  

**v1.3.4 (28/May/18)**: Some minor corrections. Also thanks for [WildGunman](https://github.com/WildGunman)'s suggestion on the [package config directories](https://github.com/zizhongyan/StataImproved/pull/12).

**v1.3.3 (12/Aug/17)**: <kbd>CTRL</kbd>+<kbd>r</kbd> can **run** the code **quietly** in Stata (as opposed to **do** it noisily by <kbd>CTRL</kbd>+<kbd>d</kbd>). Thanks a lot for [Andrea Discacciati's](http://ki.se/en/people/anddis) suggestions.

**v1.3.1 (05/Aug/17)**: Stata 15 introduced [the Markdown Document feature](http://www.stata.com/new-in-stata/markdown/) which allow users to convert their narrative text, code and outputs into a elegantly formatted document (e.g. Word, PDF, or HTML files). In this update, we provide the **snippests** and **syntax highlighting**  for users to code the Stata markdown script **efficiently** (Many thanks for [PJ Paul's](https://github.com/pjpaulpj) suggestions). [Please click here to see how to use it.](https://github.com/zizhongyan/StataImproved/blob/master/messages/markdown.md)

**v1.3.0 (04/Aug/17)**: Full support for **Stata 13, 14 and 15 SE/MP/IC**.  

**v1.1.2 (08/Jun/17)**: The shortcut <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> can also be used to execute the WHOLE do-file if no Matlab-style code blocks are defined. Many thanks for [Alvaro Carril](http://alvarocarril.com/)'s suggestion on this! 

**v1.1.0 (14/Feb/17)**: We fixed the ctrl+d problem for users installed via package control! 


## License
MIT License

Copyright (c) 2016-2026 Zizhong Yan and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
