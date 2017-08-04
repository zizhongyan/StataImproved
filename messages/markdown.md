# Stata 15 Markdown in ST3  -- Snippet and Syntax Highlighting

Homepage: https://packagecontrol.io/packages/Stata%20Improved%20Editor

Last update for this page: 4/Aug/2017

*******
## ABOUT
*******

Stata 15 introduced the Markdown feature. The Stata Markdown can transform the narrative text, code and outputs into a elegantly formatted document (e.g. Word, PDF, or HTML files).

(For more information about Stata Markdown, please see http://www.stata.com/new-in-stata/markdown/, or this video: https://www.youtube.com/watch?v=vNry1vQiBxs )

Based on [PJ Paul's](https://github.com/pjpaulpj) comments, in this update, we provide the **snippests** for users to code the markdown script in ST3 efficiently. 

We also provide the **syntax highlighting** for the Stata Markdown documents.

*******
## SETUP
*******
1, In ST3, open/create a markdown script, which is normally a plain text file (e.g. txt). 

2, Navigate to: `View > Syntax > Open all with current extension as… > StataImproved > Stata`.

*****************
## USE THE SNIPPET
*****************
#### 1, type `dd_v` to trigger:

`<<dd_version: ... >>`

#### 2, type `dd_display` to trigger:

`<<dd_display:  .... >>`

#### 3, type `dd_display_number` to trigger:

`<<dd_display: %4.2f  .... >>`

#### 4, type `dd_do` to trigger:

`<<dd_do>>`

`....`

`<</dd_do>>`

#### 5, type `dd_ignore` to trigger:

`<<dd_ignore>>`

`....`

`<</dd_ignore>>`

#### 6, type `dd_tilde` for insert the `"~~~~"` delimiter.





