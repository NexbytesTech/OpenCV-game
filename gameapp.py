import sys
import random
import time
import cv2
import mediapipe as mp
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

# Global leaderboard
leaderboard = []

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Tracking Game")
        self.setGeometry(100, 100, 600, 400)

        self.start_button = QPushButton("Start Game", self)
        self.start_button.setGeometry(200, 100, 200, 50)
        self.start_button.clicked.connect(self.start_game)

        self.leaderboard_button = QPushButton("Leaderboard", self)
        self.leaderboard_button.setGeometry(200, 200, 200, 50)
        self.leaderboard_button.clicked.connect(self.show_leaderboard)

    def start_game(self):
        self.game_window = GameWindow()
        self.game_window.show()

    def show_leaderboard(self):
        self.leaderboard_window = LeaderboardWindow()
        self.leaderboard_window.show()

# Game Window
class GameWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game")
        self.setGeometry(100, 100, 800, 600)
        self.score = 0
        self.start_time = time.time()
        self.time_limit = 30  # Initial game time
        self.last_move_time = time.time()
        self.x_enemy = random.randint(50, 600)
        self.y_enemy = random.randint(50, 400)
        self.enemy_color = (0, 255, 0)
        self.running = True

        # OpenCV Video Capture
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Mediapipe setup
        self.mp_hands = mp.solutions.hands.Hands(
            min_detection_confidence=0.8, min_tracking_confidence=0.5
        )

        # Layout
        self.image_label = QLabel(self)
        self.image_label.setGeometry(0, 0, 800, 600)

    def update_frame(self):
        if not self.running:
            return

        _, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Hand detection
        results = self.mp_hands.process(image)

        # Draw enemy
        cv2.circle(image, (self.x_enemy, self.y_enemy), 25, self.enemy_color, 5)

        # Timer and score display
        remaining_time = int(self.time_limit - (time.time() - self.start_time))
        cv2.putText(image, f"Time: {remaining_time}s", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, f"Score: {self.score}", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # End game if time runs out
        if remaining_time <= 0:
            self.end_game()
            return

        # Move enemy randomly
        if time.time() - self.last_move_time > 2:
            self.x_enemy = random.randint(50, 600)
            self.y_enemy = random.randint(50, 400)
            self.last_move_time = time.time()

        # Check for hand collisions
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for point in mp.solutions.hands.HandLandmark:
                    if point == mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP:
                        landmark = hand_landmarks.landmark[point]
                        x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
                        cv2.circle(image, (x, y), 15, (255, 0, 0), -1)
                        if abs(x - self.x_enemy) < 25 and abs(y - self.y_enemy) < 25:
                            self.score += 1
                            self.time_limit += 5
                            self.x_enemy = random.randint(50, 600)
                            self.y_enemy = random.randint(50, 400)
                            self.enemy_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        # Convert the image to QImage for PyQt5
        h, w, ch = image.shape
        q_image = QImage(image.data, w, h, ch * w, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_image))

    def end_game(self):
        self.running = False
        self.timer.stop()
        self.cap.release()
        leaderboard.append(self.score)
        self.close()

# Leaderboard Window
class LeaderboardWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Leaderboard")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Rank", "Score"])
        self.update_leaderboard()
        self.layout.addWidget(self.table)

    def update_leaderboard(self):
        sorted_scores = sorted(leaderboard, reverse=True)
        self.table.setRowCount(len(sorted_scores))
        for i, score in enumerate(sorted_scores):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(score)))

# Run the App
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
