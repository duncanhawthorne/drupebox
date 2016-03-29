# drupebox
Drupebox is a Dropbox sync script for the Raspberry Pi.

![](https://raw.githubusercontent.com/sarahschofield120/drupebox/master/icon.png)

There is no official Dropbox client for the Raspberry Pi as the Raspberry Pi uses an ARM based processor which is  not supported. This script provides an approximation of the functionality using the Dropbox API through a python script which can be run from the Raspbian terminal. The program will also work on other linux environments.

The drupebox script supports uploading, downloading, and syncing a folder on the computer to an app folder inside Dropbox. The terminal script can be run regularly, e.g. hourly through a cron job, to keep the folder regularly in sync.

The drupebox script was built having looked at other available scripts for the Raspberry Pi. These other scripts do not appear to cover a direct syncing of local folders with Dropbox, i.e. only uploading / downloading files where there have been changes made to keep the folder in sync. Drupebox achieves this goal. For reference, other Dropbox scripts can be found at https://github.com/GuoJing/Drop2PI and https://github.com/andreafabrizi/Dropbox-Uploader 

To run the script do the following:

Download the source code:
```
git clone https://github.com/duncanhawthorne/drupebox.git
```

Install dependencies for the script
```
sudo apt-get install python-configobj
```

Change directory into the Drupebox folder
```
cd drupebox
```

Run the drupebox script
```
python drupebox.py
```
The drupebox script with start an authorization with Dropbox.
* Click the link to dropbox that will appear in the terminal (or go to the link using a different computer).
* Log into Dropbox and approve the authorization for the app
* Dropbox will give you a code to paste back into the terminal window to complete the authorization
* Tell drupebox the folder on your computer to keep in sync with dropbox, or press enter to select the default folder /home/pi/Dropbox

Drupebox will then do an upload of what is in that folder
When the Drupebox script is run again, it will download/upload the local/remote additions/changes/deletions to keep the folder on your computer and the dropbox folder in sync.



*A raspberry is an aggregate fruit composed of small individual elements called drupes which together form the botanic berry.
