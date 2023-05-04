# Drupebox
Drupebox is a Dropbox sync app built for the Raspberry Pi.

![](https://raw.githubusercontent.com/duncanhawthorne/drupebox/master/icon.png)

Drupebox enables Dropbox syncing on a Raspberry Pi using the Dropbox API, supporting uploading, downloading, and syncing a folder on your computer with an App folder inside Dropbox.

Drupebox is a python script which you run from the Raspberry Pi OS terminal. Drupebox can be run regularly (e.g. hourly or on each boot), to keep your folder regularly in sync.

How to use
-----------

Install dependencies for Drupebox
```
sudo apt-get install git python3-configobj python3-dropbox
```

Download Drupebox into the Drupebox script folder
```
git clone https://github.com/duncanhawthorne/drupebox.git
```

Run Drupebox
```
python3 drupebox/drupebox.py
```

Authorise Drupbox to sync your Dropbox folder
* Drupebox will start an authorization process with Dropbox.
* Click the link to Dropbox that will appear in the terminal (or visit that link using a different computer).
* Log into Dropbox and approve the authorization for the app. The app will only have authorization to a single App folder in Dropbox - the newly created "Drupebox" folder within the Apps folder. Drupebox will have no access to the rest of your Dropbox.
* Dropbox will give you a code to paste back into the terminal window to complete the authorization. This code will not leave your Raspberry Pi.
* Tell Drupebox the folder on your computer to keep in sync with Dropbox, or press enter to select the default folder /home/pi/Dropbox/.
* Your selected folder on your Raspberry Pi will then sync with the Drupebox folder.

Keep your folder in sync
* When Drupebox is first run, Drupebox will do an upload of the files in the folder on your Raspberry Pi to the newly created Drupebox folder in your Dropbox.
* When you run Drupebox again, it will download/upload the local/remote additions/changes/deletions to keep the folder on your Raspberry Pi and the Drupebox folder in Dropbox in sync. Files will be synced only where changes have been made.
* The Drupebox script can be run from a cron job to keep your folder constantly in sync. 

Drupebox also supports other linux environments.

*A raspberry is an aggregate fruit composed of small individual elements called drupes which together form the botanic berry.
