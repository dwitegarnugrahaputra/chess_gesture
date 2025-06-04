import pygame
import cv2
import chess

from gesture_control import GestureController
from chess_game import ChessGame
from gui_display import ChessGUI, WIDTH, HEIGHT, FPS, SQUARE_SIZE

# --- KONSTANTA BARU ---
CURSOR_SMOOTHING_FACTOR = 0.6 # Nilai antara 0.0 (tidak smoothing) dan 1.0 (smoothing maksimal)
                             # Rekomendasi: 0.2 - 0.8. Semakin tinggi, semakin halus tapi lambat responsnya.

class MainGame:
    def __init__(self):
        self.gesture_controller = GestureController()
        self.chess_game = ChessGame()
        self.gui = ChessGUI()

        self.running = False
        
        # current_cursor_x, current_cursor_y akan menyimpan posisi kursor yang SUDAH di-smoothing
        self.current_cursor_x, self.current_cursor_y = None, None 
        self.is_hand_closed = False
        self.prev_is_hand_closed = False
        
        self.selected_square_gui = None
        self.possible_moves_gui = []
        
        # Variabel untuk logika klik-lepas: "IDLE", "SELECTED_DRAG"
        self.click_state = "IDLE" 
        
        # Variabel baru untuk smoothing kursor. Inisialisasi di tengah layar agar tidak None
        self.smoothed_cursor_x = WIDTH // 2
        self.smoothed_cursor_y = HEIGHT // 2


    def start_game(self):
        """Memulai semua subsistem dan game loop."""
        if not self.gesture_controller.start_camera():
            print("Failed to start camera. Exiting.")
            return

        print("Camera started. Game is running.")
        self.running = True
        self.game_loop()

    def game_loop(self):
        """Loop utama permainan."""
        while self.running:
            # --- 1. Event Handling Pygame (untuk keluar) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # --- 2. Pemrosesan Kamera & Gestur ---
            ret, frame = self.gesture_controller.cap.read()
            if not ret:
                print("Failed to grab frame from camera.")
                self.running = False
                break
            
            # Flip frame secara horizontal agar lebih intuitif (seperti cermin)
            frame = cv2.flip(frame, 1)

            # Proses frame dengan MediaPipe
            display_frame, hand_landmarks = self.gesture_controller.process_frame(frame)
            
            img_h, img_w, _ = display_frame.shape
            cursor_x_raw, cursor_y_raw = self.gesture_controller.get_hand_position(hand_landmarks, img_w, img_h)
            
            # --- Terapkan Smoothing Kursor & Penanganan None ---
            if cursor_x_raw is not None and cursor_y_raw is not None:
                # --- START PERUBAHAN UNTUK ROI ---
                # BARIS 76: Definisikan ROI dalam persentase dari lebar/tinggi frame kamera
                # Contoh: hanya gunakan 80% bagian tengah frame (dari 10% hingga 90%)
                # Sesuaikan nilai-nilai ini (0.1, 0.9) berdasarkan kamera dan kenyamanan Anda.
                # Jika masalah utama di pojok kiri bawah, coba perkecil roi_x_start dan roi_y_start
                # Atau perkecil roi_x_end dan roi_y_end jika masalah di pojok kanan atas
                
                roi_x_start_perc = 0.05 # Contoh: mulai dari 5% dari kiri (lebih dekat ke tepi)
                roi_x_end_perc = 0.95   # Contoh: berakhir di 95% dari kiri (lebih dekat ke tepi)
                roi_y_start_perc = 0.05 # Contoh: mulai dari 5% dari atas
                roi_y_end_perc = 0.95   # Contoh: berakhir di 95% dari atas

                roi_x_start = int(img_w * roi_x_start_perc)
                roi_x_end = int(img_w * roi_x_end_perc)
                roi_y_start = int(img_h * roi_y_start_perc)
                roi_y_end = int(img_h * roi_y_end_perc)

                # BARIS 88: Pastikan kursor mentah berada di dalam ROI yang kita definisikan
                if roi_x_start <= cursor_x_raw <= roi_x_end and \
                   roi_y_start <= cursor_y_raw <= roi_y_end:
                    
                    # BARIS 91: Normalisasi ulang kursor berdasarkan ROI
                    # Ini memetakan posisi kursor dari ROI ke rentang 0.0 - 1.0 lagi
                    normalized_x_roi = (cursor_x_raw - roi_x_start) / (roi_x_end - roi_x_start)
                    normalized_y_roi = (cursor_y_raw - roi_y_start) / (roi_y_end - roi_y_start)

                    # BARIS 95: Skala kursor dari ROI normalized ke ukuran jendela Pygame
                    target_x = int(normalized_x_roi * WIDTH)
                    target_y = int(normalized_y_roi * HEIGHT)
                else:
                    # BARIS 99: Jika kursor di luar ROI, pertahankan posisi smoothing terakhir
                    # Ini mencegah kursor melompat jika tangan keluar dari area yang ditetapkan
                    target_x, target_y = self.smoothed_cursor_x, self.smoothed_cursor_y 
                # --- END PERUBAHAN UNTUK ROI ---

                # Smoothing menggunakan interpolasi linear (lerp)
                # Kursor yang di-smoothing bergerak menuju posisi target
                self.smoothed_cursor_x = int(self.smoothed_cursor_x * CURSOR_SMOOTHING_FACTOR + target_x * (1 - CURSOR_SMOOTHING_FACTOR))
                self.smoothed_cursor_y = int(self.smoothed_cursor_y * CURSOR_SMOOTHING_FACTOR + target_y * (1 - CURSOR_SMOOTHING_FACTOR))
                
                # Update posisi kursor yang akan digunakan oleh GUI dan logika game
                self.current_cursor_x = self.smoothed_cursor_x
                self.current_cursor_y = self.smoothed_cursor_y
            else:
                # Jika tangan tidak terdeteksi, set kursor menjadi None (tidak ditampilkan & tidak memicu aksi)
                self.current_cursor_x, self.current_cursor_y = None, None 

            # Deteksi status tangan (terbuka/tertutup)
            if hand_landmarks:
                self.is_hand_closed = self.gesture_controller.is_hand_closed(hand_landmarks)
            else:
                self.is_hand_closed = False

            # --- 3. Logika Game Berdasarkan Gestur (Klik-Lepas) ---
            current_hover_square_name = None
            # Pastikan kursor ada dan valid (bukan None) sebelum mencoba mendapatkan nama kotak
            if self.current_cursor_x is not None and self.current_cursor_y is not None:
                current_hover_square_name = self.gui.get_square_name_from_pixels(self.current_cursor_x, self.current_cursor_y)

            # --- Deteksi "Klik Down" (Tangan dari Terbuka -> Tertutup) untuk Memilih Bidak ---
            if self.is_hand_closed and not self.prev_is_hand_closed:
                # Hanya proses jika kursor valid dan game dalam state IDLE (belum ada bidak dipilih)
                if self.current_cursor_x is not None and self.current_cursor_y is not None and self.click_state == "IDLE":
                    if current_hover_square_name:
                        # Coba pilih kotak di bawah kursor
                        self.chess_game.select_square(current_hover_square_name)
                        self.selected_square_gui = self.chess_game.selected_square # Update highlight GUI
                        
                        if self.selected_square_gui: # Jika bidak berhasil dipilih
                            self.possible_moves_gui = self.chess_game.get_legal_moves(chess.square_name(self.selected_square_gui))
                            self.click_state = "SELECTED_DRAG" # Ubah state ke "sedang drag"
                        else: # Jika klik di kotak kosong atau bidak lawan tanpa pilihan sebelumnya
                            self.selected_square_gui = None
                            self.possible_moves_gui = []
                            self.click_state = "IDLE" # Tetap di IDLE
                    else: # Jika klik down di luar papan
                        self.click_state = "IDLE"

            # --- Deteksi "Klik Up" (Tangan dari Tertutup -> Terbuka) untuk Melakukan Langkah ---
            elif not self.is_hand_closed and self.prev_is_hand_closed:
                # Hanya proses jika kursor valid dan game dalam state SELECTED_DRAG (sudah ada bidak dipilih)
                if self.current_cursor_x is not None and self.current_cursor_y is not None and self.click_state == "SELECTED_DRAG":
                    if current_hover_square_name:
                        # Coba lakukan langkah ke kotak di bawah kursor
                        move_successful = self.chess_game.select_square(current_hover_square_name) # Panggil lagi select_square untuk move
                        
                        # Reset highlight dan state setelah mencoba langkah
                        self.selected_square_gui = self.chess_game.selected_square # Akan jadi None jika move berhasil/dibatalkan
                        self.possible_moves_gui = [] 
                    else: # Jika lepas klik di luar papan setelah memilih bidak
                        self.selected_square_gui = None # Batalkan pilihan
                        self.possible_moves_gui = []
                    self.click_state = "IDLE" # Kembali ke state IDLE

            # Simpan status gestur saat ini untuk deteksi transisi di iterasi berikutnya
            self.prev_is_hand_closed = self.is_hand_closed 

            # --- 4. Pembaharuan GUI ---
            self.gui.screen.fill((0, 0, 0)) # Bersihkan layar
            
            # Dapatkan status game terbaru dari logika catur
            game_status = self.chess_game.get_game_status()

            # Gambar papan catur, bidak, highlight, dan status game
            self.gui.draw_board(self.chess_game.get_board_state(), 
                                 self.selected_square_gui, 
                                 self.possible_moves_gui,
                                 game_status)
            
            # Gambar kursor gestur, hanya jika posisinya valid (bukan None)
            if self.current_cursor_x is not None and self.current_cursor_y is not None:
                self.gui.draw_cursor(self.current_cursor_x, self.current_cursor_y, self.is_hand_closed)

            # Perbarui tampilan Pygame
            self.gui.update_display()

           # --- Tampilkan frame kamera di jendela terpisah (untuk debugging) ---
            # 'display_frame' sudah digambar dengan landmark tangan di gesture_control.py
            cv2.imshow('Camera Feed (Debug)', display_frame) 

            # Tambahkan handler untuk menutup jendela kamera dengan 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False


        # --- 5. Bersih-bersih setelah game loop selesai ---
        self.gesture_controller.stop_camera()
        cv2.destroyAllWindows()
        self.gui.quit()
        print("Game closed.")

if __name__ == "__main__":
    game = MainGame()
    game.start_game()