# Improved Stata Editor for macOS : using sublime text 3

The Sublime Text 3 (ST3) is probably the most popular text editor under the macOS platform. This plugin (beta) is committed to making the ST3 to be the favourable Stata do-file editor for Mac users.  

(Last edited on 1st Dec 2016 by [Z Yan](mailto:helloyzz@gmail.com) and [C Wang](mailto:flora7819@gmail.com). Comments are welcome. )

## Main Features
#### 1, Execute the selected do-file 
#### 2, Split the do-file into cells, and execute a block of do-file (just like what you do in Matlab) !!
#### 3, Automated Section Header, Comments toggle, and To Do List.
#### 4, Auto-completion for i) common used commands, ii) for loops, iii) writing program.
#### 5, Select any **word**, press \`, it will become **\`word'**. 
#### 6, Select any **word**, press `cmd+4`, it will become **${word}**. 
#### 7, Select any command, press `F1` to see its help file. 
#### 8, Select any variable(s), press `F2` to see the data browser. 
#### 9, Stata Syntax-highlighting  

## Installations 

Install the [Sublime Text 3 (ST3)](https://www.sublimetext.com/3). Open the ST3, Click the Preferences-> Browse Packages-> Then you will reach the folder `~/Library/Application Support/Sublime Text 3/Packages`. Download these files from this webpage by click the green button above (Clone and download, Download zip), and unpack the zip file into that folder. 

## Usage 
### Code Execution
`ctrl+d` -- Execute selected codes. if no code is selected, execute the current line. 

![demo](/pictures/tu1.gif)
### Matlab Style Execution for a Block
Say, you have the following do-file:

![demo](/pictures/tu2)
1) The "break line" can be simply inserted by `ctrl+s`.

2) Put the cursor within a block, click  `ctrl+shift+d` to execute this block.

### Automated Section Header, Comments toggle, and To Do List.
Type `comm-h`, you will have a section header:

![demo](/pictures/tu4.gif)

Type `comm-l`, you will insert a line of comments:

![demo](/pictures/tu3.gif)

Type `comm-t`, you will insert to do list:

![demo](/pictures/tu5.gif)


Remember to press `tab` to fill up these templates!!!

### Automated For loops
Type `for...`, you will trigger a auto-completed for loop template, such as:

![demo](/pictures/tu6.gif)

Remember to press `tab` to fill up this template.

### Automated program
Type `prog...`, you will trigger:

![demo](/pictures/tu7.gif)

Press `tab` define the name of the program.




### Command auto-completion
There are a few auto-completions. For instance, when type `merge`, you will trigger

![demo](/pictures/tu8.gif)

Again, press `tab` to fill up this template.

### Macros
Select any word, press \` to make it as \`word'. 
Select any word, press `cmd+4` to make it as ${word}. 

![demo](/pictures/tu9.gif)

### Help File 
 Select any command, press `F1` to see the help file. 

### Data Browser
Select any variable(s), press `F2` to see the data browser.

### DEMO (YouTube)
https://www.youtube.com/watch?v=4vvsk8lG6fY&t=389s

## Multiple Instances of Stata
If you openned multiple instances of Stata, please note that this plugin will send the code to your MOST RECENTLY OPENNED Stata session. 


 
 
#Background information:
1, This plugin is motivated by the article ["Some notes on text editors for Stata users"](http://fmwww.bc.edu/repec/bocode/t/textEditors.html#vim) By Nicolas J. Cox, and some part of the code is motivated and modified based on following packages: [StataEditor](https://github.com/mattiasnordin/) for the auto-completion, and [StataEnhanced by Andrew Heiss] (https://github.com/andrewheiss/) for the AppleScript.
).

This plugin basically creates a temporary do-file, which is then sent to the Stata to execute. All temporary cache files will be removed shortly when you close the Stata session.


2, This package is the Mac only. For Windows users, please follow the instructions in the Nicolas J. Cox's webpage above.
 
        
3, This plugin has been tested on Mac OS X Yosemite, El Capitan and macOS, and supports Stata 13 and 14 SE/MP/IC.
 
