# Face-Recognition-Activity
https://github.com/Lesekater/Face-Recognition-Activity

A script that checks if a face is detected in a webcam-feed and sends a "occupied" or "unoccupied" state to an mqtt topic


## Description

### `face-recognition-occupancy.py`
The Script acceses the local webcam and captures frames at an interval. These Frames are then evaluated by a ml model throught cv2. Based on the result it sends a "occupied" or "unoccupied" state to an mqtt topic.

The Script can be paused and resumed by sending ether "off" or "on" to the _configuredMqttTopic_/cmd.

---

## Installation

**Ubuntu**: A version of Python is already installed.  
**Mac OS X**: A version of Python is already installed.  
**Windows**: You will need to install one of the 3.x versions available at [python.org](http://www.python.org/getit/). (SCRIPT IS NOT TESTED!!)

## General usage information

1. Download the script.
2. Install the Dependencies. (pip install -r requirements.txt)
3. Configure the Script by creating an config.json (see configExample.json)
4. Run the script. (python3 face-recognition-occupancy.py)
