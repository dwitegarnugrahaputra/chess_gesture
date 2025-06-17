import pygame
import cv2
import chess
import asyncio 
import sys 
import random 

# Import modul-modul lokal secara eksplisit
import gesture_control
import chess_game
import gui_display

# --- KONSTANTA ---
CURSOR_SMOOTHING_FACTOR = 0.6 

# Waktu "berpikir" AI yang tetap (default)
AI_FIXED_THINKING_TIME = 1.0 # Jeda 1.0 detik untuk AI sederhana

class MainGame:
    def __init__(self):
        self.gesture_controller = gesture_control.GestureController()
        self.chess_game = chess_game.ChessGame()
        self.gui = gui_display.ChessGUI() 

        self.running = False
        
        # State game utama: HOMEPAGE, PLAYER_COLOR_SELECTION, PLAYING_VS_COMPUTER, PLAYING_MULTIPLAYER
        # State IN_GAME_MENU tidak lagi ada sebagai state terpisah
        self.game_state = "HOMEPAGE" 
        
        self.current_cursor_x, self.current_cursor_y = None, None 
        self.is_hand_closed = False
        self.prev_is_hand_closed = False
        
        self.selected_square_gui = None 
        self.possible_moves_gui = [] 
        
        self.click_state = "IDLE" 
        self.smoothed_cursor_x = gui_display.WIDTH // 2 
        self.smoothed_cursor_y = gui_display.HEIGHT // 2 

        self.ai_task = None 
        
        self.player_color = chess.WHITE 
        self.ai_player_color = chess.BLACK 
        
        self.selected_game_mode = None 
        self.selected_player_color_name = None 
        self.player_is_black_view = False 

    def start_game(self):
        """Memulai semua subsistem (kamera, Pygame) dan game loop utama."""
        print(f"Python version: {sys.version}")
        print(f"python-chess version: {chess.__version__}")

        if not self.gesture_controller.start_camera():
            print("Failed to start camera. Exiting.")
            return

        print("Camera started. Game is running.")
        self.running = True
        asyncio.run(self.game_loop_async()) 

    async def game_loop_async(self):
        """Loop utama permainan, dijalankan secara asynchronous."""
        while self.running:
            # --- 1. Event Handling Pygame (misal: tombol tutup jendela) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # --- 2. Pemrosesan Kamera & Deteksi Gestur (Selalu Aktif) ---
            ret, frame = self.gesture_controller.cap.read()
            if not ret:
                print("Failed to grab frame from camera.")
                self.running = False
                break
            
            frame = cv2.flip(frame, 1) 
            display_frame, hand_landmarks = self.gesture_controller.process_frame(frame)
            
            img_h, img_w, _ = display_frame.shape
            cursor_x_raw, cursor_y_raw = self.gesture_controller.get_hand_position(hand_landmarks, img_w, img_h)
            
            # --- Terapkan Smoothing Kursor & Penanganan None untuk koordinat mentah ---
            if cursor_x_raw is not None and cursor_y_raw is not None:
                roi_x_start_perc = 0.05 
                roi_x_end_perc = 0.95   
                roi_y_start_perc = 0.05 
                roi_y_end_perc = 0.95   

                roi_x_start = int(img_w * roi_x_start_perc)
                roi_x_end = int(img_w * roi_x_end_perc)
                roi_y_start = int(img_h * roi_y_start_perc)
                roi_y_end = int(img_h * roi_y_end_perc)

                if roi_x_start <= cursor_x_raw <= roi_x_end and \
                   roi_y_start <= cursor_y_raw <= roi_y_end:
                    normalized_x_roi = (cursor_x_raw - roi_x_start) / (roi_x_end - roi_x_start)
                    normalized_y_roi = (cursor_y_raw - roi_y_start) / (roi_y_end - roi_y_start)

                    target_x = int(normalized_x_roi * gui_display.WIDTH) 
                    target_y = int(normalized_y_roi * gui_display.HEIGHT)
                else:
                    target_x, target_y = self.smoothed_cursor_x, self.smoothed_cursor_y 

                self.smoothed_cursor_x = int(self.smoothed_cursor_x * CURSOR_SMOOTHING_FACTOR + target_x * (1 - CURSOR_SMOOTHING_FACTOR))
                self.smoothed_cursor_y = int(self.smoothed_cursor_y * CURSOR_SMOOTHING_FACTOR + target_y * (1 - CURSOR_SMOOTHING_FACTOR))
                
                self.current_cursor_x = self.smoothed_cursor_x
                self.current_cursor_y = self.smoothed_cursor_y
            else:
                self.current_cursor_x, self.current_cursor_y = None, None 

            if hand_landmarks:
                self.is_hand_closed = self.gesture_controller.is_hand_closed(hand_landmarks)
            else:
                self.is_hand_closed = False

            # Siapkan posisi kursor dalam format tuple (x, y) untuk fungsi GUI, atau None
            cursor_pos_for_gui = None
            if self.current_cursor_x is not None and self.current_cursor_y is not None:
                cursor_pos_for_gui = (self.current_cursor_x, self.current_cursor_y)

            # --- Logika Game Berdasarkan State ---
            if self.game_state == "HOMEPAGE":
                self._handle_homepage_logic(cursor_pos_for_gui, self.is_hand_closed, self.prev_is_hand_closed)
            elif self.game_state == "PLAYER_COLOR_SELECTION": 
                await self._handle_player_color_selection_logic(cursor_pos_for_gui, self.is_hand_closed, self.prev_is_hand_closed)
            elif self.game_state in ["PLAYING_VS_COMPUTER", "PLAYING_MULTIPLAYER"]: 
                await self._handle_playing_logic(cursor_pos_for_gui, self.is_hand_closed, self.prev_is_hand_closed) 
            # Dihapus: elif self.game_state == "IN_GAME_MENU":
            #    self._handle_in_game_menu_logic(cursor_pos_for_gui, self.is_hand_closed, self.prev_is_hand_closed)

            self.prev_is_hand_closed = self.is_hand_closed 

            # --- Pembaharuan GUI Berdasarkan State ---
            self.gui.screen.fill((0, 0, 0)) # Selalu bersihkan layar sebelum menggambar (untuk fallback)

            # Gambar elemen GUI sesuai game_state
            if self.game_state == "HOMEPAGE":
                self.gui.draw_homepage(cursor_pos_for_gui) 
            elif self.game_state == "PLAYER_COLOR_SELECTION": 
                self.gui.draw_color_selection(cursor_pos_for_gui, self.selected_game_mode, self.selected_player_color_name)
            elif self.game_state in ["PLAYING_VS_COMPUTER", "PLAYING_MULTIPLAYER"]:
                game_status = self.chess_game.get_game_status()
                self.gui.draw_board(self.chess_game.get_board_state(), 
                                     self.selected_square_gui, 
                                     self.possible_moves_gui,
                                     game_status,
                                     player_is_black_view=self.player_is_black_view) 
                self.gui.draw_buttons(cursor_pos_for_gui, self.game_state) 
            # Jika tombol Quit diklik, tampilkan menu overlay, bukan state game yang terpisah
            # Maka, tidak perlu ada "elif self.game_state == 'IN_GAME_MENU'" lagi di sini.
            
            # Gambar kursor gestur di atas semua elemen GUI lainnya
            if self.current_cursor_x is not None and self.current_cursor_y is not None:
                self.gui.draw_cursor(self.current_cursor_x, self.current_cursor_y, self.is_hand_closed)

            self.gui.update_display() 

            # Tampilkan feed kamera untuk debugging
            cv2.imshow('Camera Feed (Debug)', display_frame) 
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                self.running = False
            
            await asyncio.sleep(0.01) 

        # --- 5. Bersih-bersih setelah game loop selesai ---
        self.gesture_controller.stop_camera() 
        cv2.destroyAllWindows() 
        self.gui.quit() 
        print("Game closed.")
    
    def _handle_homepage_logic(self, cursor_pos, is_closed, prev_is_hand_closed):
        """Logika untuk halaman utama (homepage)."""
        if is_closed and not prev_is_hand_closed: 
            if cursor_pos is not None: 
                clicked_button = self.gui.get_button_clicked(cursor_pos, self.game_state)
                if clicked_button in ["VS COMPUTER", "MULTIPLAYER"]:
                    print(f"Entering mode selection for: {clicked_button}")
                    self.selected_game_mode = clicked_button
                    self.game_state = "PLAYER_COLOR_SELECTION" 
                    self.selected_player_color_name = None 

    async def _handle_player_color_selection_logic(self, cursor_pos, is_closed, prev_is_hand_closed):
        """Logika untuk layar pemilihan warna pemain."""
        if is_closed and not prev_is_hand_closed:
            if cursor_pos is not None:
                clicked_button = self.gui.get_button_clicked(cursor_pos, self.game_state)

                if clicked_button == "PLAY AS A WHITE":
                    self.selected_player_color_name = "PLAY AS A WHITE"
                    self.player_color = chess.WHITE
                    self.ai_player_color = chess.BLACK
                    self.player_is_black_view = False 
                    print("Player selected White.")
                    self._start_game_after_color_selection()

                elif clicked_button == "PLAY AS A BLACK":
                    self.selected_player_color_name = "PLAY AS A BLACK"
                    self.player_color = chess.BLACK
                    self.ai_player_color = chess.WHITE
                    self.player_is_black_view = True 
                    print("Player selected Black, board will be inverted.")
                    self._start_game_after_color_selection()

    def _start_game_after_color_selection(self):
        """Helper function to transition based on selected game mode after color selection."""
        if self.selected_game_mode == "VS COMPUTER":
            self.game_state = "PLAYING_VS_COMPUTER" 
            self.chess_game.reset_game() 
            print("Starting VS COMPUTER game.")
            
            if self.chess_game.get_board_state().turn == self.ai_player_color:
                print("It's AI's turn initially. Attempting to start AI move task.")
                if self.ai_task is None or self.ai_task.done(): 
                    self.ai_task = asyncio.create_task(self._handle_ai_move())
                else:
                    print("AI task is already running from init, skipping new task creation.") 
            else:
                print("It's player's turn initially. AI will wait for player's move.")

        elif self.selected_game_mode == "MULTIPLAYER":
            self.game_state = "PLAYING_MULTIPLAYER" 
            self.chess_game.reset_game()
            print("Starting Multiplayer game (Placeholder for actual multiplayer logic).")

    async def _handle_playing_logic(self, cursor_pos, is_closed, prev_is_hand_closed):
        """Logika untuk mode bermain catur (Player vs Computer atau Multiplayer), termasuk menu in-game."""
        current_hover_square_name = None
        if cursor_pos is not None: 
            current_hover_square_name = self.gui.get_square_name_from_pixels(cursor_pos[0], cursor_pos[1], self.player_is_black_view)
            
            clicked_button_name = self.gui.get_button_clicked(cursor_pos, self.game_state) 
            if clicked_button_name and is_closed and not prev_is_hand_closed:
                if clicked_button_name == "Restart":
                    self.chess_game.reset_game()
                    self.selected_square_gui = None
                    self.possible_moves_gui = []
                    print("Game restarted.")
                    
                    if self.game_state == "PLAYING_VS_COMPUTER" and self.chess_game.get_board_state().turn == self.ai_player_color:
                        print("It's AI's turn after restart. Attempting to start AI move task.")
                        if self.ai_task is None or self.ai_task.done(): 
                            self.ai_task = asyncio.create_task(self._handle_ai_move())
                        else:
                            print("AI task is already running from restart, skipping new task creation.") 
                    else:
                        print("It's player's turn after restart. AI will wait.")

                elif clicked_button_name == "Undo":
                    self.chess_game.undo_move() 
                    self.selected_square_gui = None
                    self.possible_moves_gui = []
                    if self.ai_task and not self.ai_task.done(): 
                        self.ai_task.cancel()
                        print("AI thinking cancelled due to Undo.")
                elif clicked_button_name == "Redo":
                    self.chess_game.redo_move() 
                    self.selected_square_gui = None
                    self.possible_moves_gui = []
                elif clicked_button_name == "Quit": # Tombol Quit langsung berfungsi dari sidebar
                    self.running = False 
                    print("Quitting game from in-game sidebar.")
                return 

        # --- Logika Deteksi Gerakan Bidak (Klik-Lepas) ---
        if is_closed and not prev_is_hand_closed and cursor_pos is not None: 
            if self.click_state == "IDLE": 
                if current_hover_square_name:
                    piece_at_square = self.chess_game.get_board_state().piece_at(chess.parse_square(current_hover_square_name))
                    
                    can_select_piece = False
                    if self.game_state == "PLAYING_VS_COMPUTER":
                        if piece_at_square and piece_at_square.color == self.player_color:
                            can_select_piece = True
                    elif self.game_state == "PLAYING_MULTIPLAYER":
                        if piece_at_square and piece_at_square.color == self.chess_game.get_board_state().turn:
                            can_select_piece = True

                    if can_select_piece:
                        self.chess_game.select_square(current_hover_square_name)
                        self.selected_square_gui = self.chess_game.selected_square
                        if self.selected_square_gui:
                            self.possible_moves_gui = self.chess_game.get_legal_moves(chess.square_name(self.selected_square_gui))
                            self.click_state = "SELECTED_DRAG" 
                    else:
                        print(f"Cannot select piece at {current_hover_square_name}. It's not your piece or square is empty.")
                        self.click_state = "IDLE" 
                else:
                    self.click_state = "IDLE"

        elif not is_closed and prev_is_hand_closed and cursor_pos is not None: 
            if self.click_state == "SELECTED_DRAG": 
                if current_hover_square_name:
                    move_successful = self.chess_game.select_square(current_hover_square_name)
                    print(f"Player move successful: {move_successful}") 
                    self.selected_square_gui = None
                    self.possible_moves_gui = [] 
                    
                    print(f"After player move: Board turn: {'White' if self.chess_game.get_board_state().turn == chess.WHITE else 'Black'}, AI color: {'White' if self.ai_player_color == chess.WHITE else 'Black'}")
                    print(f"Is game over? {self.chess_game.get_board_state().is_game_over()}")

                    if self.game_state == "PLAYING_VS_COMPUTER" and \
                       move_successful and \
                       self.chess_game.get_board_state().turn == self.ai_player_color and \
                       not self.chess_game.get_board_state().is_game_over():
                        print("It is AI's turn and game is not over. Attempting to start AI move task.")
                        if self.ai_task is None or self.ai_task.done(): 
                            self.ai_task = asyncio.create_task(self._handle_ai_move()) 
                        else:
                            print("AI task is already running, skipping new task creation.")
                    elif move_successful:
                        print("Player moved successfully, but it's not AI's turn yet or game is over.")
                    else:
                        print("Player's move was not successful.")
                else:
                    self.selected_square_gui = None
                    self.possible_moves_gui = []
                self.click_state = "IDLE"
        
    # Dihapus: _handle_in_game_menu_logic
    # async def _handle_in_game_menu_logic(self, cursor_pos, is_closed, prev_is_hand_closed): 
    #    ...

    async def _handle_ai_move(self):
        """Meminta langkah dari AI sederhana dan melaksanakannya."""
        try:
            if self.chess_game.get_board_state().turn == self.ai_player_color and \
               not self.chess_game.get_board_state().is_game_over():
                
                print(f"AI ({'White' if self.ai_player_color == chess.WHITE else 'Black'}) is thinking for {AI_FIXED_THINKING_TIME} seconds (simple AI)...") 
                
                await asyncio.sleep(AI_FIXED_THINKING_TIME) 

                legal_moves = list(self.chess_game.get_board_state().legal_moves)
                if not legal_moves:
                    print("No legal moves for AI. Game might be over or stalled.")
                    return

                best_move = random.choice(legal_moves)
                
                if best_move in self.chess_game.get_board_state().legal_moves:
                    self.chess_game.select_square(chess.square_name(best_move.from_square))
                    self.chess_game.select_square(chess.square_name(best_move.to_square))
                    print(f"AI moved: {best_move.uci()} (random move)")
                else:
                    print(f"AI generated an illegal move: {best_move.uci()}. This shouldn't happen with random legal moves.")

                self.selected_square_gui = None 
                self.possible_moves_gui = [] 

            else:
                print("AI move not executed: Not AI's turn or game is over.") 
                print(f"Current turn: {'White' if self.chess_game.get_board_state().turn == chess.WHITE else 'Black'}, AI color: {'White' if self.ai_player_color == chess.WHITE else 'Black'}, Game Over: {self.chess_game.get_board_state().is_game_over()}")

        except asyncio.CancelledError: 
            print("AI thinking cancelled by user action (e.g., Undo or Pause).")
        except Exception as e:
            print(f"An unexpected error occurred during AI move: {e}")
        finally:
            self.ai_task = None 


if __name__ == "__main__":
    game = MainGame()
    game.start_game()
