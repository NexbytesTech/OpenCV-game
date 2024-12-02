import sys
import random
import time
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QComboBox, QTextEdit
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import mediapipe as mp


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Tracking Game")
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.showFullScreen()

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Header Layout
        self.header_layout = QHBoxLayout()
        self.layout.addLayout(self.header_layout)

        self.level_selector = QComboBox(self)
        self.level_selector.addItems(["Easy", "Medium", "Hard"])
        self.level_selector.setStyleSheet(
            "padding: 5px; font-size: 16px; color: black; background-color: lightgreen;"
        )
        self.level_selector.currentIndexChanged.connect(self.update_level_color)
        self.header_layout.addWidget(self.level_selector)

        self.start_button = QPushButton("Start Game", self)
        self.start_button.setStyleSheet("background-color: #00cc00; font-size: 18px; padding: 10px;")
        self.start_button.clicked.connect(self.start_game)
        self.header_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Game", self)
        self.stop_button.setStyleSheet("background-color: #cc0000; font-size: 18px; padding: 10px;")
        self.stop_button.clicked.connect(self.stop_game)
        self.header_layout.addWidget(self.stop_button)
        self.stop_button.setEnabled(False)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.setStyleSheet("background-color: #333333; font-size: 18px; padding: 10px;")
        self.exit_button.clicked.connect(self.close_application)
        self.header_layout.addWidget(self.exit_button)

        self.leaderboard_text = QTextEdit(self)
        self.leaderboard_text.setReadOnly(True)
        self.leaderboard_text.setStyleSheet("background-color: #333333; color: white; font-size: 14px; padding: 10px;")
        self.layout.addWidget(self.leaderboard_text)

        # Game Display Area
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #00ff00; background-color: #000;")
        self.layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        # Game Variables
        self.cap = None
        self.running = False
        self.score = 0
        self.time_limit = 30
        self.enemy_color = (0, 255, 0)  # Consistent enemy color
        self.x_enemy = random.randint(100, 700)
        self.y_enemy = random.randint(100, 500)
        self.enemy_last_seen = time.time()
        self.start_time = time.time()
        self.last_move_time = time.time()
        self.difficulty_factor = 1.0

        # Mediapipe Hand Detection
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8,
        )

        # Timer for Game Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Display Leaderboard
        self.update_leaderboard()

    def update_level_color(self):
        level = self.level_selector.currentText()
        if level == "Easy":
            self.level_selector.setStyleSheet("padding: 5px; font-size: 16px; color: black; background-color: lightgreen;")
        elif level == "Medium":
            self.level_selector.setStyleSheet("padding: 5px; font-size: 16px; color: black; background-color: yellow;")
        elif level == "Hard":
            self.level_selector.setStyleSheet("padding: 5px; font-size: 16px; color: black; background-color: red;")

    def start_game(self):
        # Set difficulty based on level
        level = self.level_selector.currentText()
        if level == "Easy":
            self.difficulty_factor = 1.0
        elif level == "Medium":
            self.difficulty_factor = 1.5
        elif level == "Hard":
            self.difficulty_factor = 2.0

        self.running = True
        self.cap = cv2.VideoCapture(0)
        self.score = 0
        self.time_limit = 30
        self.start_time = time.time()
        self.enemy_last_seen = time.time()
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.timer.start(20)  # Update every 20 ms

    def update_frame(self):
        if not self.running:
            return

        _, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Hand detection
        results = self.mp_hands.process(image)

        # Draw enemy
        if time.time() - self.enemy_last_seen > 3:  # Enemy disappears after 3 seconds
            self.x_enemy = random.randint(100, image.shape[1] - 100)
            self.y_enemy = random.randint(100, image.shape[0] - 100)
            self.enemy_last_seen = time.time()

        cv2.circle(image, (self.x_enemy, self.y_enemy), 25, self.enemy_color, -1)

        # Timer and score display
        remaining_time = int(self.time_limit - (time.time() - self.start_time) * self.difficulty_factor)
        cv2.putText(image, f"Time: {remaining_time}s", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, f"Score: {self.score}", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # End game if time runs out
        if remaining_time <= 0:
            self.end_game()
            return

        # Check for collisions and update score
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Index finger tip
                index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                x = int(index_tip.x * image.shape[1])
                y = int(index_tip.y * image.shape[0])

                # Draw fingertip
                cv2.circle(image, (x, y), 15, (255, 0, 0), -1)

                # Check for collision
                if abs(x - self.x_enemy) < 25 and abs(y - self.y_enemy) < 25:
                    self.score += 1
                    self.time_limit += 5
                    self.x_enemy = random.randint(100, image.shape[1] - 100)
                    self.y_enemy = random.randint(100, image.shape[0] - 100)
                    self.enemy_last_seen = time.time()

        # Convert frame to QPixmap
        h, w, ch = image.shape
        q_image = QImage(image.data, w, h, ch * w, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_image))

    def stop_game(self):
        self.end_game()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def end_game(self):
        self.running = False
        self.timer.stop()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

        # Save score to leaderboard
        with open("leaderboard.txt", "a") as f:
            f.write(f"Score: {self.score}\n")

        self.update_leaderboard()

    def update_leaderboard(self):
        try:
            with open("leaderboard.txt", "r") as f:
                scores = f.readlines()
        except FileNotFoundError:
            scores = []

        scores = sorted([int(s.strip().split(": ")[1]) for s in scores if s.strip()], reverse=True)[:5]
        self.leaderboard_text.setPlainText("\n".join([f"{i + 1}. Score: {score}" for i, score in enumerate(scores)]))

    def close_application(self):
        self.stop_game()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())
