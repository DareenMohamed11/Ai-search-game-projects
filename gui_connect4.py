import tkinter as tk
from tkinter import messagebox
import time
import csv
import os
import threading

from connectfour import (
    Connect4Board1D,
    Connect4Minimax,
    Connect4Expectiminimax,
    Connect4AlphaBeta,
    Connect4Heuristic
)


class Connect4GUI:
    def __init__(self, game, ai_depth=3):
        self.game = game
        self.ai_depth = ai_depth
        self.cell_size = 60

        self.root = tk.Tk()
        self.root.title("Connect4")

        # --- Variables ---
        self.algorithm_choice = tk.StringVar(value="expecti")
        self.tree_option = tk.StringVar(value="chosen")  # none / chosen / full / leaf
        self.expecti_probs = {}  # store probabilities for GUI tree

        # --- Top control bar ---
        ctrl = tk.Frame(self.root)
        ctrl.pack(pady=5)

        tk.Label(ctrl, text="Algorithm:").grid(row=0, column=0)
        tk.Radiobutton(ctrl, text="Minimax", variable=self.algorithm_choice, value="minimax").grid(row=0, column=1)
        tk.Radiobutton(ctrl, text="Alpha-Beta", variable=self.algorithm_choice, value="alphabeta").grid(row=0, column=2)
        tk.Radiobutton(ctrl, text="Expectimax", variable=self.algorithm_choice, value="expecti").grid(row=0, column=3)

        tk.Label(ctrl, text="Depth:").grid(row=0, column=4, padx=(15, 0))
        self.depth_entry = tk.Entry(ctrl, width=3)
        self.depth_entry.insert(0, str(ai_depth))
        self.depth_entry.grid(row=0, column=5)

        tk.Label(ctrl, text="Tree:").grid(row=0, column=6)
        tk.OptionMenu(ctrl, self.tree_option, "none", "chosen", "full", "leaf").grid(row=0, column=7)

        tk.Button(ctrl, text="Restart", command=self.restart).grid(row=0, column=8, padx=6)

        # --- Board canvas ---
        self.canvas = tk.Canvas(self.root,
                                width=self.game.width * self.cell_size,
                                height=self.game.height * self.cell_size + 300,
                                bg="#FFDDEE")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.user_click)

        self.turn_label = tk.Label(self.root, text="Your Turn!", font=("Arial", 14))
        self.turn_label.pack()
        self.score_label = tk.Label(self.root, text="Score — You:0 | AI:0", font=("Arial", 12))
        self.score_label.pack()

        self.results_file = "results.csv"
        self._ensure_results_csv()

        self.ai = None
        self.last_ai_move = None
        self.create_ai()
        self.draw()

    # --- Ensure results CSV has header ---
    def _ensure_results_csv(self):
        if not os.path.exists(self.results_file):
            with open(self.results_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "algorithm", "depth", "move_number", "move_col", "nodes", "time_s"])

    # --- AI creation ---
    def create_ai(self):
        try:
            depth = int(self.depth_entry.get())
        except:
            depth = self.ai_depth
        alg = self.algorithm_choice.get()
        print_tree_flag = (self.tree_option.get() != "none")

        if alg == "minimax":
            self.ai = Connect4Minimax(Connect4Heuristic(), max_depth=depth, print_tree=print_tree_flag)
        elif alg == "alphabeta":
            self.ai = Connect4AlphaBeta(Connect4Heuristic(), max_depth=depth, print_tree=print_tree_flag)
        else:
            self.ai = Connect4Expectiminimax(Connect4Heuristic(), max_depth=depth, print_tree=print_tree_flag)

    def restart(self):
        self.game = Connect4Board1D()
        self.draw()
        self.update_score()
        self.turn_label.config(text="Your Turn!")
        self.create_ai()
        self.last_ai_move = None
        self.expecti_probs = {}

    # --- Draw the board ---
    def draw(self):
        self.canvas.delete("all")
        for r in range(self.game.height):
            for c in range(self.game.width):
                x1 = c * self.cell_size + 5
                y1 = r * self.cell_size + 5
                x2 = x1 + self.cell_size - 10
                y2 = y1 + self.cell_size - 10
                v = self.game.board[r * self.game.width + c]
                col = "white"
                if v == 1: col = "#1E90FF"
                if v == -1: col = "#C71585"
                self.canvas.create_oval(x1, y1, x2, y2, fill=col, outline="black")

        if getattr(self, "last_ai_move", None) is not None:
            col = self.last_ai_move
            h = self.game.heights[col]
            if h > 0:
                row = self.game.height - h
                x_center = col * self.cell_size + self.cell_size / 2
                y_center = row * self.cell_size + self.cell_size / 2
                r = self.cell_size/2 - 6
                self.canvas.create_oval(x_center - r, y_center - r, x_center + r, y_center + r, outline="yellow", width=3)

    def user_click(self, e):
        if self.game.is_full(): return
        col = e.x // self.cell_size
        if col not in self.game.generate_moves(): return

        self.game.current_player = -1
        self.game.make_move(col)
        self.draw()
        self.update_score()

        if self.game.is_full():
            self.show_winner()
            return

        self.turn_label.config(text="AI thinking...")
        threading.Thread(target=self.ai_turn).start()

    # --- AI Turn ---
    def ai_turn(self):
        if self.game.is_full():
            self.root.after(0, self.show_winner)
            return

        self.create_ai()
        self.game.current_player = 1
        self.expecti_probs = {}

        # Patch Expectiminimax to capture probabilities for GUI tree
        if isinstance(self.ai, Connect4Expectiminimax):
            self.expecti_probs = {}
            original_chance = self.ai._chance_node  # store original

            def patched_chance_node(board, col, depth, indent=0):
                val = original_chance(board, col, depth, indent)
                moves = board.generate_moves()
                prob = 1.0 / max(1, len(moves))  # uniform probability
                self.expecti_probs[col] = prob
                return val

            self.ai._chance_node = patched_chance_node

        # Optional tree printing

            print(f"\n=== AI Turn: Depth={self.ai.max_depth}, Algorithm={self.algorithm_choice.get()} ===")
            board_clone_for_print = self.clone_board(self.game)
            self.print_tree_console(board_clone_for_print, self.ai)

        # --- Measure AI computation time ---
        start_time = time.time()
        move = self.ai.get_best_move(self.game)
        elapsed = time.time() - start_time

        # Restore original method
        if isinstance(self.ai, Connect4Expectiminimax):
            self.ai._chance_node = original_chance

        # --- Log move ---
        nodes = getattr(self.ai, "nodes", getattr(self.ai, "nodes_evaluated", None))
        nodes = int(nodes) if nodes is not None else None

        alg_name = self.algorithm_choice.get()
        depth = self.ai.max_depth
        move_number = sum(self.game.heights) + 1
        print(f"[MOVE LOG] alg={alg_name} depth={depth} move_num={move_number} chosen_col={move} nodes={nodes} time_s={elapsed:.4f}")

        # Save to CSV
        with open(self.results_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), alg_name, depth, move_number, move, nodes, f"{elapsed:.4f}"])

        if move in self.game.generate_moves():
            self.game.make_move(move)
            self.last_ai_move = move

        self.root.after(0, self.finish_ai_turn)

    def finish_ai_turn(self):
        self.draw()
        self.update_score()

        if self.tree_option.get() != "none":
            board_clone_for_draw = self.clone_board(self.game)
            self.draw_tree_graphically(self.tree_option.get(), board_clone_for_draw)

        if self.game.is_full():
            self.show_winner()
        else:
            self.turn_label.config(text="Your Turn!")

    def update_score(self):
        ai = self.game.count_fours(1)
        hu = self.game.count_fours(-1)
        self.score_label.config(text=f"Score — You:{hu} | AI:{ai}")

    def show_winner(self):
        ai = self.game.count_fours(1)
        hu = self.game.count_fours(-1)
        winner = self.game.check_winner()
        if winner == 1:
            msg = f"AI wins! AI:{ai} You:{hu}"
        elif winner == -1:
            msg = f"You win! You:{hu} AI:{ai}"
        else:
            msg = f"Draw! AI:{ai} You:{hu}"
        messagebox.showinfo("Game Over", msg)

    def clone_board(self, board):
        b = Connect4Board1D(board.width, board.height)
        b.board = list(board.board)
        b.heights = list(board.heights)
        b.current_player = board.current_player
        return b

    # --- Fixed GUI tree drawing ---
    def draw_tree_graphically(self, option="chosen", board_clone=None):
        self.canvas.delete("tree")
        start_y = self.game.height * self.cell_size + 20
        tree_width = self.game.width * self.cell_size

        if board_clone is None:
            board_clone = self.clone_board(self.game)

        root_move = self.last_ai_move if self.last_ai_move is not None else 0
        self._draw_subtree(board_clone, self.ai, 0, 0, tree_width, start_y, option, parent_x=None, root_move=root_move)

    def _draw_subtree(self, board, ai, depth, x_min, x_max, y, option, parent_x=None, is_ai_turn=True, root_move=None):
        if board.is_full() or depth >= ai.max_depth:
            return

        moves_to_consider = []
        if option == "full":
            moves_to_consider = board.generate_moves()
        elif option == "chosen":
            moves_to_consider = [root_move] if depth == 0 and root_move is not None else board.generate_moves()[:2]
        elif option == "leaf":
            moves_to_consider = [root_move] if depth == 0 and root_move is not None else board.generate_moves()[:1]

        n = len(moves_to_consider)
        if n == 0:
            return

        for i, move in enumerate(moves_to_consider):
            child_x = x_min + (i + 0.5) * (x_max - x_min) / n
            node_radius = 15
            node_color = "#1E90FF" if is_ai_turn else "#C71585"
            self.canvas.create_oval(child_x - node_radius, y - node_radius, child_x + node_radius, y + node_radius,
                                    fill=node_color, tags="tree")

            # clone board for safety and proper heuristic evaluation
            local_board = self.clone_board(board)
            local_board.make_move(move)
            try:
                leaf_value = ai.heuristic.evaluate(local_board, 1, -1) if is_ai_turn else ai.heuristic.evaluate(local_board, -1, 1)
            except Exception:
                leaf_value = None

            label = f"C={move+1}"
            if leaf_value is not None:
                label += f"\nH={leaf_value:.0f}"

            # Add probability for Expectiminimax chance nodes
            if not is_ai_turn and isinstance(ai, Connect4Expectiminimax):
                prob = self.expecti_probs.get(move, 1.0 / max(1, len(board.generate_moves())))
                label += f"\nP={prob:.2f}"

            self.canvas.create_text(child_x, y, text=label, tags="tree", fill="white")

            if parent_x is not None:
                parent_y = y - 60
                self.canvas.create_line(parent_x, parent_y, child_x, y - node_radius, tags="tree")

            next_x_min = x_min + i * (x_max - x_min) / n
            next_x_max = x_min + (i + 1) * (x_max - x_min) / n
            self._draw_subtree(local_board, ai, depth + 1, next_x_min, next_x_max, y + 70, option,
                               parent_x=child_x, is_ai_turn=not is_ai_turn)

    # --- Fixed console tree printing ---
    def print_tree_console(self, board, ai, depth=0, max_depth=None, maxing=True, indent=""):
        if max_depth is None:
            max_depth = ai.max_depth

        if board.is_full() or depth >= max_depth:
            try:
                h = ai.heuristic.evaluate(board, 1, -1) if maxing else ai.heuristic.evaluate(board, -1, 1)
            except Exception:
                h = None
            print(f"{indent}[Leaf] h={h}")
            return

        is_expectimax = hasattr(ai, "chance_probs")  # example flag, adjust if your AI has it

        moves = board.generate_moves()
        for i, move in enumerate(moves):
            is_last = i == len(moves) - 1
            branch = "└──" if is_last else "├──"
            next_indent = indent + ("    " if is_last else "│   ")

            board.make_move(move)
            try:
                h = ai.heuristic.evaluate(board, 1, -1) if maxing else ai.heuristic.evaluate(board, -1, 1)
            except Exception:
                h = None

            if is_expectimax and not maxing:  # chance node
                prob = getattr(ai, "chance_probs", {}).get(move, 1.0 / len(moves))
                print(f"{indent}{branch} [Chance] col={move + 1} prob={prob:.2f} val={h}")
            else:
                player_str = "AI" if maxing else "Human"
                print(f"{indent}{branch} [{player_str}] depth={depth} col={move + 1} h={h}")

            self.print_tree_console(board, ai, depth + 1, max_depth, not maxing, next_indent)
            board.undo_move(move)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Connect4GUI(Connect4Board1D()).run()

