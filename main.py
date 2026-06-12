# main.py
import random
import time

# -------------------------------------------------
# -------------------------------------------------

#  BASIC BOARD UTILITIES

#bt3ml empty board
def empty_board():
    # b3ml list  9 elements, kol element is a row.
    # Each row is also a list of 9 zeros.
    # 0 means "empty cell" in Sudoku.
    return [[0 for _ in range(9)] for _ in range(9)]


#bt3ml copy mn board
def clone_board(board):
    # bcreate a new list of rows.
    # row[:] means "copy the row" 3shan al boardCopy my sharysh memory m3a board aslya.
    return [row[:] for row in board]


# bt3ml a printable board shape
def board_to_string(board):
    return '\n'.join(                      # Join each row with a newline
        ' '.join(                          # Join each value with a space
            str(v) if v != 0 else '.'      # Show number, or '.' if value is 0 (empty)
            for v in row                   # Loop through each value in the row
        )
        for row in board                   # Loop through each row of the board
    )

# -------------------------------------------------
# -------------------------------------------------

#Constraint Checking

#btcheck eny a7ot val fy cell (r,c) valid wala la2a
def is_valid(board, r, c, val):

    # btcheck al row
    for i in range(9):
        if board[r][i] == val:  # if 'val' already exists in row r
            return False  # cannot place it

    #btcheck al column
    for i in range(9):
        if board[i][c] == val:  # if 'val' already exists in column c
            return False  # cannot place it

    # btcheck al 3x3 BOX CHECK
    # bgeb al top-left corner of the 3x3 block
    # --------------------------
    br = (r // 3) * 3  # block row start
    bc = (c // 3) * 3  # block column start

    for rr in range(br, br + 3):  # loop through the 3 rows of the block
        for cc in range(bc, bc + 3):  # loop through 3 columns of the block
            if board[rr][cc] == val:
                return False  # found same val → not valid

    # --------------------------
    # If none of the checks failed → it's valid
    # --------------------------
    return True


#bageb awl empty cell (0) on the board.
# Returns (row, col) or None if full.
def find_empty(board):
    # Loop through every row
    for r in range(9):
        # Loop through every column in that row
        for c in range(9):
            # If this cell contains 0 → it's empty
            if board[r][c] == 0:
                return r, c  # return its position

    # If no empty cell was found → the board is full
    return None


# -------------------------------------------------
# HEURISTICS
# -------------------------------------------------

# MRV
def select_unassigned_var_mrv(board):
    min_domain = 10  # Start with something bigger than any possible domain size
    best = None  # Best cell so far

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:  # Only consider empty cells
                # Count how many values 1–9 are valid in this cell
                domain_size = sum(is_valid(board, r, c, v) for v in range(1, 10))

                # Pick the cell with the smallest domain size
                if domain_size < min_domain:
                    min_domain = domain_size
                    best = (r, c)

    return best  # Return the cell with mrv


# LCV
def order_lcv(board, r, c):
    # Least Constraining Value (choose value that limits neighbors least)
    scores = []
    for v in range(1, 10):
        if is_valid(board, r, c, v):
            count = 0
            for (rr, cc) in get_neighbors(r, c):
                if board[rr][cc] == 0 and is_valid(board, rr, cc, v):
                    count += 1
            scores.append((count, v))
    scores.sort()
    return [v for (_, v) in scores]

# Forward Checking
def forward_check(board, r, c, val):
    # Check neighbors can still take at least one valid value
    for (rr, cc) in get_neighbors(r, c):
        if board[rr][cc] == 0:
            if not any(is_valid(board, rr, cc, v) for v in range(1, 10)):
                return False
    return True

# -------------------------------------------------
# BACKTRACKING SOLVER
#awl 7aga solve_backtracking picks a cell (MRV).
#For that cell, order_lcv chooses numbers smartly.

#For each number:
#Check is_valid → is this legal?
#Place it temporarily
#forward_check → will neighbors be okay?
#Recurse → solve_backtracking on new board
#If fail → undo move (board[r][c] = 0) and try next number
#This continues until the board is solved or all options fail.
# -------------------------------------------------

def solve_backtracking(board):
    #b5tar most constrained empty cell using MRV (fewest options).
    loc = select_unassigned_var_mrv(board)

    #lw mafesh yaba mafesh empty cell w board is solved
    if not loc:
        return True

    r, c = loc

    #hgrb arkam in LCV order al least constraining al awl
    for val in order_lcv(board, r, c):
        if is_valid(board, r, c, val):
            #lw valid hplace temporarily
            board[r][c] = val

            #h3ml forward check
            if forward_check(board, r, c, val):
                if solve_backtracking(board):
                    return True

            board[r][c] = 0 #hy undo move

    return False # lw kolohom failed


# -------------------------------------------------
# -------------------------------------------------

#  solution COUNTER (used to ensure uniqueness)
def count_solutions(board, limit=2):

    counter = [0]

    def _helper(b):
        if counter[0] >= limit:
            return
        empty = find_empty(b)
        if not empty:
            counter[0] += 1
            return
        r, c = empty
        for v in range(1, 10):
            if is_valid(b, r, c, v):
                b[r][c] = v
                _helper(b)
                b[r][c] = 0
                if counter[0] >= limit:
                    return

    # bsht8l 3la clone
    board_copy = clone_board(board)
    _helper(board_copy)
    return counter[0]

# -------------------------------------------------
#  PUZZLE GENERATOR
# -------------------------------------------------

def fill_box(board, br, bc):
    nums = list(range(1, 10))
    random.shuffle(nums)
    idx = 0
    for r in range(br, br+3):
        for c in range(bc, bc+3):
            board[r][c] = nums[idx]
            idx += 1

def fill_diagonal(board):
    for k in range(0, 9, 3):
        fill_box(board, k, k)

def generate_full_solution():
    board = empty_board()
    fill_diagonal(board)
    solve_backtracking(board)
    return board

def remove_cells(board, holes):
    """
    Remove cells while ensuring the resulting puzzle has exactly one solution.
    We try random positions and remove a cell only if the puzzle remains unique.
    """
    coords = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(coords)

    removed = 0
    for r, c in coords:
        if removed >= holes:
            break
        backup = board[r][c]
        board[r][c] = 0

        # Check uniqueness: count solutions up to 2
        copy_board = clone_board(board)
        sols = count_solutions(copy_board, limit=2)

        if sols == 1:
            removed += 1
        else:
            board[r][c] = backup

    return board

def generate_puzzle(holes=40):
    full = generate_full_solution()
    puzzle = clone_board(full)
    puzzle = remove_cells(puzzle, holes)
    return puzzle, full

# -------------------------------------------------
#  CSP + AC-3
# -------------------------------------------------

#b3ml domain (list of possible numbers ) le kol cell
def init_domains(board):
    domains = {}
    for r in range(9):
        for c in range(9):
            #lw already filled
            if board[r][c] != 0:
                domains[(r, c)] = [board[r][c]]
            #lw la2a ha7ot kol arkam mn 1 le 9
            else:
                domains[(r, c)] = [i for i in range(1,10)]
    return domains

#btrg3 neighbors le cell mo3yna
def get_neighbors(r, c):
    neighbors = set()
    for cc in range(9):
        if cc != c:
            neighbors.add((r, cc))

    for rr in range(9):
        if rr != r:
            neighbors.add((rr, c))

    br = (r // 3) * 3
    bc = (c // 3) * 3
    for rr in range(br, br+3):
        for cc in range(bc, bc+3):
            if rr != r or cc != c:
                neighbors.add((rr, cc))

    return neighbors

#btcreate all arcss
def create_arcs():
    arcs = []
    #loop through every cell
    for r in range(9):
        for c in range(9):
            #bageb neighbours cell de
            neighbors = get_neighbors(r, c)
            for (rr, cc) in neighbors:
                #Create an arc (cell, neighbor) for every neighbor
                arcs.append(((r, c), (rr, cc)))
    return arcs

#checks if any value in Xi is impossible because of Xj
def revise(domains, Xi, Xj):
    revised = False #btrack 3shan lw 3mlna remove le ay value
    xi_values = domains[Xi][:]
    xj_values = domains[Xj]

    for x in xi_values:
        supported = False
        for y in xj_values:
            if x != y:
                supported = True
                break

        if not supported:
            domains[Xi].remove(x)
            revised = True

    return revised

#Goal: For each cell, shrink its domain by removing impossible numbers.
#Works with arcs (Xi, Xj)
def ac3(domains):
    #b3ml list le kol al arcs aly fe board
    arcs = create_arcs()
    #w a3ml copy mnhom w a7othom fy queue
    queue = arcs[:]

    while queue:
        Xi, Xj = queue.pop(0)
        if revise(domains, Xi, Xj):
            #lw domain xi b2a empty , y3ne mafesh ay 7aga tnf3o , yaba AC failed , return false
            if len(domains[Xi]) == 0:
                return False
            #8er kda lw domain bs et8yr lakn msh zero
            #h re add kol neighbors bta3t xi m3ada xj fy queue 3shan 5alas 3mlt arc dah
            for Xk in get_neighbors(*Xi):
                if Xk != Xj:
                    queue.append((Xk, Xi))

    #hfdl a3ml kda le7ad ma queue yaba fade
    #lama queue yaba fade yaba AC3 succeeded , w hreturn true
    return True

#fill in cells that have only one option
def update_board_with_domains(board, domains):
    changed = False
    for r in range(9):
        for c in range(9):
            if len(domains[(r,c)]) == 1:
                if board[r][c] == 0:
                    board[r][c] = domains[(r,c)][0]
                    changed = True
    return changed


def ac3_trace(domains):

    arcs = create_arcs()
    queue = arcs[:]
    #count how many times we actually remove something from a domain
    total_revisions = 0
    #count how many values we removed in total.
    total_pruned = 0

    while queue:
        Xi, Xj = queue.pop(0)

        #Save a copy of the domains of Xi and Xj before revising
        xi_before = domains[Xi][:]
        xj_before = domains[Xj][:]

        print(f"Revising arc ({Xi}, {Xj})")
        print(f"Current domain of {Xi}: {xi_before}")
        print(f"Domain of {Xj}: {xj_before}")

        removed = []

        for x in xi_before:
            supported = False
            for y in xj_before:
                if x != y:   # Sudoku constraint
                    supported = True
                    break

            if not supported:
                domains[Xi].remove(x)
                removed.append(x)
                total_pruned += 1

                print(
                    f"Removed value {x} from {Xi} because no supporting value exists in {Xj}"
                )

        if removed:
            total_revisions += 1
            xi_after = domains[Xi][:]

            print(f"Updated domain of {Xi}: {xi_after}")
            print("-------------------------------------")


            yield {
                'type': 'revise',
                'Xi': Xi,
                'Xj': Xj,
                'xi_before': xi_before,
                'xj': xj_before,
                'removed': removed,
                'xi_after': xi_after
            }

            # Re-enqueue neighbors
            for Xk in get_neighbors(*Xi):
                if Xk != Xj:
                    queue.append((Xk, Xi))


            if len(domains[Xi]) == 1:
                yield {
                    'type': 'singleton',
                    'Xi': Xi,
                    'value': domains[Xi][0]
                }

    print(f"\n=== AC-3 SUMMARY ===")
    print(f"Total revisions: {total_revisions}")
    print(f"Total values pruned: {total_pruned}")
    print(f"Total arcs processed: {len(arcs)}")
    print("====================\n")
    yield {
        'type': 'summary',
        'revisions': total_revisions,
        'pruned': total_pruned
    }


def complete_to_unique_solution(partial_board, max_attempts=100):

    # al awl  bcheck if the partial board is solvable
    test_board = clone_board(partial_board)
    if not solve_backtracking(test_board):
        return None  # Unsolvable with current clues

    # Get a full solution
    solution = clone_board(test_board)

    # Count how many solutions exist with current clues
    solutions_count = count_solutions(partial_board, limit=2)

    if solutions_count == 1:
        # lw hya Already unique b Return the partial board zy ma hya
        return clone_board(partial_board)

    # b add more clues from the solution to make it unique
    puzzle = clone_board(partial_board)

    # bgeb kol empty positions fe random order
    empty_cells = [(r, c) for r in range(9) for c in range(9)
                   if puzzle[r][c] == 0]
    random.shuffle(empty_cells)

    added_clues = 0

    # Try adding clues one by one le7ad ma yaba unique
    for r, c in empty_cells:
        # Add this clue from the solution
        puzzle[r][c] = solution[r][c]
        added_clues += 1

        # bCheck lw unique now
        if count_solutions(puzzle, limit=2) == 1:
            # Success! We have a unique puzzle
            break

    # bVerify the puzzle is valid and unique
    if count_solutions(puzzle, limit=2) == 1:
        return puzzle
    else:
        # lw lesa msh unique after adding all possible clues,
        # return the solution (fully filled board)
        return solution

