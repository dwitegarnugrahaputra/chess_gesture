import chess

class ChessGame:
    def __init__(self):
        """
        Menginisialisasi papan catur baru.
        'chess.Board()' akan membuat papan dalam posisi awal permainan.
        """
        self.board = chess.Board()
        self.selected_square = None  # Untuk melacak kotak yang sedang dipilih oleh pemain
        self.move_history_redo = [] # Menyimpan langkah yang di-undo untuk keperluan redo

    def get_board_state(self):
        """
        Mengembalikan objek board dari python-chess.
        """
        return self.board

    def get_turn(self):
        """
        Mengembalikan giliran pemain saat ini.
        True untuk Putih (chess.WHITE), False untuk Hitam (chess.BLACK).
        """
        return self.board.turn == chess.WHITE

    def select_square(self, square_coords):
        """
        Memilih atau membatalkan pilihan sebuah kotak di papan, atau melakukan langkah.
        square_coords: String notasi catur (e.g., 'e2').
        Mengembalikan True jika pemilihan/langkah berhasil, False jika tidak.
        """
        try:
            # Mengonversi string notasi catur ke objek square (integer)
            square = chess.Square(chess.parse_square(square_coords)) 
        except ValueError:
            print(f"Invalid square coordinate: {square_coords}")
            return False 

        # Jika belum ada bidak yang dipilih (ini adalah pemilihan pertama)
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece:
                # Pastikan bidak yang dipilih adalah milik pemain yang sedang giliran
                # chess.WHITE adalah True, chess.BLACK adalah False. self.board.turn adalah boolean
                if (piece.color == self.board.turn): 
                    self.selected_square = square
                    print(f"Selected: {chess.square_name(square)}")
                    return True 
            return False # Tidak ada bidak milik pemain yang bisa dipilih, atau kotak kosong

        # Jika sudah ada bidak yang dipilih (pemain mencoba melakukan langkah)
        else:
            from_square = self.selected_square
            to_square = square

            # Cek promosi pion (jika pion mencapai baris terakhir)
            # Asumsi promosi ke Ratu (Queen) untuk penyederhanaan
            move = None
            if self.board.piece_at(from_square) and self.board.piece_at(from_square).piece_type == chess.PAWN and \
               (chess.square_rank(to_square) == 7 or chess.square_rank(to_square) == 0): # Cek baris terakhir untuk promosi
                move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
            else:
                move = chess.Move(from_square, to_square)

            if move in self.board.legal_moves:
                self.board.push(move) # Lakukan langkah
                self.selected_square = None # Reset pilihan
                self.move_history_redo = [] # Kosongkan history redo saat langkah baru dilakukan
                print(f"Moved {chess.square_name(from_square)} to {chess.square_name(to_square)}")
                return True 
            else:
                # Jika langkah tidak sah, atau mencoba klik kotak yang sama lagi
                print(f"Illegal move: {chess.square_name(from_square)} to {chess.square_name(to_square)}")
                self.selected_square = None # Batalkan pilihan
                return False 

    def undo_move(self):
        """
        Membatalkan langkah terakhir di papan.
        Mengembalikan True jika berhasil, False jika tidak ada langkah untuk di-undo.
        """
        if self.board.move_stack: # Cek apakah ada langkah yang bisa di-undo
            last_move = self.board.pop() # Batalkan langkah terakhir
            self.move_history_redo.append(last_move) # Tambahkan ke history redo
            print(f"Undone move: {last_move.uci()}")
            self.selected_square = None # Pastikan tidak ada bidak yang dipilih setelah undo
            return True
        print("No moves to undo.")
        return False

    def redo_move(self):
        """
        Mengulang langkah yang baru saja di-undo.
        Mengembalikan True jika berhasil, False jika tidak ada langkah untuk di-redo.
        """
        if self.move_history_redo: # Cek apakah ada langkah yang bisa di-redo
            next_move = self.move_history_redo.pop() # Ambil langkah terakhir dari history redo
            # Penting: Pastikan langkah yang di-redo valid di posisi papan saat ini.
            if next_move in self.board.legal_moves: # Pastikan legal di posisi saat ini
                self.board.push(next_move) # Lakukan langkah
                print(f"Redone move: {next_move.uci()}")
                self.selected_square = None
                return True
            else:
                # Jika langkah tidak lagi valid (misal karena state board berubah),
                # kembalikan move ke history_redo dan cetak pesan
                self.move_history_redo.append(next_move) # Kembalikan ke history redo
                print(f"Cannot redo move {next_move.uci()} - not a legal move in current position.")
                return False
        print("No moves to redo.")
        return False

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
        Juga membersihkan history redo.
        """
        self.board.reset()
        self.selected_square = None
        self.move_history_redo = [] # Kosongkan history redo saat reset
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
