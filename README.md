# AutoWipe Script
Author: Florian Oertel\
Email: florian.oertel@outlook.com

Used to automate blueprint/map wipes for Rust Game Servers running on linux, using LGSM.

<h3>Quick Installtion for Centos8.1:</h3>

<h4>Install needed RPMS (if missing)</h4>

```console
sudo dnf install git nano -y
```

<h4>Clone Repository And Prepare Files</h4>

```console
sudo mkdir /usr/local/bin/AutoWipe
cd /usr/local/bin/AutoWipe
sudo git clone https://github.com/flovest/AutoWipeScript.git ./
sudo chown -R ./ <serviceuser>
```

<h4>Configuration File "autowipe.json"</h4>

```console
"bp_wipe_days": [ "4" ]
#A list of days at which the server should execute the bp_wipe_command | 1=Monday ... 7=Sunday

"map_wipe_days": [ "4" ]
#A list of days at which the server should execute the map_wipe_command | 1=Monday ... 7=Sunday

"bp_wipe_time": "2200"
#Time in 24h HHMM format, that defines at which time the bp_wipe_command should be executed

"map_wipe_time": "1500"
#Time in 24h HHMM format, that defines at which time the map_wipe_command should be executed

"bp_wipe_types": [ "3" ]
#A list of types, that define the wipe algorithm
#Available Types:
#1=Weekly
#2=Every 2nd Week (where first wipe is first_bp_wipe/first_map_wipe)
#3=Every first weekday in "bp_wipe_days" of the current month
#4=Every second weekday in "bp_wipe_days" of the current month
#5=Every third weekday in "bp_wipe_days" of the current month
#6=Every fourth weekday in "bp_wipe_days" of the current month
#7=Every fifth weekday in "bp_wipe_days" of the current month

"map_wipe_types": [ "1" ]
#A list of types, that define the wipe algorithm
#Available Types see "bp_wipe_types"

"first_bp_wipe": "2021-2-2"
#Defines the first day of the blue print wipe. The bp_wipe_command won't execute before this date pasts. Dateformat has to match the given at "date_parse_format".

"first_map_wipe": "2021-1-21"
#Defines the first day of the blue print wipe. The map_wipe_command won't execute before this date pasts. Dateformat has to match the given at "date_parse_format".

"wipe_check_interval_seconds": "10"
#Defines the amount of seconds between the autowipe process checks if a new wipe has to be triggered.

"date_parse_format": "%Y-%m-%d"
#Declares the dateformat, that is used to parse the first_bp_wipe and the first_map_wipe.

"bp_wipe_command": "/usr/local/bin/AutoWipe/wipe.sh bpwipe"
#Command that is executed when a blueprint wipe is triggered.

"map_wipe_command": "/usr/local/bin/AutoWipe/wipe.sh mapwipe"
#Command that is executed when a map wipe is triggered.

"log_file_location": "/usr/local/bin/AutoWipe/autowipe.log"
#Location of the log file

"log_level": "4"
#Sets the log level.
#Log Levels:
#FATAL=1
#ERROR=2
#WARN=3
#INFO=4
#DEBUG=5
#TRACE=6

"time_zone": "CET"
#Time zone that is used to check the wipe time. If not given, the local timezone is taken.

"wipe_command_retries_on_fail": "-1"
#Declared the count of retries before the whole process terminates, when a wipe command does not exit with code 0. -1 equals infinite.

"append_date_to_logfile_name": "true"
#Should be true to avoid large log file and to have them seperated for each day.
```

<h4>Setting Up the Wipe Script</h4>
Since the autowipe.py script does only handle the logic about when a wipe is happening, the actual wipe is done with via the configuration bp/map-wipe-command. The checked-in wipe.sh, is a simple demonstation about how a wipe can be done using LGSM. Depending on the wipe procedure you choose, this script has to be adapted. If creating a completely new wipe script, make sure the script is executable 'chmod +x <path to wipe.sh>' and the service-user is able to execute it.

<h4>Create Systemd Service</h4>

```console
sudo nano /etc/systemd/system/autowipe.service
```
Paste the following text into the file and make sure to replace "[serviceuser]" with the name of the user this service should run with. In most cases you want to take the same user that runs the targeted rustserver instance.
```console
[Unit]
Description=Service for AutoWipe script by Florian Oertel
After=network.target

[Service]
User=[serviceuser]
Type=simple
ExecStart=/bin/bash -c "/usr/local/bin/AutoWipe/autowipe.py -c \"/usr/local/bin/AutoWipe/autowipe.json\""
RestartSec=15
Restart=always

[Install]
WantedBy=multi-user.target
```

<h4>Reload the Systemd Daemon</h4>

```console
sudo systemctl daemon-reload
```

<h4>Enable Service to auto run at start</h4>

```console
sudo systemctl enable autowipe
```

<h4>Start Service</h4>

```console
sudo systemctl start autowipe
```
