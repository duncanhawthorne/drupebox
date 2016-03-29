# drupebox
Drupebox is a Dropbox sync script for the Raspberry Pi.

![](https://raw.githubusercontent.com/sarahschofield120/drupebox/master/icon.png =250x)

There is no official Dropbox client for the Raspberry Pi as the Raspberry Pi uses an ARM based processor. This script provides an approximation of the functionality using the Dropbox API through a bash script which can be run from the Raspbian terminal. The program will also work on other linux and unix type environments.

The script supports uploading, downloading, and syncing a folder on the computer to an app folder inside Dropbox. The terminal script can be run regularly, e.g. hourly through a cron job, to keep the folder regularly in sync.

This script was built having looked at other available scripts for the Raspberry Pi. These other scripts do not appear to cover a direct syncing of local folders with Dropbox, i.e. only uploading / downloading files where there have been changes made, additing , so I wrote Drupebox to achieve this goal. For reference, other dropbox scripts can be found at https://github.com/GuoJing/Drop2PI and https://github.com/andreafabrizi/Dropbox-Uploader 

To run the script:

Download the source code:
git clone https://github.com/duncanhawthorne/drupebox.git

Change directory into the Drupebox folder
cd drupebox

Install dependencies for the script
sudo apt-get install python-configobj

Run the drupebox script
python drupebox

The drupebox script with start an authorization with Dropbox.
Click the link to dropbox that will appear in the terminal (or go to the link using a different computer).
Log into Dropbox and approve the authorization for the app
Dropbox will give you a code to paste back into the terminal window to complete the authorization

Tell drupebox the local folder to keep in sync, or press enter to select the default folder /home/pi/Dropbox

Drupebox will do an initial upload of what is in that folder
When Drupebox is run subsequently, it will download/upload the local/remote additions/changes/deletions to keep the folder in sync.



*A raspberry is an aggregate fruit composed of small individual elements called drupes which together form the botanic berry.
