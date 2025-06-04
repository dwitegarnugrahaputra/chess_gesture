import chess

class ChessGame:
    def __init__(self):
        """
        Menginisialisasi papan catur baru.
        'chess.Board()' akan membuat papan dalam posisi awal permainan.
        """
        self.board = chess.Board()
        self.selected_square = None  # Untuk melacak kotak yang sedang dipilih oleh pemain

    def get_board_state(self):
        """
        Mengembalikan objek board dari python-chess.
        """
        return self.board

    def get_turn(self):
        """
        Mengembalikan giliran pemain saat ini.
        True untuk Putih, False untuk Hitam.
        """
        return self.board.turn == chess.WHITE

    def select_square(self, square_coords):
        """
        Memilih atau membatalkan pilihan sebuah kotak di papan.
        square_coords: String notasi catur (e.g., 'e2').
        """
        try:
            # Mengonversi string notasi catur ke objek square (integer)
            square = chess.Square(chess.parse_square(square_coords)) 
        except ValueError:
            print(f"Invalid square coordinate: {square_coords}")
            return False # Indikasi bahwa pemilihan gagal

        # Jika belum ada bidak yang dipilih, dan ada bidak di kotak yang dipilih
        if self.selected_square is None:
            if self.board.piece_at(square):
                # Pastikan bidak yang dipilih adalah milik pemain yang sedang giliran
                if (self.board.piece_at(square).color == chess.WHITE and self.board.turn == chess.WHITE) or \
                   (self.board.piece_at(square).color == chess.BLACK and self.board.turn == chess.BLACK):
                    self.selected_square = square
                    print(f"Selected: {chess.square_name(square)}")
                    return True # Indikasi pemilihan berhasil
            return False # Tidak ada bidak milik pemain yang bisa dipilih

        # Jika sudah ada bidak yang dipilih, ini berarti pemain mencoba melakukan langkah
        else:
            from_square = self.selected_square
            to_square = square

            move = chess.Move(from_square, to_square)

            if move in self.board.legal_moves:
                self.board.push(move) # Lakukan langkah
                self.selected_square = None # Reset pilihan
                print(f"Moved {chess.square_name(from_square)} to {chess.square_name(to_square)}")
                return True # Indikasi langkah berhasil
            else:
                # Jika langkah tidak sah, batalkan pilihan saat ini
                print(f"Illegal move: {chess.square_name(from_square)} to {chess.square_name(to_square)}")
                self.selected_square = None # Batalkan pilihan
                return False # Indikasi langkah gagal

    def get_legal_moves(self, square_name=None):
        """
        Mengembalikan langkah-langkah yang sah untuk bidak di kotak tertentu,
        atau semua langkah sah jika tidak ada square_name.
        """
        legal_moves_for_piece = []
        
        # Jika tidak ada square_name spesifik, dan ada bidak yang sedang dipilih
        if square_name is None and self.selected_square:
            square = self.selected_square # Gunakan square yang sudah dipilih (dalam bentuk integer)
        elif square_name:
            # Mengonversi string notasi catur (e.g., 'e2') ke objek square (integer)
            try:
                square = chess.parse_square(square_name)
            except ValueError:
                return [] # Return empty list jika square_name tidak valid
        else:
            return [] # Jika tidak ada square_name dan tidak ada yang dipilih

        for move in self.board.legal_moves:
            if move.from_square == square:
                legal_moves_for_piece.append(move.to_square)
        return legal_moves_for_piece
    
    def reset_game(self):
        """
        Mengatur ulang papan catur ke posisi awal.
        """
        self.board.reset()
        self.selected_square = None
        print("Game reset.")

    def get_game_status(self):
        """
        Mengecek status permainan (check, checkmate, stalemate, game over).
        """
        status = {"game_over": self.board.is_game_over(),
                  "checkmate": self.board.is_checkmate(),
                  "stalemate": self.board.is_stalemate(),
                  "check": self.board.is_check(),
                  "turn": "White" if self.board.turn == chess.WHITE else "Black"}
        
        if status["game_over"]:
            if status["checkmate"]:
                status["message"] = f"Checkmate! {'Black' if self.board.turn == chess.WHITE else 'White'} wins!"
            elif status["stalemate"]:
                status["message"] = "Stalemate! It's a draw."
            else:
                status["message"] = "Game over (Draw by other means)."
        elif status["check"]:
            status["message"] = f"{status['turn']} is in check!"
        else:
            status["message"] = f"{status['turn']}'s turn."
        
        return status