import pygame
import os
import chess # Untuk menggunakan konstanta bidak seperti chess.PAWN, chess.WHITE, dll.

# --- KONSTANTA PYGAME ---
WIDTH, HEIGHT = 800, 800 # Ukuran jendela game
BOARD_SIZE = 8 # Papan catur 8x8
SQUARE_SIZE = WIDTH // BOARD_SIZE # Ukuran setiap kotak di papan
FPS = 60 # Frames per second

# Warna
LIGHT_SQUARE_COLOR = (235, 235, 205) # Krem
DARK_SQUARE_COLOR = (110, 140, 100) # Hijau gelap
HIGHLIGHT_COLOR_SELECTED = (0, 255, 0, 100) # Hijau transparan untuk kotak terpilih
HIGHLIGHT_COLOR_POSSIBLE = (255, 255, 0, 100) # Kuning transparan untuk langkah valid
CHECK_COLOR = (255, 0, 0, 100) # Merah transparan untuk Raja yang di-check

# --- MAPPING BIDAK KE FILE GAMBAR ---
# Mapping bidak python-chess ke nama file gambar
# Sesuaikan nama file gambar sesuai dengan yang kamu simpan di folder assets/
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

        self.images = {} # Dictionary untuk menyimpan gambar bidak yang sudah dimuat
        self.load_images()
        
        self.font = pygame.font.Font(None, 36) # Font untuk teks status

    def load_images(self):
        """Memuat semua gambar bidak catur."""
        for piece_char, filename in PIECE_IMAGES.items():
            path = os.path.join("assets", filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                # Sesuaikan ukuran gambar bidak agar pas dengan SQUARE_SIZE
                self.images[piece_char] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
            except pygame.error as e:
                print(f"Error loading image {path}: {e}")
                # Jika gambar tidak bisa dimuat, buat placeholder atau keluar
                # Untuk pengembangan, bisa jadi kotak kosong atau teks
                self.images[piece_char] = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                self.images[piece_char].fill((255, 0, 0, 128)) # Merah transparan sebagai placeholder
                pygame.draw.circle(self.images[piece_char], (255, 255, 255), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 20)
                pygame.font.init()
                font = pygame.font.Font(None, 24)
                text_surface = font.render(piece_char, True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=(SQUARE_SIZE // 2, SQUARE_SIZE // 2))
                self.images[piece_char].blit(text_surface, text_rect)


    def draw_board(self, board, selected_square=None, legal_moves=None, game_status=None):
        """
        Menggambar papan catur dan bidak-bidaknya.
        board: Objek chess.Board dari ChessGame.
        selected_square: Kotak yang sedang dipilih (integer).
        legal_moves: Daftar langkah sah untuk bidak yang dipilih (daftar integer).
        game_status: Dictionary status game dari ChessGame.
        """
        # Gambar kotak papan
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Gambar highlight untuk kotak yang dipilih
        if selected_square is not None:
            # Konversi dari objek square (integer) ke koordinat piksel
            selected_col = chess.square_file(selected_square)
            selected_row = 7 - chess.square_rank(selected_square) # Pygame y-axis terbalik
            
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA) # Surface transparan
            s.fill(HIGHLIGHT_COLOR_SELECTED)
            self.screen.blit(s, (selected_col * SQUARE_SIZE, selected_row * SQUARE_SIZE))

        # Gambar highlight untuk langkah yang sah
        if legal_moves:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT_COLOR_POSSIBLE)
            for move_to_square in legal_moves:
                move_col = chess.square_file(move_to_square)
                move_row = 7 - chess.square_rank(move_to_square)
                self.screen.blit(s, (move_col * SQUARE_SIZE, move_row * SQUARE_SIZE))
        
        # Gambar bidak
        for square in chess.SQUARES: # Iterasi melalui semua 64 kotak catur
            piece = board.piece_at(square)
            if piece:
                # Konversi dari objek square (integer) ke koordinat piksel
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square) # Pygame y-axis terbalik

                piece_char = piece.symbol() # 'P', 'r', 'K', dll.
                if piece_char in self.images:
                    self.screen.blit(self.images[piece_char], (col * SQUARE_SIZE, row * SQUARE_SIZE))
                else:
                    # Fallback jika gambar tidak ditemukan
                    print(f"Warning: Image for piece '{piece_char}' not found.")


        # Gambar highlight untuk Raja yang di-check
        if game_status and game_status["check"]:
            king_square = board.king(board.turn)
            if king_square:
                king_col = chess.square_file(king_square)
                king_row = 7 - chess.square_rank(king_square)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(CHECK_COLOR)
                self.screen.blit(s, (king_col * SQUARE_SIZE, king_row * SQUARE_SIZE))

        # Tampilkan status game (misalnya, giliran siapa, checkmate, dll.)
        if game_status and "message" in game_status:
            text_surface = self.font.render(game_status["message"], True, (255, 255, 255)) # Putih
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 30)) # Posisikan di bawah
            self.screen.blit(text_surface, text_rect)


    def draw_cursor(self, cursor_x, cursor_y, is_closed=False):
        """
        Menggambar kursor gestur di layar.
        """
        cursor_color = (0, 255, 0) if not is_closed else (255, 0, 0) # Hijau saat hover, Merah saat klik
        pygame.draw.circle(self.screen, cursor_color, (cursor_x, cursor_y), 15)


    def update_display(self):
        """Memperbarui tampilan layar Pygame."""
        pygame.display.flip()
        self.clock.tick(FPS)

    def quit(self):
        """Keluar dari Pygame."""
        pygame.quit()

    def get_square_from_pixels(self, px, py):
        """
        Mengonversi koordinat piksel ke koordinat kotak catur (integer).
        Mengembalikan None jika di luar papan.
        """
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            col = px // SQUARE_SIZE
            row = py // SQUARE_SIZE
            # Konversi dari koordinat Pygame (0,0 di kiri atas) ke koordinat catur (A1 di kiri bawah)
            # Rank 0-7 (bottom to top), File 0-7 (left to right)
            square = chess.square(col, 7 - row)
            return square
        return None

    def get_square_name_from_pixels(self, px, py):
        """
        Mengonversi koordinat piksel ke nama kotak catur (e.g., 'e2').
        """
        square_int = self.get_square_from_pixels(px, py)
        if square_int is not None:
            return chess.square_name(square_int)
        return None