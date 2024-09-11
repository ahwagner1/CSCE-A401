# CSCE-A401

__Rough draft of what the scope adjustment scode could look like.__


## Tutorial
Connect to github and navigate to the folder you want to clone this repository too. 

Use the command `git clone git@github.com:ahwagner1/CSCE-A401.git` which will clone the files to your local repository

Run the file with `python ScopeAdjustment.py`

An application will open that has multiple fields.
 - First select __Upload Image__ and upload the __rifle_grouping.png__ image
 - Then specify the widht and the height of the target. I'm not sure the dimensions of the image in this repo so use your best guess if using that image
 - Next, click on the __Mark Shots__ button. This will allow you to select where on the target the shots hit. Just click on the shots on the target and a red dot will appear where you click
 - Finally, hit __Calculate Adjustment__. This will display a popup that specifies how much to adjust your rifle scope


### Some features that should be added
 - Undo button when marking shots
 - Inputs for target distance from rifle, bullet ballistics, and wind information

