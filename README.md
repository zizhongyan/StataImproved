# Improved Stata Editor for macOS : using sublime text 3

The Sublime Text 3 (ST3) is probably the most popular text editor under the macOS platform. This plugin (v.1.0.0) is committed to making the ST3 to be the favourable and handy Stata do-file editor for Mac users.  

* This package has been accepted by the [Sublime Text package manager](https://packagecontrol.io/packages/Stata%20Improved%20Editor) on 16th Jan 2017.
* Last edited on 16th Jan 2017 by [Zizhong Yan](mailto:helloyzz@gmail.com) and [Chuhong Wang](mailto:flora7819@gmail.com). Comments are welcome. 

## 🏆 Main Features
#### 1, Execute the selected do-file 
#### 2, Split the do-file into cells, and execute a block of do-file (just like what you do in Matlab) !!
#### 3, Automated way to write Comments toggle, create a Fancy Section Header, and a To Do List.
#### 4, Automatic template for i) writting common used commands, ii) for loops, iii) writing program.(We are updating/incorprating more templates/snippets for Stata commands.)
#### 5, Select any **word**, press <kbd>\`</kbd>, it will become \`**word**'. 
#### 6, Select any **word**, press <kbd>$</kbd>, it will become **${word}**. 
#### 7, Select any **word**, press <kbd>cmd</kbd>+<kbd>/</kbd>, it will become **/* word */**. 
#### 8, Select any command, press <kbd>F1</kbd> to see its help file. 
#### 9, Select any variable(s), press <kbd>F2</kbd> to see the data browser. 
#### 10, Press <kbd>F5</kbd>, insert the current date and time in the code.
#### 11, Stata Syntax-highlighting  

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
Open the ST3, click the Preferences-> Browse Packages-> Then you will reach the folder `~/Library/Application Support/Sublime Text 3/Packages`. Download [this Stata plugin from here](https://github.com/zizhongyan/StataImproved/archive/master.zip), and unpack the zip fil into that folder, and rename it as "StataImproved". 



## 🎷 Usage 
### 🎷Code Execution
<kbd>CTRL</kbd>+<kbd>d</kbd> -- Execute selected codes. if no code is selected, execute the current line. 

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu1.gif)
### 🎷Matlab Style Execution for a Block
Say, you have the following do-file:
 
![ScreenShot](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu2.png)

1) The "break line" can be simply inserted by <kbd>CTRL</kbd>+<kbd>s</kbd> .

2) Put the cursor within a block, click  <kbd>CTRL</kbd>+<kbd>SHIFT</kbd>+<kbd>d</kbd>  to execute this block.

### 🎷Automated Section Header, Comments toggle, and To Do List.
Type `comm-h`, you will have a section header:

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu4.gif)

Type `comm-l`, you will insert a line of comments:

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu3.gif)

Type `comm-t`, you will insert to do list:

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu5.gif)


Remember to press <kbd>TAB</kbd> to fill up these templates!!!

### 🎷Automated For loops
Type `for...`, you will trigger a auto-completed for loop template, such as:

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu6.gif)

Remember to press <kbd>TAB</kbd> to fill up this template.

### 🎷Automated program
Type `prog...`, you will trigger:

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu7.gif)

Press <kbd>TAB</kbd> define the name of the program.




### 🎷Command auto-completion
We are updating/incorprating more templates/snippets for Stata commands.

Current, there are a few auto-completions. For instance, when type `merge`, you will trigger

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu8.gif)

Again, press <kbd>TAB</kbd> to fill up this template.

### 🎷Macros
Select any word, press \` to make it as \`word'. 
Select any word, press `$` to make it as ${word}. 

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu9.gif)

### 🎷Toggle comments
Select any word, press <kbd>CMD</kbd> +<kbd>/</kbd> 

![demo](https://raw.githubusercontent.com/zizhongyan/StataImproved/master/pictures/tu10.gif)


### 🎷Help File 
 Select any command, press <kbd>F1</kbd>  to see the help file. 

### 🎷Data Browser
Select any variable(s), press <kbd>F2</kbd>  to see the data browser.

### 🎷DEMO (YouTube)
https://www.youtube.com/watch?v=4vvsk8lG6fY&t=389s

## Multiple Instances of Stata
If you openned multiple instances of Stata, please note that this plugin will send the code to your MOST RECENTLY OPENNED Stata session. 


 
 
## Background information:
1, This plugin is motivated by the article ["Some notes on text editors for Stata users"](http://fmwww.bc.edu/repec/bocode/t/textEditors.html#vim) By Nicolas J. Cox, and some part of the code is motivated and modified based on following packages: [StataEditor](https://github.com/mattiasnordin/) for the auto-completion, and [StataEnhanced by Andrew Heiss] (https://github.com/andrewheiss/) for the AppleScript.
).

This plugin basically creates a temporary do-file, which is then sent to the Stata to execute. All temporary cache files will be removed shortly when you close the Stata session.


2, This package is the Mac only. For Windows users, please follow the instructions in the Nicolas J. Cox's webpage above.
 
        
3, This plugin has been tested on Mac OS X Yosemite, El Capitan and macOS, and supports Stata 13 and 14 SE/MP/IC.
 
## Liciense
MIT License

Copyright (c) 2016 Zizhong Yan & Chuhong Wang

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
