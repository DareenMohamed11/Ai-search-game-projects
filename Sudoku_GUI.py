# sudoku_gui_scrollable.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import random
import threading

from main import ( order_lcv, forward_check, select_unassigned_var_mrv,
    clone_board,generate_puzzle, is_valid, solve_backtracking,
    init_domains, ac3_trace, find_empty,count_solutions,complete_to_unique_solution
)

CELL_SIZE = 65
ANIMATION_DELAY = 0.03

class SudokuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sudoku CSP - GUI Mode 1/2")
        self.puzzle = None
        self.solution = None
        self.cells = [[None]*9 for _ in range(9)]
        self.prefilled = [[False]*9 for _ in range(9)]
        self.status = tk.StringVar(value="Ready")
        self.geometry("750x850")
        # Track which cells the AI filled during solving
        self.ai_filled = set()
        self.build_ui()

    def build_ui(self):
        # --- Scrollable Canvas Setup ---
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Frame inside canvas ---
        scrollable_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # --- Main container ---
        container = tk.Frame(scrollable_frame)
        container.pack(expand=True)

        # Sudoku Grid
        frame = tk.Frame(container, bg="black")
        frame.pack(pady=20)

        for r in range(9):
            for c in range(9):
                cell = tk.Label(frame, text="", font=("Arial", 22),
                                width=2, height=1, bg="white",
                                relief="solid", bd=2)
                cell.grid(row=r, column=c, ipadx=10, ipady=10)
                if r % 3 == 0: cell.grid_configure(pady=(3, 0))
                if c % 3 == 0: cell.grid_configure(padx=(3, 0))
                self.cells[r][c] = cell

        # Buttons frame
        ctl = tk.Frame(container)
        ctl.pack(pady=10)

        ttk.Button(ctl, text="Easy Puzzle", command=lambda: self.gen("easy")).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(ctl, text="Medium Puzzle", command=lambda: self.gen("medium")).grid(row=0, column=1, padx=5, pady=3)
        ttk.Button(ctl, text="Hard Puzzle", command=lambda: self.gen("hard")).grid(row=0, column=2, padx=5, pady=3)
        ttk.Button(ctl, text="Mode 2 (User Input)", command=self.start_mode2).grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Solve (AI Demo)", command=self.start_solve_anim_thread).grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Solve (User)", command=self.start_user_solving).grid(row=4, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Reset", command=self.reset).grid(row=3, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Validate Board", command=self.validate_board) \
            .grid(row=5, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Check Solution Uniqueness", command=self.check_uniqueness) \
            .grid(row=6, column=0, columnspan=3, pady=5, sticky="ew")
        ttk.Button(ctl, text="Auto-Complete to Unique", command=self.auto_complete_to_unique) \
            .grid(row=8, column=0, columnspan=3, pady=5, sticky="ew")
        # Status label
        ttk.Label(container, textvariable=self.status).pack(pady=5)

    # --- Render ---
    def render(self, board, domains=None, ai_filled=None):
        if ai_filled is None:
            ai_filled = set()

        for r in range(9):
            for c in range(9):
                val = board[r][c]
                cell = self.cells[r][c]
                if val == 0:
                    if domains:
                        dom = domains.get((r,c), [])
                        txt = ''.join(str(x) for x in dom) if dom else ""
                        cell.config(text=txt, bg="white", font=("Arial", 10))
                    else:
                        cell.config(text="", bg="white", font=("Arial", 22))
                else:
                    if self.prefilled[r][c]:
                        bg = "#b2d8ff"  # prefilled
                    elif (r, c) in ai_filled:
                        bg = "#d0ffd0"  # AI solver filled
                    else:
                        bg = "#ffd6e6"  # user input
                    cell.config(text=str(val), bg=bg, font=("Arial", 22))
        self.update_idletasks()

    def gen(self, diff):
        holes = {"easy":36, "medium":44, "hard":52}[diff]
        self.status.set(f"Generating {diff} puzzle...")
        self.update()
        puzzle, sol = generate_puzzle(holes)
        self.puzzle = puzzle
        self.solution = sol
        self.ai_filled.clear()
        for r in range(9):
            for c in range(9):
                self.prefilled[r][c] = (puzzle[r][c] != 0)
        self.render(puzzle)
        self.status.set("Puzzle ready!")

    def reset(self):
        self.puzzle = [[0]*9 for _ in range(9)]
        self.solution = None
        self.prefilled = [[False]*9 for _ in range(9)]
        self.ai_filled.clear()
        for r in range(9):
            for c in range(9):
                self.cells[r][c].config(text="", bg="white")
        self.status.set("Board cleared.")

    # --- Mode 2 ---
    def start_mode2(self):
        self.status.set("Mode 2: Click cells to input numbers, then press Solve")
        if self.puzzle is None:
            self.puzzle = [[0]*9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                cell.config(bg="white")
                cell.bind("<Button-1>", lambda e, row=r, col=c: self.edit_cell(row, col))

    # --- User-solving mode ---
    def start_user_solving(self):
        if not self.puzzle:
            messagebox.showinfo("No puzzle", "Generate a puzzle or input one in Mode 2 first!")
            return

        # Check if board is empty or has too few clues
        clue_count = sum(1 for r in range(9) for c in range(9) if self.puzzle[r][c] != 0)
        if clue_count < 17:
            messagebox.showwarning("Too Few Clues",
                                   f"Only {clue_count} clues provided.\n"
                                   "A proper Sudoku needs at least 17 clues to potentially have a unique solution.\n"
                                   "This board likely has multiple solutions and is not a valid Sudoku puzzle.")
            return  # BLOCK user from solving

        # SAFETY CHECK: block user if board is unsolvable
        test_board = clone_board(self.puzzle)
        solvable = solve_backtracking(test_board)

        if not solvable:
            self.status.set("Cannot solve — board is invalid")
            self.mark_invalid_cells()
            messagebox.showerror(
                "Invalid Board",
                "This board has NO possible solution.\n"
            )
            return  # USER SOLVING IS BLOCKED HERE

        # Check for uniqueness - THIS IS CRITICAL FOR SUDOKU
        solutions = count_solutions(self.puzzle, limit=2)

        if solutions == 0:
            self.status.set("Board has no solutions")
            messagebox.showerror("Invalid Board", "This board has no possible solutions!")
            return

        elif solutions > 1:
            self.status.set("Board has multiple solutions")
            messagebox.showerror(
                "Invalid Sudoku Puzzle",
                f"This board has MULTIPLE possible solutions.\n"
                f"A proper Sudoku puzzle must have exactly ONE unique solution.\n\n"
                f"This violates standard Sudoku rules. Please fix the board first."
            )
            return  # BLOCK solving - this is not a valid Sudoku!

        # Only allow solving if board has EXACTLY ONE solution
        self.status.set("User-solving mode: Click cells to enter numbers")
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                if not self.prefilled[r][c]:
                    cell.config(bg="white")
                    cell.bind("<Button-1>", lambda e, row=r, col=c: self.edit_cell(row, col))
                else:
                    cell.config(bg="#b2d8ff")
                    cell.unbind("<Button-1>")
    def edit_cell(self, r, c):
        val = simpledialog.askstring("Input", f"Enter number for cell ({r+1},{c+1}) or leave empty")
        if val is None: return
        val = val.strip()
        if val == "" or val == "0":
            if (r, c) in self.ai_filled:
                self.ai_filled.discard((r, c))
            self.cells[r][c].config(text="", bg="white")
            if self.puzzle:
                self.puzzle[r][c] = 0
        elif val.isdigit() and 1 <= int(val) <= 9:
            if is_valid(self.puzzle, r, c, int(val)):
                if (r, c) in self.ai_filled:
                    self.ai_filled.discard((r, c))
                self.cells[r][c].config(text=val, bg="#ffd6e6")
                self.puzzle[r][c] = int(val)
            else:
                messagebox.showwarning("Invalid input", f"Number {val} violates Sudoku rules!")
        else:
            messagebox.showerror("Invalid input", "Enter a number between 1 and 9 or leave empty.")

    # --- AI Solver ---
    def start_solve_anim_thread(self):
        if not self.puzzle:
            messagebox.showinfo("No puzzle", "Generate a puzzle or use Mode 2 first!")
            return

        # Check if board is empty or has too few clues
        clue_count = sum(1 for r in range(9) for c in range(9) if self.puzzle[r][c] != 0)
        if clue_count < 17:
            messagebox.showwarning("Too Few Clues",
                                   f"Only {clue_count} clues provided.\n"
                                   "A proper Sudoku needs at least 17 clues to potentially have a unique solution.\n"
                                   "This board likely has multiple solutions and is not a valid Sudoku puzzle.")
            return  # BLOCK AI from solving

        # SAFETY CHECK: stop AI if board is unsolvable
        test_board = clone_board(self.puzzle)
        solvable = solve_backtracking(test_board)

        if not solvable:
            self.status.set("Cannot solve — board is invalid")
            self.mark_invalid_cells()
            messagebox.showerror("Invalid Board", "This board has NO possible solution.\n")
            return  # DO NOT START AI THREAD

        # Check for uniqueness - BLOCK AI if multiple solutions
        solutions = count_solutions(self.puzzle, limit=2)

        if solutions == 0:
            self.status.set("Board has no solutions")
            messagebox.showerror("Invalid Board", "This board has no possible solutions!")
            return

        elif solutions > 1:
            self.status.set("Board has multiple solutions")
            messagebox.showerror(
                "Invalid Sudoku Puzzle",
                f"This board has MULTIPLE possible solutions.\n"
                f"A proper Sudoku puzzle must have exactly ONE unique solution.\n\n"
                f"AI solving is blocked because this is not a valid Sudoku puzzle."
            )
            return  # BLOCK AI - this is not a valid Sudoku!

        # Only start AI if board has exactly one solution
        t = threading.Thread(target=self.solve_anim)
        t.daemon = True
        t.start()
    def solve_anim(self):
        work = clone_board(self.puzzle)
        self.ai_filled.clear()
        self.status.set("Solving (AC-3 + BT fallback)...")
        self.update()
        start = time.perf_counter()
        domains = init_domains(work)
        ac3_generator = ac3_trace(domains)

        for event in ac3_generator:
            etype = event['type']
            if etype == 'revise':
                Xi = event['Xi']; Xj = event['Xj']
                self.highlight_cells([Xi, Xj], "#ffef99")
                self.render(work, domains, ai_filled=self.ai_filled)
                time.sleep(ANIMATION_DELAY)
                self.unhighlight_cells([Xi, Xj])
            elif etype == 'singleton':
                Xi = event['Xi']; val = event['value']; r, c = Xi
                was_empty_original = (self.puzzle is None) or (self.puzzle[r][c] == 0)
                if not self.prefilled[r][c] and was_empty_original:
                    self.ai_filled.add((r, c))
                work[r][c] = val
                self.render(work, domains, ai_filled=self.ai_filled)
                time.sleep(ANIMATION_DELAY)

        for r in range(9):
            for c in range(9):
                if len(domains[(r,c)]) == 1:
                    work[r][c] = domains[(r,c)][0]
                    if not self.prefilled[r][c] and ((self.puzzle is None) or (self.puzzle[r][c] == 0)):
                        self.ai_filled.add((r, c))

        if find_empty(work) is not None:
            solved = self._bt_anim(work)
            total_time = time.perf_counter() - start
            if solved:
                self.status.set(f"Solved in {total_time:.3f}s (AC-3 + BT)")
            else:
                self.status.set("Unsolvable puzzle!")
        else:
            total_time = time.perf_counter() - start
            self.status.set(f"Solved (AC-3) in {total_time:.3f}s")

        self.render(work, ai_filled=self.ai_filled)
        self.puzzle = work

    def highlight_cells(self, positions, color):
        for (r, c) in positions:
            self.cells[r][c].config(bg=color)
        self.update_idletasks()

    def unhighlight_cells(self, positions):
        for (r, c) in positions:
            lbl = self.cells[r][c]
            if self.prefilled[r][c]:
                lbl.config(bg="#b2d8ff")
            elif (r, c) in self.ai_filled:
                lbl.config(bg="#d0ffd0")
            else:
                if self.puzzle and self.puzzle[r][c] != 0:
                    lbl.config(bg="#ffd6e6")
                else:
                    lbl.config(bg="white")
        self.update_idletasks()

    def _bt_anim(self, board):
        loc = select_unassigned_var_mrv(board)
        if not loc:
            return True
        r, c = loc

        for val in order_lcv(board, r, c):
            if is_valid(board, r, c, val):
                board[r][c] = val
                self.ai_filled.add((r, c))
                self.cells[r][c].config(text=str(val), bg="#d0ffd0")
                self.update_idletasks()
                time.sleep(ANIMATION_DELAY)

                if forward_check(board, r, c, val) and self._bt_anim(board):
                    return True

                board[r][c] = 0
                if (r, c) in self.ai_filled:
                    self.ai_filled.remove((r, c))
                self.cells[r][c].config(text="", bg="white")
                self.update_idletasks()
                time.sleep(ANIMATION_DELAY)

        return False

    def validate_board(self):
        if not self.puzzle:
            messagebox.showinfo("No board", "Please enter a board first using Mode 2.")
            return

        self.status.set("Validating board...")
        self.update()

        # First check if solvable
        test_board = clone_board(self.puzzle)
        solvable = solve_backtracking(test_board)

        if not solvable:
            messagebox.showerror("Invalid Board",
                                 "This board has NO possible solution!\n"
                                 "It violates basic Sudoku constraints.")
            self.status.set("Board is NOT solvable")
            return

        # If solvable, check for uniqueness
        solutions = count_solutions(self.puzzle, limit=2)

        if solutions == 1:
            messagebox.showinfo("Valid Sudoku",
                                " PERFECT! This is a valid Sudoku puzzle.\n"
                                " Has exactly ONE unique solution\n"
                                " Meets all Sudoku requirements")
            self.status.set("Valid Sudoku (unique solution)")
        elif solutions == 0:
            messagebox.showwarning("Unexpected Error",
                                   "Unexpected: No solutions found despite passing initial check")
            self.status.set("No solutions found")
        else:
            messagebox.showerror("Invalid Sudoku",
                                 "NOT a valid Sudoku puzzle!\n"
                                 f"This board has {solutions}+ possible solutions.\n"
                                 "A proper Sudoku must have exactly ONE unique solution.")
            self.status.set("Invalid: Multiple solutions")

    def mark_invalid_cells(self):
        """Mark cells that violate Sudoku rules with red background"""
        # Reset all cells first
        for r in range(9):
            for c in range(9):
                if self.prefilled[r][c]:
                    self.cells[r][c].config(bg="#b2d8ff")
                elif self.puzzle[r][c] != 0:
                    self.cells[r][c].config(bg="#ffd6e6")
                else:
                    self.cells[r][c].config(bg="white")

        # Check for conflicts in rows
        for r in range(9):
            seen = set()
            for c in range(9):
                val = self.puzzle[r][c]
                if val != 0:
                    if val in seen:
                        # Mark all instances of this value in the row
                        for cc in range(9):
                            if self.puzzle[r][cc] == val:
                                self.cells[r][cc].config(bg="#ffcccc")
                    else:
                        seen.add(val)

        # Check for conflicts in columns
        for c in range(9):
            seen = set()
            for r in range(9):
                val = self.puzzle[r][c]
                if val != 0:
                    if val in seen:
                        # Mark all instances of this value in the column
                        for rr in range(9):
                            if self.puzzle[rr][c] == val:
                                self.cells[rr][c].config(bg="#ffcccc")
                    else:
                        seen.add(val)

        # Check for conflicts in 3x3 boxes
        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                seen = set()
                cells_in_box = []
                for r in range(box_r, box_r + 3):
                    for c in range(box_c, box_c + 3):
                        val = self.puzzle[r][c]
                        if val != 0:
                            if val in seen:
                                # Mark all instances in this box
                                for rr in range(box_r, box_r + 3):
                                    for cc in range(box_c, box_c + 3):
                                        if self.puzzle[rr][cc] == val:
                                            self.cells[rr][cc].config(bg="#ffcccc")
                            else:
                                seen.add(val)

    def check_uniqueness(self):
        """Check if the current board has exactly one solution"""
        if not self.puzzle:
            messagebox.showinfo("No board", "Please enter a board first.")
            return

        # Count solutions (limit to 2 for efficiency)
        solutions = count_solutions(self.puzzle, limit=2)

        if solutions == 0:
            messagebox.showinfo("No Solutions", "This board has no valid solutions.")
        elif solutions == 1:
            messagebox.showinfo("Unique Solution",
                                "Perfect! This board has exactly ONE solution.\n"
                                "This is a proper Sudoku puzzle.")
        else:
            messagebox.showwarning("Multiple Solutions",
                                   f"This board has MULTIPLE solutions (at least {solutions}).\n"
                                   "A proper Sudoku should have exactly one unique solution.")

    def auto_complete_to_unique(self):
        """Complete the current board to have a unique solution"""
        if not self.puzzle:
            messagebox.showinfo("No Board", "Please enter a board first.")
            return

        # Count current clues
        clue_count = sum(1 for r in range(9) for c in range(9) if self.puzzle[r][c] != 0)

        # Check if board is solvable
        test_board = clone_board(self.puzzle)
        if not solve_backtracking(test_board):
            messagebox.showerror("Unsolvable",
                                 "This board has conflicting numbers.\n"
                                 "Use 'Validate Board' to find errors.")
            return

        self.status.set(f"Creating puzzle from {clue_count} clues...")
        self.update()

        # Try to auto-complete to a unique puzzle
        completed_puzzle = complete_to_unique_solution(self.puzzle)

        if completed_puzzle:
            # Calculate what was added
            added_cells = []
            for r in range(9):
                for c in range(9):
                    if self.puzzle[r][c] == 0 and completed_puzzle[r][c] != 0:
                        added_cells.append((r, c, completed_puzzle[r][c]))

            # Count total clues in completed puzzle
            total_clues = sum(1 for r in range(9) for c in range(9) if completed_puzzle[r][c] != 0)

            # Update the board
            old_puzzle = clone_board(self.puzzle)
            self.puzzle = completed_puzzle

            # Update prefilled status (only keep original as prefilled)
            for r in range(9):
                for c in range(9):
                    self.prefilled[r][c] = (old_puzzle[r][c] != 0)

            # Clear AI filled
            self.ai_filled.clear()

            # Render
            self.render(self.puzzle)

            # Check if the result is a full solution or a puzzle
            is_full_solution = all(completed_puzzle[r][c] != 0 for r in range(9) for c in range(9))

            if is_full_solution:
                messagebox.showinfo("Complete Solution",
                                    f"Board completed to a full solution!\n\n"
                                    f"Starting clues: {clue_count}\n"
                                    f"Added cells: {81 - clue_count}\n\n"
                                    f"Note: With only {clue_count} starting clues,\n"
                                    f"the only way to guarantee uniqueness was to\n"
                                    f"fill ALL remaining cells.")
            else:
                # Determine difficulty based on total clues
                if total_clues > 45:
                    difficulty = "Easy"
                elif total_clues > 37:
                    difficulty = "Medium"
                else:
                    difficulty = "Hard"

                messagebox.showinfo("Success!",
                                    f"✓ Created a Sudoku puzzle!\n\n"
                                    f"Starting clues: {clue_count}\n"
                                    f"Added clues: {len(added_cells)}\n"
                                    f"Total clues: {total_clues}\n\n"
                                    f"Difficulty: {difficulty}\n"
                                    f"Has exactly one unique solution!")

                self.status.set(f"Created {total_clues}-clue puzzle")
        else:
            messagebox.showwarning("Failed",
                                   "Could not create a proper puzzle.\n"
                                   "Your clues might be too sparse or conflicting.\n"
                                   "Try adding more numbers in the same row/column/box.")
            self.status.set("Auto-complete failed")
if __name__ == "__main__":
    app = SudokuGUI()
    app.mainloop()
