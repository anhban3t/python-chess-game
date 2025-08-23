import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from PIL import Image, ImageTk
import chess
import pygame
import random
import time

pygame.mixer.init()


def play_sound(name):
    try:
        pygame.mixer.Sound(f"sounds/{name}.wav").play()
    except Exception as e:
        print(f"Sound error: {e}")


BOARD_SIZE = 8
SQUARE_SIZE = 80


LIGHT_COLOR = "#F0D9B5"
DARK_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#C86428"
HIGHLIGHT_LEGAL = "#8BB381"

PIECE_IMAGES = {}
PIECE_FILES = {
    "P": "images/wp.png", "R": "images/wr.png", "N": "images/wn.png",
    "B": "images/wb.png", "Q": "images/wq.png", "K": "images/wk.png",
    "p": "images/bp.png", "r": "images/br.png", "n": "images/bn.png",
    "b": "images/bb.png", "q": "images/bq.png", "k": "images/bk.png"
}

# time 10 minutes for each player
TIMER_SECONDS = 10 * 60


class ChessGame(tk.Frame):
    def __init__(self, master, start_window, ai_mode=False, player_color="white"):
        super().__init__(master)
        self.master = master
        self.start_window = start_window
        self.ai_mode = ai_mode
        self.player_color = player_color.lower()
        self.board = chess.Board()
        self.selected_piece = None
        self.selected_square = None
        self.flipped = False
        self.legal_moves = []
        self.promotion_pieces = None
        self.promotion_move = None
        self.game_over = False

        self.white_time = TIMER_SECONDS
        self.black_time = TIMER_SECONDS
        self.timer_running = False

        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.load_images()
        self.update_ui()

        if self.player_color == "black":
            self.flipped = True
            self.update_ui()
            if self.ai_mode and self.board.turn == chess.WHITE:
                self.after(500, self.play_ai_move)

        elif self.player_color == "random":
            self.player_color = random.choice(["white", "black"])
            self.flipped = (self.player_color == "black")
            self.update_ui()
            if self.ai_mode and self.board.turn != (self.player_color == "white"):
                self.after(500, self.play_ai_move)

        self.start_timer()

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for chessboard
        width = BOARD_SIZE * SQUARE_SIZE
        height = BOARD_SIZE * SQUARE_SIZE
        self.canvas = tk.Canvas(main_frame, width=width, height=height, bg=LIGHT_COLOR, highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=10, padx=(0, 20))
        self.canvas.bind("<Button-1>", self.on_square_click)

        # Right side panel
        right_panel = tk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky="ns")

        # Timer labels
        timer_frame = tk.Frame(right_panel)
        timer_frame.pack(pady=(0, 20))

        self.white_timer_label = tk.Label(timer_frame, text="White: 10:00", font=("Helvetica", 14, "bold"), fg="black")
        self.white_timer_label.pack()

        self.black_timer_label = tk.Label(timer_frame, text="Black: 10:00", font=("Helvetica", 14, "bold"), fg="black")
        self.black_timer_label.pack()

        # Move history box (scrollable text)
        history_frame = tk.Frame(right_panel)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_label = tk.Label(history_frame, text="Move History:", font=("Helvetica", 12, "bold"))
        self.history_label.pack(anchor="w")

        self.move_history = scrolledtext.ScrolledText(
            history_frame, width=30, height=20, state='disabled',
            font=("Courier", 10), wrap=tk.WORD
        )
        self.move_history.pack(fill=tk.BOTH, expand=True)

        # Game info label
        self.game_info = tk.Label(right_panel, text="", font=("Helvetica", 12))
        self.game_info.pack(pady=5)

        # Buttons frame
        btn_frame = tk.Frame(right_panel)
        btn_frame.pack(pady=20)

        self.quit_button = tk.Button(
            btn_frame, text="Quit Game", command=self.quit_to_start,
            bg="#D35400", fg="white", font=("Helvetica", 12, "bold"),
            padx=10
        )
        self.quit_button.pack(side=tk.LEFT, padx=5)

        self.restart_button = tk.Button(
            btn_frame, text="Restart Game", command=self.restart_game,
            bg="#27AE60", fg="white", font=("Helvetica", 12, "bold"),
            padx=10
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)

        self.flip_button = tk.Button(
            btn_frame, text="Flip Board", command=self.flip_board,
            bg="#3498DB", fg="white", font=("Helvetica", 12, "bold"),
            padx=10
        )
        self.flip_button.pack(side=tk.LEFT, padx=5)

    def load_images(self):
        for piece, file in PIECE_FILES.items():
            image = Image.open(file).convert("RGBA")
            image = image.resize((SQUARE_SIZE, SQUARE_SIZE), Image.LANCZOS)
            PIECE_IMAGES[piece] = ImageTk.PhotoImage(image)

    def draw_board(self):
        self.canvas.delete("square")
        self.canvas.delete("highlight")

        # Draw squares
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                display_row = 7 - row if not self.flipped else row
                display_col = col if not self.flipped else 7 - col

                color = LIGHT_COLOR if (display_row + display_col) % 2 == 0 else DARK_COLOR
                self.canvas.create_rectangle(
                    col * SQUARE_SIZE, row * SQUARE_SIZE,
                    (col + 1) * SQUARE_SIZE, (row + 1) * SQUARE_SIZE,
                    fill=color, tags="square"
                )

        # Highlight selected square
        if self.selected_square is not None:
            sq = self.selected_square
            rank = chess.square_rank(sq)
            file = chess.square_file(sq)
            if self.flipped:
                display_row = rank
                display_col = 7 - file
                row = 7 - display_row
                col = display_col
            else:
                row = 7 - rank
                col = file
            self.canvas.create_rectangle(
                col * SQUARE_SIZE, row * SQUARE_SIZE,
                (col + 1) * SQUARE_SIZE, (row + 1) * SQUARE_SIZE,
                fill=HIGHLIGHT_COLOR, stipple='gray50', tags="highlight"
            )

        # Highlight legal moves
        for move in self.legal_moves:
            to_square = move.to_square
            rank = chess.square_rank(to_square)
            file = chess.square_file(to_square)
            if self.flipped:
                display_row = rank
                display_col = 7 - file
                row = 7 - display_row
                col = display_col
            else:
                row = 7 - rank
                col = file

            if self.board.piece_at(to_square):
                # Draw a circle for captures
                center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                radius = SQUARE_SIZE // 3
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=HIGHLIGHT_LEGAL, width=3, tags="highlight"
                )
            else:
                # Draw a dot for regular moves
                center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                radius = SQUARE_SIZE // 8
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    fill=HIGHLIGHT_LEGAL, outline="", tags="highlight"
                )

    def draw_pieces(self):
        self.canvas.delete("piece")
        self.canvas.delete("promotion")

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                display_row = 7 - row if not self.flipped else row
                display_col = col if not self.flipped else 7 - col

                square = chess.square(display_col, display_row)
                piece = self.board.piece_at(square)
                if piece:
                    self.canvas.create_image(
                        col * SQUARE_SIZE + SQUARE_SIZE // 2,
                        row * SQUARE_SIZE + SQUARE_SIZE // 2,
                        image=PIECE_IMAGES[piece.symbol()],
                        tags="piece"
                    )

        # promotion of pawn
        if self.promotion_pieces:
            # Determine promotion square position
            promotion_square = self.promotion_move.to_square
            file = chess.square_file(promotion_square)

            if self.flipped:
                row = 0
            else:
                row = 7

            # Draw promotion pieces in a row
            for i, piece in enumerate(self.promotion_pieces):
                self.canvas.create_image(
                    file * SQUARE_SIZE + SQUARE_SIZE // 2,
                    row * SQUARE_SIZE + SQUARE_SIZE // 2 - (i * SQUARE_SIZE),
                    image=PIECE_IMAGES[piece],
                    tags="promotion"
                )

    def on_square_click(self, event):
        if self.game_over:
            return

        if self.promotion_pieces:
            self.handle_promotion_click(event)
            return

        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE

        if self.flipped:
            row = 7 - row
            col = 7 - col

        square = chess.square(col, 7 - row)  # Convert to chess format
        piece = self.board.piece_at(square)

        if self.selected_square is None:
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
                self.update_ui()
        else:
            move = None
            # Check if this is a promotion move
            for legal_move in self.legal_moves:
                if legal_move.to_square == square:
                    move = legal_move
                    break

            if move:
                if move.promotion:  # If promotion is needed
                    self.promotion_move = move
                    self.show_promotion_dialog(move)
                    return
                else:
                    self.make_move(move)
            else:
                # If clicked on another piece of the same color, select that instead
                if piece and piece.color == self.board.turn:
                    self.selected_square = square
                    self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
                    self.update_ui()
                else:
                    self.selected_square = None
                    self.legal_moves = []
                    self.update_ui()

    def handle_promotion_click(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE

        if self.flipped:
            row = 7 - row
            col = 7 - col

        # Get promotion square position
        promotion_square = self.promotion_move.to_square
        file = chess.square_file(promotion_square)

        if col != file:
            return  # Clicked on wrong file

        # Determine which piece was selected based on row
        promotion_row = 0 if self.flipped else 7
        piece_index = promotion_row - row

        if piece_index < 0 or piece_index >= len(self.promotion_pieces):
            return

        # Update the move with the selected promotion
        move = self.promotion_move
        move.promotion = chess.Piece.from_symbol(self.promotion_pieces[piece_index]).piece_type
        self.make_move(move)
        self.promotion_pieces = None
        self.promotion_move = None

    def show_promotion_dialog(self, move):
        # Determine which pieces to show based on color
        color = self.board.turn
        if color == chess.WHITE:
            self.promotion_pieces = ["Q", "R", "B", "N"]
        else:
            self.promotion_pieces = ["q", "r", "b", "n"]

        self.update_ui()

    def make_move(self, move):
        captured = self.board.piece_at(move.to_square)
        self.board.push(move)

        if captured:
            play_sound("capture")
        else:
            play_sound("move")

        if self.board.is_check() and not self.board.is_checkmate():
            play_sound("check")

        self.add_move_to_history(move)
        self.check_game_status()
        self.selected_square = None
        self.legal_moves = []
        self.update_ui()
        self.switch_timer()

        if not self.game_over and self.ai_mode and self.board.turn != (self.player_color == "white"):
            self.after(1000, self.play_ai_move)

    def play_ai_move(self):
        if not self.timer_running or self.board.is_game_over():
            return

        # Show "AI is thinking..." message
        self.game_info.config(text="AI is thinking...")
        self.update()

        # Add delay to make AI move more natural
        self.after(500, self._execute_ai_move)

    def _execute_ai_move(self):
        _, move = minimax(self.board, 3, -float('inf'), float('inf'), self.board.turn == chess.WHITE)
        if move:
            self.make_move(move)
        self.game_info.config(text="")

    def add_move_to_history(self, move):
        try:
            # Get the current move number
            move_number = self.board.fullmove_number

            # Get the move in algebraic notation
            try:
                move_text = self.board.san(move)
            except:
                # Fallback to UCI notation if SAN fails
                move_text = move.uci()

            self.move_history.config(state='normal')

            # If it's white's move, start a new line with move number
            if self.board.turn == chess.WHITE:
                # Check if we need to add a newline (not the first move)
                if not self.move_history.get("1.0", "end-1c").strip() == "":
                    self.move_history.insert(tk.END, "\n")
                self.move_history.insert(tk.END, f"{move_number}. {move_text}")
            else:
                # Black's move - add to the same line
                self.move_history.insert(tk.END, f" {move_text}")

            self.move_history.config(state='disabled')
            self.move_history.see(tk.END)
        except Exception as e:
            print("Error in move history:", e)
            # Fallback to UCI notation if everything fails
            self.move_history.config(state='normal')
            self.move_history.insert(tk.END, f"\n{move.uci()}")
            self.move_history.config(state='disabled')
            self.move_history.see(tk.END)

    def check_game_status(self):
        if self.board.is_checkmate():
            self.game_over = True
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            play_sound("game_over")
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins!")
            self.stop_timer()
        elif self.board.is_stalemate():
            self.game_over = True
            play_sound("game_over")
            messagebox.showinfo("Game Over", "Stalemate! It's a draw!")
            self.stop_timer()
        elif self.board.is_insufficient_material():
            self.game_over = True
            play_sound("game_over")
            messagebox.showinfo("Game Over", "Draw due to insufficient material!")
            self.stop_timer()
        elif self.board.is_seventyfive_moves():
            self.game_over = True
            play_sound("game_over")
            messagebox.showinfo("Game Over", "Draw by 75-move rule!")
            self.stop_timer()
        elif self.board.is_fivefold_repetition():
            self.game_over = True
            play_sound("game_over")
            messagebox.showinfo("Game Over", "Draw by fivefold repetition!")
            self.stop_timer()

    def update_ui(self):
        self.draw_board()
        self.draw_pieces()
        turn_text = "White" if self.board.turn == chess.WHITE else "Black"
        self.master.title(f"Chess Game - {turn_text}'s turn")

    def flip_board(self):
        self.flipped = not self.flipped
        self.update_ui()

    def quit_to_start(self):
        self.stop_timer()
        self.pack_forget()
        self.start_window.pack(fill=tk.BOTH, expand=True)

    def restart_game(self):
        self.board.reset()
        self.selected_piece = None
        self.selected_square = None
        self.legal_moves = []
        self.promotion_pieces = None
        self.promotion_move = None
        self.game_over = False
        self.move_history.config(state='normal')
        self.move_history.delete(1.0, tk.END)
        self.move_history.config(state='disabled')
        self.white_time = TIMER_SECONDS
        self.black_time = TIMER_SECONDS
        self.timer_running = False
        self.update_timer_labels()
        self.update_ui()
        self.start_timer()

    # Timer functions
    def start_timer(self):
        self.timer_running = True
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False

    def update_timer_labels(self):
        def sec_to_str(s):
            m = s // 60
            sec = s % 60
            return f"{m:02d}:{sec:02d}"

        self.white_timer_label.config(text=f"White: {sec_to_str(self.white_time)}")
        self.black_timer_label.config(text=f"Black: {sec_to_str(self.black_time)}")

    def update_timer(self):
        if not self.timer_running:
            return

        if self.board.turn == chess.WHITE:
            self.white_time -= 1
            if self.white_time <= 0:
                self.timer_running = False
                self.game_over = True
                play_sound("game_over")
                messagebox.showinfo("Time Over", "White's time is over! Black wins!")
                return
        else:
            self.black_time -= 1
            if self.black_time <= 0:
                self.timer_running = False
                self.game_over = True
                play_sound("game_over")
                messagebox.showinfo("Time Over", "Black's time is over! White wins!")
                return

        self.update_timer_labels()
        self.after(1000, self.update_timer)

    def switch_timer(self):
        pass


def evaluate_board(board):
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    value = 0

    # Material evaluation
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            v = piece_values.get(piece.piece_type, 0)
            value += v if piece.color == chess.WHITE else -v

    return value


def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None

    if maximizing:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move


class StartWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self, bg="#2C3E50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        # Title
        title_frame = tk.Frame(main_frame, bg="#2C3E50")
        title_frame.pack(pady=(20, 40))

        tk.Label(title_frame, text="Chess Master", font=("Helvetica", 36, "bold"),
                 fg="white", bg="#2C3E50").pack()

        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg="#2C3E50")
        btn_frame.pack(pady=20)

        # Play vs AI button with color selection
        ai_frame = tk.Frame(btn_frame, bg="#2C3E50")
        ai_frame.pack(fill=tk.X, pady=10)

        tk.Label(ai_frame, text="Play with AI:", font=("Helvetica", 14),
                 fg="white", bg="#2C3E50").pack(side=tk.LEFT, padx=10)

        colors = ["White", "Black", "Random"]
        self.ai_color = tk.StringVar(value="White")

        for color in colors:
            rb = tk.Radiobutton(ai_frame, text=color, variable=self.ai_color,
                                value=color, font=("Helvetica", 12),
                                fg="white", bg="#2C3E50", selectcolor="#2C3E50",
                                activebackground="#2C3E50", activeforeground="white")
            rb.pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Play With AI", command=self.play_ai,
                  width=20, font=("Helvetica", 14, "bold"),
                  bg="#3498DB", fg="white", activebackground="#2980B9",
                  padx=10, pady=5).pack(pady=10)

        # Play vs Human button
        tk.Button(btn_frame, text="Play With Friends", command=self.play_human,
                  width=20, font=("Helvetica", 14, "bold"),
                  bg="#27AE60", fg="white", activebackground="#219653",
                  padx=10, pady=5).pack(pady=10)

        # Quit button
        tk.Button(btn_frame, text="Quit", command=self.master.quit,
                  width=20, font=("Helvetica", 14, "bold"),
                  bg="#E74C3C", fg="white", activebackground="#C0392B",
                  padx=10, pady=5).pack(pady=10)

        # Footer
        footer_frame = tk.Frame(main_frame, bg="#2C3E50")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        tk.Label(footer_frame, text="By : Aqib Ahmed", font=("Helvetica", 10),
                 fg="white", bg="#2C3E50").pack()

    def play_ai(self):
        self.pack_forget()
        ChessGame(self.master, self, ai_mode=True, player_color=self.ai_color.get().lower()).pack(fill=tk.BOTH,
                                                                                                  expand=True)

    def play_human(self):
        self.pack_forget()
        ChessGame(self.master, self, ai_mode=False).pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Chess Game")
    root.geometry("800x700")

    #window icon
    try:
        root.iconbitmap("images/chess_icon.ico")
    except:
        pass

    StartWindow(root)
    root.mainloop()