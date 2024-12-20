import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs

import mediapipe as mp
import cv2
import time
import random

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


score = 0
x_enemy = random.randint(50, 600)
y_enemy = random.randint(50, 400)
enemy_color = (0, 255, 0)
start_time = time.time()
time_limit = 30  # Initial game duration
last_move_time = time.time()

def draw_enemy_as_ring(image):
   
    global x_enemy, y_enemy, enemy_color
    cv2.circle(image, (x_enemy, y_enemy), 25, enemy_color, 5)  # Outer ring

def draw_text_with_border(image, text, position, font, scale, color, thickness, border_color, border_thickness):
   
    x, y = position
    cv2.putText(image, text, (x, y), font, scale, border_color, thickness + border_thickness)
    cv2.putText(image, text, (x, y), font, scale, color, thickness)


video = cv2.VideoCapture(1)
with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5) as hands:
    while video.isOpened():
        _, frame = video.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)
        imageHeight, imageWidth, _ = image.shape
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        
        remaining_time = int(time_limit - (time.time() - start_time))
        draw_text_with_border(image, f"Time: {remaining_time}s", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, (0, 0, 0), 2)
        draw_text_with_border(image, f"Score: {score}", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, (0, 0, 0), 2)

        if remaining_time <= 0:
            print(f"Game Over! Final Score: {score}")
            break

        
        if time.time() - last_move_time > 2:  # Slower movement interval
            x_enemy = random.randint(50, 600)
            y_enemy = random.randint(50, 400)
            last_move_time = time.time()

        
        draw_enemy_as_ring(image)

        if results.multi_hand_landmarks:
            for hand in results.multi_hand_landmarks:
                for point in mp_hands.HandLandmark:
                    if point == mp_hands.HandLandmark.INDEX_FINGER_TIP:
                        normalizedLandmark = hand.landmark[point]
                        pixelCoordinatesLandmark = mp_drawing._normalized_to_pixel_coordinates(
                            normalizedLandmark.x, normalizedLandmark.y, imageWidth, imageHeight
                        )
                        if pixelCoordinatesLandmark:
                            cv2.circle(image, (pixelCoordinatesLandmark[0], pixelCoordinatesLandmark[1]), 15, (255, 0, 0), -1)
                            
                            if abs(pixelCoordinatesLandmark[0] - x_enemy) < 25 and abs(pixelCoordinatesLandmark[1] - y_enemy) < 25:
                                score += 1
                                time_limit += 3  # Increase game duration by 5 seconds
                                x_enemy = random.randint(50, 600)
                                y_enemy = random.randint(50, 400)
                                enemy_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        cv2.imshow("Hand Tracking Game", image)

        if cv2.waitKey(10) & 0xFF == ord("q"):
            print(f"Final Score: {score}")
            break

video.release()
cv2.destroyAllWindows()
