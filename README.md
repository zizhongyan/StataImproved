# Improved Stata Editor for macOS : a sublime text 3 plugin

The Sublime Text 3 (ST3) is probably the most popular text editor under the macOS platform. This plugin (beta) is committed to making the ST3 to be the favourable Stata do-file editor for Mac users.  

(Last edited on 25th Nov 2016 by [Z Yan](mailto:helloyzz@gmail.com) and [C Wang](mailto:flora7819@gmail.com) )

## Main Features
#### 1, Execute the selected do-file 
#### 2, Split the do-file into cells, and execute a block of do-file (just like what you do in Matlab) !!
#### 3, Automated Section Header, Comments toggle, and To Do List.
#### 4, Auto-completion for i) common used commands, ii) for loops, iii) writing program.
#### 5, Select any word, press \` to make it as \`word'. 
#### 6, Select any word, press `cmd+4` to make it as ${word}. 
#### 7, Select any command, press `F1` to see the help file. 
#### 8, Select any variable(s), press `F2` to see the data browser. 
#### 9, Improved Stata Syntax-highlighting  



## Usage 
### Code Execution
`ctrl+d` -- Execute selected codes. if no code is selected, execute the current line.
### Matlab Style Execution for a Block
Say, you have the following do-file:
 
    /* -Piu_Sign- (Code Break Line) - (by Stata Editor for macOS (github) )  */
    
    use http://www.stata-press.com/data/r13/nlswork, clear
    merge 1: m price using auto.dta 
    return list
    
    /* -Piu_Sign- (Code Break Line) - (by Stata Editor for macOS (github) )  */
    
    sysuse auto, clear
    reg price  weight
    display _b[weight]
    ereturn list
    mat b = e(b)
    
    /* -Piu_Sign- (Code Break Line) - (by Stata Editor for macOS (github) )  */
1) The "break line" can be simply inserted by `ctrl+s`.

2) Put the cursor within a block, click  `ctrl+shift+d` to execute this block.

### Automated Section Header, Comments toggle, and To Do List.
Type `comm-h`, you will have a section header:

    *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
    /*  Section: title        
        Notes: */
    *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
    Content  
    
    
    
    *-*-*-*-*-*-*-* End of the Section title *-*-*-*-*-*-*-*-*-*-*

Type `comm-l`, you will insert a line of comments:

    /* [> insert here <] */ 

Type `comm-t`, you will insert to do list:

    /*------------------------- 
    To Do:
       1.first  
       2.second  
    -------------------------*/ 



Remember to press `tab` to fill up these template!!!

### Automated For loops
Type `for...`, you will trigger a auto-completed for loop template, such as:

    forvalues j = 1 (1) n {
    	$0
    }  // end of forvalues j = 1 (1) n

Remember to press `tab` to fill up this template.

### Automated program
Type `prog...`, you will trigger:

    capture program drop Name
    program define Name
        $0
    end // end of program Name

Press `tab` define the name of the program.




### Command auto-completion
There are a few auto-completions. For instance, when type `merge`, you will trigger

    merge  1:?  variables? using "?.dta

Again, press `tab` to fill up this template.

### Macros
Select any word, press \` to make it as \`word'. 
Select any word, press `cmd+4` to make it as ${word}. 

### Help File 
 Select any command, press `F1` to see the help file. 

### Data Browser
Select any variable(s), press `F2` to see the data browser.

#Configurations

###Step 1, Installation
Two ways:

#### Install via package control. 
This method is safer and quicker. If you do not have the package control system in your ST3, you will need to install it in advance. To install it, please go to [this webpage](https://packagecontrol.io/installation).

1, In the ST3, press `super+shift+p` to have the package control box, type `package control: install package`, press enter. 

2, Then type `Stata Improved Editor macOS` you will find it from a dropdown list, and choose it to install. 

#### Or manually
Download these files from here, and unpack it into the folder: `~/Library/Application Support/Sublime Text 3/Packages`. How to access this folder? In the finder, press `super+shift+g`, type the folder path in the box, and press `enter`.

###Step 2, To ensure that the do-files are opened in the Stata by default and hence are executed  directly, we need to make the following two changes.

2.1. Uncheck the "Edit do-files opened from the Finder in Do-file Editor" in Preference>General Preference>Windows>Do-file Editor>Advanced (Stata 13/14), or Preferences > Do-file Editor > Advanced (Stata 12).

2.2. Ensure the do-files are opened in the Stata by default. If it is not, please:
Right click on any do-file under Finder > Open With > Select Stata from Applications folder > check "Always Open With" > Open.


 
#Background information:
1, This plugin is motivated by the article ["Some notes on text editors for Stata users"](http://fmwww.bc.edu/repec/bocode/t/textEditors.html#vim), and some part of the code is motivated and modified based on following packages, [stata package](github.com/docsteveharris), [StataEditor](github.com/mattiasnordin/), and [StataEnhanced](github.com/andrewheiss/
).

This plugin basically creates a temporary do-file, which is then sent to the Stata to execute.
The Stata13+ has introduced the AppleScript commands (i.e. DoCommand and DoCommandAsync) which allows script commands to directly enter the Stata without creating any temporary file. If you would use the AppleScript style plugin for Mac, you might use the StataEnhanced package by [Andrew Heiss](https://github.com/andrewheiss/SublimeStataEnhanced/)
However, we did not consider this option for two reasons:
 		   
i) AppleScript commands will go through all selected commands anyways even if the Stata has already reported an error message. This behaves quite differently from the Stata in-built do-file editor and could probably cause mistakes.
 		
ii) AppleScript commands sometimes do not work properly based on our own experience and tests, though we have not figured out the reason so far. Therefore we believe that creating a temporary do-file would be safer and more reliable and it behaves exactly the same as what the in-built do-file editor does. The temp file is harmless since it has just been temporarily saved in a cache folders in the macOS.
 
2, This package is the Mac only. For Windows users, please follow the instructions in the webpage above.

3, Some auto-completion code are based on StataEditor package (Version 0.7.0) by [Mattias Nordin](https://github.com/mattiasnordin/StataEditor), which works under the Windows platform.
        
4, This plugin has been tested on Mac OS X Yosemite, El Capitan and macOS, and supports Stata 12-14SE/MP/IC. (It should also work well with Stata 11, but has not been formally tested).
 
