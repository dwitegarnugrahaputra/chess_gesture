import cv2
import mediapipe as mp
import math

class GestureController:
    def __init__(self, detection_confidence=0.7, tracking_confidence=0.5):
        # Inisialisasi MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1, # Kita hanya butuh mendeteksi satu tangan
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = None # Objek VideoCapture untuk kamera

        # Thresholds for gesture detection
        # Untuk pinch gesture (jari telunjuk dan jempol bersentuhan)
        self.PINCH_THRESHOLD = 0.04 # Nilai normalized. Sesuaikan ini untuk akurasi pinch.
                                     # Semakin kecil, semakin rapat jari harus bersentuhan.
        
        # Threshold untuk mendeteksi jari terbuka (saat hover/tidak klik)
        # Jika Anda ingin menggunakan is_hand_open untuk gestur hover, pastikan threshold ini pas
        self.OPEN_FINGER_THRESHOLD = 0.1 # Nilai normalized. Jarak antara ujung jari dan sendi di bawahnya.


    def start_camera(self, camera_id=0):
        """Memulai stream dari kamera."""
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {camera_id}.")
            return False
        return True

    def stop_camera(self):
        """Menghentikan stream kamera."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def process_frame(self, frame):
        """Memproses satu frame untuk deteksi tangan dan gestur."""
        # Ubah BGR ke RGB (MediaPipe membutuhkan RGB)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False # Tandai gambar sebagai tidak dapat ditulis untuk performa

        # Proses gambar dengan MediaPipe Hands
        results = self.hands.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # Ubah kembali ke BGR

        hand_landmarks = None
        if results.multi_hand_landmarks:
            # Kita hanya peduli pada tangan pertama yang terdeteksi
            hand_landmarks = results.multi_hand_landmarks[0]
            # Opsional: Gambarkan landmark di frame (untuk debugging visual)
            # Anda bisa mengaktifkan ini jika ingin melihat landmark di jendela kamera debug
            self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        return image, hand_landmarks

    def get_hand_position(self, hand_landmarks, img_width, img_height):
        """
        Mengambil posisi kursor dari landmark ujung jari telunjuk.
        """
        if hand_landmarks:
            # Menggunakan landmark INDEX_FINGER_TIP (ujung jari telunjuk) sebagai posisi kursor
            index_finger_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            # Konversi koordinat normalisasi (0.0-1.0) ke koordinat piksel
            cx, cy = int(index_finger_tip.x * img_width), int(index_finger_tip.y * img_height)
            return cx, cy
        return None, None

    def is_hand_closed(self, hand_landmarks):
        """
        Mengecek apakah gestur 'pinch' (jari telunjuk dan jempol bersentuhan) terdeteksi.
        """
        if not hand_landmarks:
            return False
        
        # Dapatkan koordinat landmark penting
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Hitung jarak Euclidean 3D antara thumb_tip dan index_tip
        distance = math.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2 + 
            (thumb_tip.z - index_tip.z)**2 
        )
        
        # Jika jarak kurang dari threshold, anggap sebagai "pinch" (tertutup)
        return distance < self.PINCH_THRESHOLD

    def is_hand_open(self, hand_landmarks):
        """
        Mengecek apakah tangan 'terbuka' (jari telunjuk dan tengah terentang).
        Metode ini sekarang menggunakan self.OPEN_FINGER_THRESHOLD.
        """
        if not hand_landmarks:
            return False
        
        # Hanya memeriksa jari telunjuk (INDEX) dan jari tengah (MIDDLE)
        fingers_to_check = {
            "INDEX": [self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP],
            "MIDDLE": [self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        }

        open_fingers_count = 0
        for finger_name, landmarks_indices in fingers_to_check.items():
            tip = hand_landmarks.landmark[landmarks_indices[0]] # Ujung jari
            pip = hand_landmarks.landmark[landmarks_indices[1]] # Sendi di bawah ujung jari
            
            # Hitung jarak antara ujung jari dan sendi PIP (Proximal InterPhalangeal)
            # Jika jari lurus/terbuka, jarak ini akan lebih besar
            distance = math.sqrt((tip.x - pip.x)**2 + (tip.y - pip.y)**2 + (tip.z - pip.z)**2)
            
            # Jika jaraknya di atas threshold, anggap jari itu terbuka/lurus
            if distance > self.OPEN_FINGER_THRESHOLD: # Menggunakan threshold dari __init__
                open_fingers_count += 1
        
        # Anggap tangan terbuka jika kedua jari (telunjuk dan tengah) terbuka
        return open_fingers_count >= 2