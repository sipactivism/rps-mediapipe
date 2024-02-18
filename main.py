import cv2
import numpy as np
import mediapipe as mp
import math
import random
import pymsgbox
from time import time, sleep
from PIL import ImageFont, ImageDraw, Image

from mediapipe.tasks import python
from mediapipe.tasks.python import vision, BaseOptions
from mediapipe.tasks.python.vision import GestureRecognizer, GestureRecognizerOptions, HandLandmarker, HandLandmarkerOptions

# get gesture_recognizer.task from https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task
GESTURE_RECOGNITION_OPTIONS = BaseOptions(model_asset_path="gesture_recognizer.task")
GESTURES = {"Open_Palm": "🖐","Closed_Fist": "✊","Victory": "✌","None":"❌"}
MATCHUPS = {
    "Open_Palm": {
        "Defeats": "Closed_Fist",
        "Loses To": "Victory"
    },
    "Closed_Fist": {
        "Defeats": "Victory",
        "Loses To": "Open_Palm"
    },
    "Victory": {
        "Defeats": "Open_Palm",
        "Loses To": "Closed_Fist"
    }
}
COUNTDOWN_TIME = 3
ROUND_COUNT = 10

recognizer = GestureRecognizer.create_from_options(GestureRecognizerOptions(base_options=GESTURE_RECOGNITION_OPTIONS))

def draw_emoji(frame,text: str,loc: tuple):
    pil_img = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_img)
    draw.text(loc,text,fill=(0,0,0),font=ImageFont.truetype("Noto_Emoji\\static\\NotoEmoji-Regular.ttf",100))
    return np.array(pil_img)

def game_loop(cap: cv2.VideoCapture):
    score = {
        "Player": 0,
        "Computer": 0
    }
    gesture_list = list(GESTURES.keys())
    gesture_list.remove("None")
    running = True
    # choose random gesture
    while running:
        text = "❓"
        for round in range(1,ROUND_COUNT+1):
            text = "❓"
            computer_gesture = random.choice(gesture_list)
            #print(computer_gesture)
            player_gesture = None
            start_time = time()
            end_time = start_time + COUNTDOWN_TIME
            # timer
            while time() < end_time:
                _, frame = cap.read()
                width, height, _ = frame.shape
                # convert to mediapipe's image format
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB,data=frame)
                # feed into recognizer
                result = recognizer.recognize(mp_img)
                # check if gesture is found
                if len(result.gestures) > 0:
                    located_gesture = result.gestures[0][0]
                    # is it the gesture
                    if located_gesture.category_name in gesture_list:
                        player_gesture = located_gesture.category_name
                        print(f"Gesture change: {player_gesture}")
                # add emoji
                remaining_time = end_time - time()
                print(remaining_time)
                if remaining_time <= 0.05:
                    text = GESTURES[computer_gesture]
                    # it works
                    remaining_time = -1
                cv2.putText(frame,str(math.floor(remaining_time)+1),(int(width / 2) + 20,int(height / 2)),1,20,(255,0,0),10)
                cv2.putText(frame,"Current gesture:",(50,(int(height / 2) - 10)),1,1.5,(255,0,0),2)
                cv2.putText(frame,f"Round {round}/{ROUND_COUNT}",(width - 50,50),1,2,(255,0,0),2)
                cv2.putText(frame,f"{score['Player']}-{score['Computer']}",(width - 50,80),1,2,(255,0,0),2)
                if player_gesture != None:
                    frame = draw_emoji(frame,GESTURES[player_gesture],(50,int(height / 2)))
                frame = draw_emoji(frame,text,(50,50))
                cv2.imshow("frame",frame)
                cv2.waitKey(1)
            if(not player_gesture):
                print("No contest")
            elif(player_gesture == computer_gesture):
                print("Tie!")
            elif(MATCHUPS[player_gesture]["Defeats"] == computer_gesture):
                print("Win against the computer!")
                score["Player"] += 1
            elif(MATCHUPS[player_gesture]["Loses To"] == computer_gesture):
                print("Loss against the computer!")
                score["Computer"] += 1
            sleep(1)
        running = False
    again = pymsgbox.confirm(f"Final score: {score['Player']}-{score['Computer']}. Would you like to try again?","Try again?",buttons=["Yes","No"])
    if again == "Yes":
        # run entire function again
        game_loop(cap)
def setup():
    cap = cv2.VideoCapture(0)
    game_loop(cap)
    cap.release()
    cv2.destroyAllWindows()

setup()
