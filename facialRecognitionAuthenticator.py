import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np

from random import randint
import pickle
import RPi.GPIO as GPIO
from time import sleep
import time
from google.cloud import storage
from firebase import firebase
import os
import schedule
firebase = firebase.FirebaseApplication("")


relay_pin = [26]
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, 1)


with open('labels', 'rb') as f:
    dict = pickle.load(f)
    f.close()

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))


faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
recognizer = cv2.face.createLBPHFaceRecognizer()
recognizer.load("trainer.yml")

font = cv2.FONT_HERSHEY_SIMPLEX

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = frame.array
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)
    for (x, y, w, h) in faces:
        roiGray = gray[y:y+h, x:x+w]

        id_, conf = recognizer.predict(roiGray)

        for name, value in dict.items():
            if value == id_:
                a = name

        if conf < 80:

            timer_a = time.time()
            while True:
                if time.time() - timer_a >= 0 and time.time() - timer_a < 5:
                    i = time.time() - timer_a
                    GPIO.output(relay_pin, 0)
                    #print ("ON")
                else:
                    #print ("OFF")
                    GPIO.output(relay_pin, 1)
                    break
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, a + str(conf), (x, y), font,
                        2, (0, 0, 255), 2, cv2.LINE_AA)
            print(a)
            # time.sleep(10)
            print("")

            # print("OFF")
        else:
            GPIO.output(relay_pin, 1)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.putText(frame, "UnAuth" + str(conf), (x, y),
                        font, 2, (0, 0, 255), 2, cv2.LINE_AA)
            for i in range(1):
                value = randint(1, 1000000)
                camera.capture(
                    "/home/pi/Desktop/testeun/unauth" + str(value) + ".jpg")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""
                client = storage.Client()
                bucket = client.get_bucket("")
# posting to firebase storage
                imageBlob = bucket.blob("/")
# imagePath = [os.path.join(self.path,f) for f in os.listdir(self.path)]
                time.sleep(5)
                imagePath = "/home/pi/Desktop/testeun/unauth" + \
                    str(value) + ".jpg"
                imageBlob = bucket.blob(
                    "/home/pi2/Desktop/testeun/unauth" + str(value) + ".jpg")
                imageBlob.upload_from_filename(imagePath)
# print(imageBlob.public_url)
                result = firebase.post(
                    '/myproject-1a164/unAuth/', imageBlob.public_url)
                print(imageBlob.public_url)
                # time.sleep(20)
    cv2.imshow('frame', frame)
    key = cv2.waitKey(1)
    rawCapture.truncate(0)
    if key == 27:
        break

cv2.destroyAllWindows()
