# import the necessary packages
from uuid import SafeUUID
import numpy as np
import argparse
import cv2
from time import sleep
import paho.mqtt.client as mqtt
from threading import Thread
import json

State = True
webcam = None

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", default="deploy.prototxt.txt",
    help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", default="res10_300x300_ssd_iter_140000.caffemodel",
    help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.6,
    help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

with open("config.json") as conf:
    config = json.load(conf)

# mqtt connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    global State

    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    
    if (str(message.payload.decode("utf-8")) == "off"):
        State = False
    if (str(message.payload.decode("utf-8")) == "on"):
        State = True

client = mqtt.Client(config["mqttClient"])
client.username_pw_set(username=config["mqttUser"], password=config["mqttPass"])
client.on_connect = on_connect
client.on_message=on_message #attach function to callback

client.connect(config["mqttServer"], 1883, 60)

client.loop_start()

print("Subscribing to topic",(config["mqttTopic"] + "/cmd"))
client.subscribe((config["mqttTopic"] + "/cmd"))

# Define the thread that will continuously pull frames from the camera
class CameraBufferCleanerThread:
    def __init__(self):
        self._running = True
        self.last_frame = None

    def terminate(self):
        self._running = False

    def run(self, camera):
        self._running = True
        while self._running:
            ret, self.last_frame = camera.read()

# load serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

# create a cleaning thread object
cam_cleaner = CameraBufferCleanerThread()
t = None

#main loop
Startup = True
while True:
    if State:
        if Startup:
            # startup webcam
            print("[INFO] starting up webcam..")
            webcam = cv2.VideoCapture(0)

            # Start the cleaning thread
            t = Thread(target = cam_cleaner.run, args =(webcam, ))
            t.start()
            Startup = False
        
        if cam_cleaner.last_frame is not None:
            frame = cam_cleaner.last_frame

            # load the input image and construct an input blob for the image
            # by resizing to a fixed 300x300 pixels and then normalizing it
            image = frame
            (h, w) = image.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                (300, 300), (104.0, 177.0, 123.0))

            # pass the blob through the network and obtain the detections and
            # predictions
            print("[INFO] computing object detections...")
            net.setInput(blob)
            detections = net.forward()

            detected = False

            # loop over the detections
            for i in range(0, detections.shape[2]):
                # extract the confidence (i.e., probability) associated with the
                # prediction
                confidence = detections[0, 0, i, 2]
                # filter out weak detections by ensuring the `confidence` is
                # greater than the minimum confidence
                if confidence > args["confidence"]:
                    detected = True
                    print(confidence)
                    print("publishing occupied")
                    client.publish(config["mqttTopic"], "Occupied")
                    # client.publish((config["mqttTopic"] + "/confidence"), str(confidence))
            if not detected:
                print("publishing unoccupied")
                client.publish(config["mqttTopic"], "Unoccupied")
                # client.publish((config["mqttTopic"] + "/confidence"), str(confidence))
            sleep(2)
    if not State:
        # terminate the cleaning thread
        cam_cleaner.terminate()
    if t != None:
        if not State and not t.is_alive():
            # stop the webcam and set the startup variable
            webcam.release()
            Startup = True