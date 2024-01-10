# Destiny 2 Autosplitter
Download from the latest release.

## About
This autosplitter uses Tesseract OCR to read the text from specific areas on the screen and uses that information
to decide when to split. Depending on the current split a different part of the screen will be recorded. 
<br>
At this point in time the following splits are available:
- New Objective
- Objective Complete
- Respawn Restricted
- Wipe Screen
- Joining Allies
- Boss Spawn
- Boss Dead
- Mission Completed
- Custom

The custom splits lets you input a text that the splitter will check for in the bottom left where messages
such as "Templar summons his legions" or "A relic has appeared" shows up. It is recommended to pick short strings
for the custom splits to ensure that it will be recognized even when the ocr misreads a minor part e.g. "legion" or "relic"
instead of the full prompt. Moreover not all prompts fit in the monitored area so in case of longer prompts
try to avoid using words from the end of the prompt.
<br><br>
<b>Disclaimer:</b> Due to the nature of ocr this splitter can be a bit cpu intense. On my R7 5800x it peaked at around 10% 
cpu usage.

## Livesplit Server
The autosplitter uses the LiveSplit Server to directly send splits to the livesplit client instead of emulating a button press
and also reading manuel splits to avoid desync. This is mandatory to use the tool otherwise a popup will prevent
you from using it until the livesplit server is started.
<br> 
Installation guide for LiveSplite Server: <br>
https://github.com/LiveSplit/LiveSplit.Server

## Features

### Start/Stop Autosplitter
Starting the autoplitter is indicated by the start-button as well as the first split being highlighted green.
During the run the currently monitored will continuously be highlighted green until the splitter is being stopped.

### Save/Load Splits
After creating a set of splits you can save them to a .txt file which can be loaded again at a later point.

### Add Split
When adding a split first select one of the available split options and then optionally use the checkbox for dummy or name.
Dummy will turn the split into a dummysplit which means it will be ignored which is used when you want to split e.g. a new objective
but not the next one. The name checkbox simply lets you give the split a name similar to livesplit splits
to identify them more easily.