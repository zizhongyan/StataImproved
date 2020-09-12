# Improved Stata Editor for macOS : using sublime text 3

The Sublime Text 3 (ST3) is probably the most popular text editor under the macOS platform. This plugin (v.1.3.9) is committed to making the ST3 to be the favourable and handy Stata do-file editor for Mac users.  

* This package has been accepted by the [Sublime Text package manager](https://packagecontrol.io/packages/Stata%20Improved%20Editor) on 16th Jan 2017.
* Last edited on 1st Aug 2019 by [Zizhong Yan](mailto:helloyzz@gmail.com). Comments are welcome. 


## 🎼 News 🎼 
**v1.3.9 (12/Sep/20)**: Full support for **macOS Catalina** & **Stata 13, 14, 15 and 16 SE/MP/IC**.  

**v1.3.7 (01/Aug/19)**: Full support for **Stata 13, 14, 15 and 16 SE/MP/IC**.  

**v1.3.4 (28/May/18)**: Some minor corrections. Also thanks for [WildGunman](https://github.com/WildGunman)'s suggestion on the [package config directories](https://github.com/zizhongyan/StataImproved/pull/12).

**v1.3.3 (12/Aug/17)**: <kbd>CTRL</kbd>+<kbd>r</kbd> can **run** the code **quietly** in Stata (as opposed to **do** it noisily by <kbd>CTRL</kbd>+<kbd>d</kbd>). Thanks a lot for [Andrea Discacciati's](http://ki.se/en/people/anddis) suggestions.

**v1.3.1 (05/Aug/17)**: Stata 15 introduced [the Markdown Document feature](http://www.stata.com/new-in-stata/markdown/) which allow users to convert their narrative text, code and outputs into a elegantly formatted document (e.g. Word, PDF, or HTML files). In this update, we provide the **snippests** and **syntax highlighting**  for users to code the Stata markdown script **efficiently** (Many thanks for [PJ Paul's](https://github.com/pjpaulpj) suggestions). [Please click here to see how to use it.](https://github.com/zizhongyan/StataImproved/blob/master/messages/markdown.md)

**v1.3.0 (04/Aug/17)**: Full support for **Stata 13, 14 and 15 SE/MP/IC**.  

**v1.1.2 (08/Jun/17)**: The shortcut <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd> can also be used to execute the WHOLE do-file if no Matlab-style code blocks are defined. Many thanks for [Alvaro Carril](http://alvarocarril.com/)'s suggestion on this! 

**v1.1.0 (14/Feb/17)**: We fixed the ctrl+d problem for users installed via package control! 


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
Firstly you need to install the [Sublime Text 3 (ST3)](https://www.sublimetext.com/3).

### Installation via packge control. (easiest and recommended🏅)
The installation is very simple as this package has been accepted by the [Sublime Text package manager](https://packagecontrol.io). There are 3 steps:

* Open the ST3, from the main application menu, navigate to `Tools`, open the `Command Palette` (shortcut: <kbd>CMD</kbd>+<kbd>SHIFT</kbd>+<kbd>P</kbd>)
* Select `Package Control: Install Package`
* Search `Stata Improved Editor` and hit <kbd>Enter</kbd> to complete installation.

 
If you could not find the package control in your ST3, you will need to install it in advance. To install it, please go to [this webpage](https://packagecontrol.io/installation). 

Note that though the trial version of the ST3 is untimed and unlimited, the license need be purchased. 

### Manual installation
Open the ST3, click the Preferences-> Browse Packages-> Then you will reach the folder `~/Library/Application Support/Sublime Text 3/Packages`. Download [this Stata plugin from here](https://github.com/zizhongyan/StataImproved/archive/master.zip), and unpack the zip fil into that folder, and rename it as "Stata Improved Editor". 



## 🎷 Usage 
### 🎷Code Execution
<kbd>CTRL</kbd>+<kbd>d</kbd> -- Execute (do) selected codes. 
As opposite to "do" the code by <kbd>CTRL</kbd>+<kbd>d</kbd>, <kbd>CTRL</kbd>+<kbd>r</kbd> can "run" the code quietly in Stata. 

Note that if no code is selected, the current line of the code will be sent to Stata. 

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu1.gif" width="680">

### 🎷Matlab Style Execution for a Block
Say, you have the following do-file:
 
<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu2.png" width="680">

1) The "break line" can be simply inserted by <kbd>CTRL</kbd>+<kbd>s</kbd> .

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

Select any word, press `$` to make it as ${word}. 

🏊New: If you did not select any word but put the cursor in a word, then pressing `CMD+`<kbd>\`</kbd> can also make it as 'word'.

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu9.gif" width="550">

### 🎷Toggle comments
Select any word, press <kbd>CMD</kbd> +<kbd>/</kbd> 

<img src="https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu10.gif" width="550">


### 🎷Help File 
 Select any command, press <kbd>F1</kbd>  to see the help file. 

### 🎷Data Browser
Select any variable(s), press <kbd>F2</kbd>  to see the data browser.

### 🎷DEMO (YouTube)
https://www.youtube.com/watch?v=4vvsk8lG6fY&t=389s

## Multiple Instances of Stata
If you openned multiple instances of Stata, please note that this plugin will send the code to your MOST RECENTLY OPENNED Stata session. 

If different versions of Stata are installed in your Mac (e.g. both Stata 14 and Stata 15), the plugin will send code to the most updated version of Stata (i.e. Stata 15). 


 
 
## Background information:
1, This plugin is motivated by the article ["Some notes on text editors for Stata users"](http://fmwww.bc.edu/repec/bocode/t/textEditors.html#vim) By Nicolas J. Cox, and some part of the code is motivated and modified based on following packages: [StataEditor](https://github.com/mattiasnordin/) for the auto-completion, and [StataEnhanced by Andrew Heiss] (https://github.com/andrewheiss/) for the AppleScript.
).

This plugin basically creates a temporary do-file, which is then sent to the Stata to execute. All temporary cache files will be removed shortly when you close the Stata session.


2, This package is the Mac only. For Windows users, please follow the instructions in the Nicolas J. Cox's webpage above.
 
        
3, This plugin has been tested on Mac OS X Yosemite, El Capitan and macOS, and supports Stata 13, 14, 15 and 16 SE/MP/IC.
 
## License
MIT License

Copyright (c) 2016-2019 Zizhong Yan & Chuhong Wang

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
