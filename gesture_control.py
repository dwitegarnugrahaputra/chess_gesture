import cv2
import mediapipe as mp
import math

class GestureController:
    def __init__(self, detection_confidence=0.7, tracking_confidence=0.5):
        # Inisialisasi MediaPipe Hands
        self.mp_hands = mp.solutions.hands # Mengakses modul hands dari MediaPipe
        self.hands = self.mp_hands.Hands( # Membuat objek Hands detection
            static_image_mode=False, # False berarti untuk video stream, True untuk gambar statis
            max_num_hands=1, # Kita cuma mau deteksi satu tangan aja
            min_detection_confidence=detection_confidence, # Konfidensi deteksi minimum
            min_tracking_confidence=tracking_confidence # Konfidensi pelacakan minimum
        )
        self.mp_drawing = mp.solutions.drawing_utils # Modul buat gambar landmark tangan
        self.cap = None # Variabel buat objek VideoCapture (kamera), awalnya None

        # Thresholds for gesture detection
        # Untuk pinch gesture (jari telunjuk dan jempol bersentuhan)
        self.PINCH_THRESHOLD = 0.04 # Nilai normalized. Sesuaikan ini untuk akurasi pinch.
                                     # Semakin kecil, semakin rapat jari harus bersentuhan.
        
        # Threshold untuk mendeteksi jari terbuka (saat hover/tidak klik)
        # Jika Anda ingin menggunakan is_hand_open untuk gestur hover, pastikan threshold ini pas
        self.OPEN_FINGER_THRESHOLD = 0.1 # Nilai normalized. Jarak antara ujung jari dan sendi di bawahnya.


    def start_camera(self, camera_id=0):
        """Memulai stream dari kamera."""
        # Coba gunakan backend DirectShow (cv2.CAP_DSHOW) sebagai alternatif dari default (MSMF)
        # Ini seringkali bisa mengatasi masalah "Failed to grab frame" di Windows
        self.cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW) # PERUBAHAN DI SINI!
        if not self.cap.isOpened(): # Mengecek apakah kamera berhasil dibuka dengan DSHOW
            print(f"Error: Could not open camera {camera_id} with CAP_DSHOW backend. Trying default backend as a fallback...")
            # Jika DSHOW gagal, coba backend default lagi (tanpa CAP_DSHOW) sebagai fallback
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {camera_id} with default backend either.")
                return False # Mengembalikan False kalo gagal
        
        # Tambahan pengecekan untuk memastikan kamera bisa membaca frame setelah dibuka
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Camera opened, but failed to grab first frame. It might be in use or corrupted.")
            self.cap.release() # Lepaskan kamera jika gagal membaca frame pertama
            return False

        print(f"Camera started successfully using backend: {'CAP_DSHOW' if cv2.CAP_DSHOW else 'Default'} for ID {camera_id}.")
        return True # Mengembalikan True kalo berhasil

    def stop_camera(self):
        """Menghentikan stream kamera."""
        if self.cap: # Kalo objek kamera (self.cap) ada
            self.cap.release() # Melepas sumber daya kamera
            self.cap = None # Mengatur ulang self.cap jadi None

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
            (thumb_tip.z - thumb_tip.z)**2 
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
