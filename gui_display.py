import pygame
import os
import chess

# --- KONSTANTA PYGAME ---
BOARD_RENDER_SIZE = 800 # Ukuran sisi papan catur yang akan dirender (persegi)
SIDEBAR_WIDTH = 300 # Lebar sidebar untuk tombol dan info
WIDTH = BOARD_RENDER_SIZE + SIDEBAR_WIDTH # Total lebar jendela (800 + 300 = 1100)
HEIGHT = BOARD_RENDER_SIZE # Total tinggi jendela (sama dengan tinggi papan, 800)

BOARD_SIZE = 8 # Papan catur 8x8
SQUARE_SIZE = BOARD_RENDER_SIZE // BOARD_SIZE # Ukuran setiap kotak di papan (800 / 8 = 100)
FPS = 60 # Frames per second

# Warna UI
UI_BACKGROUND_COLOR = (100, 100, 100) # Abu-abu medium-dark
TEXT_COLOR = (255, 255, 255) # Putih
SIDEBAR_COLOR = (50, 50, 50) # Warna sidebar yang lebih gelap

# Warna Papan Catur
LIGHT_SQUARE_COLOR = (235, 235, 205) # Krem
DARK_SQUARE_COLOR = (110, 140, 100) # Hijau gelap
HIGHLIGHT_COLOR_SELECTED = (0, 255, 0, 100) # Hijau transparan untuk kotak terpilih
HIGHLIGHT_COLOR_POSSIBLE = (255, 255, 0, 100) # Kuning transparan untuk langkah valid
CHECK_COLOR = (255, 0, 0, 100) # Merah transparan untuk Raja yang di-check

# --- KONSTANTA TOMBOL ---
BUTTON_MARGIN = 25 # Margin antar tombol dan dari sisi sidebar
BUTTON_WIDTH = SIDEBAR_WIDTH - (2 * BUTTON_MARGIN) # Lebar tombol disesuaikan dengan sidebar_width (300 - 50 = 250)
BUTTON_HEIGHT = 70

BUTTON_COLOR = (70, 70, 70) # Warna dasar tombol (abu-abu gelap)
BUTTON_HOVER_COLOR = (100, 100, 100) # Warna tombol saat di-hover
BUTTON_TEXT_COLOR = (255, 255, 255) # Warna teks tombol

PIECE_IMAGES = {
    'P': 'wp.png', 'R': 'wr.png', 'N': 'wn.png', 'B': 'wb.png', 'Q': 'wq.png', 'K': 'wk.png',
    'p': 'bp.png', 'r': 'br.png', 'n': 'bn.png', 'b': 'bb.png', 'q': 'bq.png', 'k': 'bk.png'
}

class ChessGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Gesture Game")
        self.clock = pygame.time.Clock()

        self.images = {} # Untuk bidak catur
        self.ui_graphics = {} # Untuk gambar UI seperti tangan dan bidak di homepage/color selection
        self.load_images()
        self.load_ui_graphics() 
        
        # Inisialisasi Font
        self.font = pygame.font.Font(None, 36) # Font default untuk status game
        self.button_font = pygame.font.Font(None, 30) # Font untuk teks tombol
        self.homepage_font_title = pygame.font.Font(None, 80) # Font besar untuk judul homepage
        self.mode_selection_font_title = pygame.font.Font(None, 60) # Font untuk judul layar pemilihan mode/warna

        # Definisi tombol homepage (di tengah seluruh jendela)
        self.homepage_buttons = {
            "VS COMPUTER": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT * 0.65, BUTTON_WIDTH, BUTTON_HEIGHT),
            "MULTIPLAYER": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT * 0.65 + BUTTON_HEIGHT + BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT),
        }

        # Tombol pemilihan warna (posisi di tengah seluruh jendela)
        self.player_color_buttons = {
            "PLAY AS A WHITE": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT * 0.65, BUTTON_WIDTH, BUTTON_HEIGHT),
            "PLAY AS A BLACK": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT * 0.65 + BUTTON_HEIGHT + BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT),
        }

        # Definisi tombol in-game (di dalam sidebar), tanpa Pause/Resume
        self.in_game_buttons = {
            "Restart": pygame.Rect(BOARD_RENDER_SIZE + BUTTON_MARGIN, BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT),
            "Undo": pygame.Rect(BOARD_RENDER_SIZE + BUTTON_MARGIN, BUTTON_MARGIN * 2 + BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT),
            "Redo": pygame.Rect(BOARD_RENDER_SIZE + BUTTON_MARGIN, BUTTON_MARGIN * 3 + BUTTON_HEIGHT * 2, BUTTON_WIDTH, BUTTON_HEIGHT),
            "Quit": pygame.Rect(BOARD_RENDER_SIZE + BUTTON_MARGIN, BUTTON_MARGIN * 4 + BUTTON_HEIGHT * 3, BUTTON_WIDTH, BUTTON_HEIGHT), # Quit dipindahkan ke sini
        }
        # Definisi tombol di menu overlay, tanpa Pause/Resume
        self.menu_buttons = {
            "Restart": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 - BUTTON_HEIGHT * 1.5 - BUTTON_MARGIN * 1.5, BUTTON_WIDTH, BUTTON_HEIGHT), # Posisi disesuaikan
            "Undo": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 - BUTTON_HEIGHT * 0.5 - BUTTON_MARGIN * 0.5, BUTTON_WIDTH, BUTTON_HEIGHT), # Posisi disesuaikan
            "Redo": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 + BUTTON_HEIGHT * 0.5 + BUTTON_MARGIN * 0.5, BUTTON_WIDTH, BUTTON_HEIGHT), # Posisi disesuaikan
            "Quit": pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 + BUTTON_HEIGHT * 1.5 + BUTTON_MARGIN * 1.5, BUTTON_WIDTH, BUTTON_HEIGHT), # Posisi disesuaikan
        }


    def load_images(self):
        """Memuat semua gambar bidak catur."""
        for piece_char, filename in PIECE_IMAGES.items():
            path = os.path.join("assets", filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                self.images[piece_char] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE)) 
            except pygame.error as e:
                print(f"Error loading piece image {path}: {e}")
                self.images[piece_char] = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                self.images[piece_char].fill((255, 0, 0, 128))
                pygame.font.init()
                font = pygame.font.Font(None, 24)
                text_surface = font.render(piece_char, True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=(SQUARE_SIZE // 2, SQUARE_SIZE // 2))
                self.images[piece_char].blit(text_surface, text_rect)

    def load_ui_graphics(self):
        """Memuat gambar grafis UI seperti tangan dan bidak untuk halaman menu."""
        ui_graphic_files = {
            "homepage_graphic": "1.png",      
            "color_select_graphic": "2.png"   
        }
        for name, filename in ui_graphic_files.items():
            path = os.path.join("assets", filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                if name == "homepage_graphic":
                    self.ui_graphics[name] = pygame.transform.scale(image, (int(WIDTH * 0.4), int(HEIGHT * 0.4)))
                elif name == "color_select_graphic":
                    self.ui_graphics[name] = pygame.transform.scale(image, (int(WIDTH * 0.35), int(HEIGHT * 0.35))) 
            except pygame.error as e:
                print(f"Error loading UI graphic {path}: {e}")
                self.ui_graphics[name] = None 


    def draw_board(self, board, selected_square=None, legal_moves=None, game_status=None, player_is_black_view=False):
        """
        Menggambar papan catur dan bidak-bidaknya.
        player_is_black_view: Jika True, papan dibalik untuk tampilan pemain Hitam.
        """
        # Gambar background untuk area papan catur
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, BOARD_RENDER_SIZE, HEIGHT)) # Clear board area with black
        
        # Gambar kotak papan
        for r_idx in range(BOARD_SIZE):
            for c_idx in range(BOARD_SIZE):
                color = LIGHT_SQUARE_COLOR if (r_idx + c_idx) % 2 == 0 else DARK_SQUARE_COLOR
                
                # Tentukan posisi tampilan baris/kolom berdasarkan orientasi
                display_col = c_idx
                display_row = r_idx if not player_is_black_view else (7 - r_idx)
                
                pygame.draw.rect(self.screen, color, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Gambar highlight untuk kotak yang dipilih
        if selected_square is not None:
            actual_col = chess.square_file(selected_square)
            actual_row = chess.square_rank(selected_square)
            
            display_col = actual_col
            display_row = (7 - actual_row) if not player_is_black_view else actual_row
            
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT_COLOR_SELECTED)
            self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

        # Gambar highlight untuk langkah yang sah
        if legal_moves:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT_COLOR_POSSIBLE)
            for move_to_square in legal_moves:
                actual_col = chess.square_file(move_to_square)
                actual_row = chess.square_rank(move_to_square)
                
                display_col = actual_col
                display_row = (7 - actual_row) if not player_is_black_view else actual_row
                
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))
        
        # Gambar bidak
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                actual_col = chess.square_file(square)
                actual_row = chess.square_rank(square) 

                display_col = actual_col 
                display_row = (7 - actual_row) if not player_is_black_view else actual_row 

                piece_char = piece.symbol()
                if piece_char in self.images:
                    self.screen.blit(self.images[piece_char], (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE)) 
                else:
                    print(f"Warning: Image for piece '{piece_char}' not found.")

        # Gambar highlight untuk Raja yang di-check
        if game_status and game_status["check"]:
            king_square = board.king(board.turn)
            if king_square:
                actual_col = chess.square_file(king_square)
                actual_row = chess.square_rank(king_square)

                display_col = actual_col
                display_row = (7 - actual_row) if not player_is_black_view else actual_row

                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(CHECK_COLOR)
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

        # --- Gambar Sidebar ---
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (BOARD_RENDER_SIZE, 0, SIDEBAR_WIDTH, HEIGHT))

        # Tampilkan status game (misalnya, giliran siapa, checkmate, dll.) di sidebar
        if game_status and "message" in game_status:
            status_text_surface = self.font.render(game_status["message"], True, TEXT_COLOR) 
            status_text_rect = status_text_surface.get_rect(center=(BOARD_RENDER_SIZE + SIDEBAR_WIDTH // 2, HEIGHT - 50))
            self.screen.blit(status_text_surface, status_text_rect)
            
    def draw_buttons(self, cursor_pos=None, game_state="playing"):
        """
        Menggambar tombol-tombol kontrol (Restart, Undo, Redo, Quit).
        cursor_pos: Posisi kursor untuk highlight hover.
        game_state: Digunakan untuk menentukan set tombol.
        """
        buttons_to_draw = {}
        if game_state in ["PLAYING_VS_COMPUTER", "PLAYING_MULTIPLAYER"]: 
            buttons_to_draw = self.in_game_buttons
        elif game_state == "IN_GAME_MENU": # Ini adalah menu overlay saat game "di-pause"
            buttons_to_draw = self.menu_buttons

        for button_name, button_rect in buttons_to_draw.items():
            current_button_color = BUTTON_COLOR
            if cursor_pos is not None and button_rect.collidepoint(cursor_pos): 
                current_button_color = BUTTON_HOVER_COLOR
            
            pygame.draw.rect(self.screen, current_button_color, button_rect, border_radius=5)

            # Teks tombol sama dengan namanya
            text_surface = self.button_font.render(button_name, True, BUTTON_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)

    def draw_homepage(self, cursor_pos=None):
        """
        Menggambar halaman utama game dengan grafis UI, background solid, dan tombol.
        """
        self.screen.fill(UI_BACKGROUND_COLOR) 
        
        if self.ui_graphics.get("homepage_graphic"):
            graphic = self.ui_graphics["homepage_graphic"]
            graphic_rect = graphic.get_rect(center=(WIDTH // 2, HEIGHT * 0.45)) 
            self.screen.blit(graphic, graphic_rect)
        
        title_part1 = self.homepage_font_title.render("CHESS HAND", True, TEXT_COLOR)
        title_part2 = self.homepage_font_title.render("GESTURE", True, TEXT_COLOR)

        title1_rect = title_part1.get_rect(center=(WIDTH // 2, HEIGHT * 0.15)) 
        title2_rect = title_part2.get_rect(center=(WIDTH // 2, HEIGHT * 0.25)) 
        self.screen.blit(title_part1, title1_rect)
        self.screen.blit(title_part2, title2_rect)

        for button_name, button_rect in self.homepage_buttons.items():
            current_button_color = BUTTON_COLOR
            if cursor_pos is not None and button_rect.collidepoint(cursor_pos): 
                current_button_color = BUTTON_HOVER_COLOR
            
            pygame.draw.rect(self.screen, current_button_color, button_rect, border_radius=5)
            
            text_surface = self.button_font.render(button_name, True, BUTTON_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)


    def draw_color_selection(self, cursor_pos=None, selected_mode=None, selected_player_color_name=None):
        """
        Menggambar layar pemilihan warna pemain.
        selected_mode: 'VS COMPUTER' atau 'MULTIPLAYER'
        """
        self.screen.fill(UI_BACKGROUND_COLOR) 

        if self.ui_graphics.get("color_select_graphic"):
            graphic = self.ui_graphics["color_select_graphic"]
            graphic_rect = graphic.get_rect(center=(WIDTH // 2, HEIGHT * 0.45)) 
            self.screen.blit(graphic, graphic_rect)

        title_text = self.mode_selection_font_title.render(selected_mode, True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT * 0.15)) 
        self.screen.blit(title_text, title_rect)

        for button_name, button_rect in self.player_color_buttons.items():
            current_button_color = BUTTON_COLOR
            if cursor_pos is not None and button_rect.collidepoint(cursor_pos):
                current_button_color = BUTTON_HOVER_COLOR
            if selected_player_color_name == button_name: 
                current_button_color = (0, 150, 150) 

            pygame.draw.rect(self.screen, current_button_color, button_rect, border_radius=5)
            text_surface = self.button_font.render(button_name, True, BUTTON_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)
        
    def draw_pause_overlay(self):
        """Menggambar overlay saat game di-pause (untuk menu in-game)."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA) 
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        menu_text = self.font.render("MENU", True, TEXT_COLOR) # Ganti "PAUSE" menjadi "MENU"
        menu_text_rect = menu_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200)) 
        self.screen.blit(menu_text, menu_text_rect)

    def get_button_clicked(self, click_pos, current_game_state):
        """
        Mengecek tombol mana yang diklik berdasarkan posisi piksel dan state game.
        Mengembalikan nama tombol (string) atau None jika tidak ada tombol.
        """
        buttons_to_check = {}
        if current_game_state == "HOMEPAGE":
            buttons_to_check = self.homepage_buttons
        elif current_game_state == "PLAYER_COLOR_SELECTION": 
            buttons_to_check = self.player_color_buttons
        elif current_game_state in ["PLAYING_VS_COMPUTER", "PLAYING_MULTIPLAYER"]:
            buttons_to_check = self.in_game_buttons
        elif current_game_state == "IN_GAME_MENU":
            buttons_to_check = self.menu_buttons

        if click_pos is None: 
            return None

        for button_name, button_rect in buttons_to_check.items():
            if button_rect.collidepoint(click_pos):
                return button_name
        return None
    
    def draw_cursor(self, cursor_x, cursor_y, is_closed=False):
        """
        Menggambar kursor gestur di layar.
        """
        cursor_color = (0, 255, 0) if not is_closed else (255, 0, 0)
        pygame.draw.circle(self.screen, cursor_color, (cursor_x, cursor_y), 15)


    def update_display(self):
        """Memperbarui tampilan layar Pygame."""
        pygame.display.flip()
        self.clock.tick(FPS)

    def quit(self):
        """Keluar dari Pygame."""
        pygame.quit()

    def get_square_from_pixels(self, px, py, player_is_black_view=False):
        """
        Mengonversi koordinat piksel ke koordinat kotak catur (integer).
        Mengembalikan None jika di luar area papan catur atau di area sidebar.
        player_is_black_view: Jika True, konversi dibalik.
        """
        if px is None or py is None:
            return None

        # Hanya deteksi klik jika berada di area papan catur (0 hingga BOARD_RENDER_SIZE di sumbu X)
        if 0 <= px < BOARD_RENDER_SIZE and 0 <= py < HEIGHT:
            col = px // SQUARE_SIZE
            if not player_is_black_view: 
                row = 7 - (py // SQUARE_SIZE)
            else: 
                row = py // SQUARE_SIZE 
            
            square = chess.square(col, row)
            return square
        return None

    def get_square_name_from_pixels(self, px, py, player_is_black_view=False):
        """
        Mengonversi koordinat piksel ke nama kotak catur (e.g., 'e2').
        """
        square_int = self.get_square_from_pixels(px, py, player_is_black_view)
        if square_int is not None:
            return chess.square_name(square_int)
        return None
