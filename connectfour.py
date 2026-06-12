import math
import time

# ============================== Connect4 Board ==============================
class Connect4Board1D:
    def __init__(self, width=7, height=6):
        self.width = width
        self.height = height
        self.board = [0] * (width * height)    # 0 = empty, 1 = AI, -1 = Human
        self.heights = [0] * width   # discs in each column
        self.current_player = 1  # 1 = AI, -1 = Human

    def get_index(self, row, col):
        #Convert (row, col) le index in the 1D board list
        return row * self.width + col

    def generate_moves(self):
        #bagyb list mn el columns elly msh full
        return [c for c in range(self.width) if self.heights[c] < self.height]

    def make_move(self, col):

               #put disc in the specified column.
               #Return True law move  successful, False law colum full.

        if self.heights[col] >= self.height:
            return False
        row = self.height - 1 - self.heights[col]
        idx = self.get_index(row, col)
        self.board[idx] = self.current_player
        self.heights[col] += 1
        self.current_player *= -1
        return True

    def undo_move(self, col):
       #bashyl disk mn column
        if self.heights[col] == 0:
            return False
        self.current_player *= -1
        row = self.height - self.heights[col]
        idx = self.get_index(row, col)
        self.board[idx] = 0
        self.heights[col] -= 1
        return True

    def is_full(self):
        #Check law  board mlyan
        return all(h == self.height for h in self.heights)

    def count_fours(self, player):
        count = 0
        W = self.width
        H = self.height
        B = self.board

        # Horizontal
        for r in range(H):
            for c in range(W - 3):
                if (B[self.get_index(r, c)] == player and
                        B[self.get_index(r, c + 1)] == player and
                        B[self.get_index(r, c + 2)] == player and
                        B[self.get_index(r, c + 3)] == player):
                    count += 1

        # Vertical
        for r in range(H - 3):
            for c in range(W):
                if (B[self.get_index(r, c)] == player and
                        B[self.get_index(r + 1, c)] == player and
                        B[self.get_index(r + 2, c)] == player and
                        B[self.get_index(r + 3, c)] == player):
                    count += 1

        # Diagonal down-right
        for r in range(H - 3):
            for c in range(W - 3):
                if (B[self.get_index(r, c)] == player and
                        B[self.get_index(r + 1, c + 1)] == player and
                        B[self.get_index(r + 2, c + 2)] == player and
                        B[self.get_index(r + 3, c + 3)] == player):
                    count += 1

        # Diagonal up-right
        for r in range(3, H):
            for c in range(W - 3):
                if (B[self.get_index(r, c)] == player and
                        B[self.get_index(r - 1, c + 1)] == player and
                        B[self.get_index(r - 2, c + 2)] == player and
                        B[self.get_index(r - 3, c + 3)] == player):
                    count += 1

        return count

    def check_winner(self):#winner howa elly 3ndo fours aktar
        if not self.is_full():
            return None   #law board msh full , m3nah el game lsa sha8al
        ai = self.count_fours(1)
        hu = self.count_fours(-1)
        if ai > hu:
            return 1
        if hu > ai:
            return -1
        return 0

# ============================== Heuristic ==============================
class Connect4Heuristic:

   #bt assign score lel board from Ai's perspective
   # 3shan a help ai y decide y7ot fen

    def __init__(self):
        # Weights: 4-in-row is extremely valuable, 3-in-row critical, 2-in-row minor, 1-in-row tiny
        # Assign weights to different streaks (more consecutive discs = higher weight)
        self.weights = {4: 100000, 3: 1000, 2: 10, 1: 1}
       #dictionary maps 3dd discs gmb b3d le score mo3yn
    # hy5le al ai y prioritize forming long streaks,
    # bs brdo hy consider blocking the opponent ( fe evaluation)

    def evaluate(self, board, ai=1, human=-1):
        # ba7seb both sides: AI score minus opponent score
        #Return heuristic score: AI score minus 2x human score 34an yb2a stronger defensive behavior
        return self._score(board, ai) - 2 * self._score(board, human)
        #Why *2
        #ai hyshof human threat as urgent
        #more defensive hy7awl y prevent human from forming threats

    def _score(self, board, player):
        W, H = board.width, board.height     #board dimensions
        B = board.board #al 1d board array
        score = 0  # h3mlo intialize b zero

        #directions : horizontal, vertical, diagonal down-right,diagonal up-right
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        #kol tuple (dr,dc)
        #dr : delta row
        #dc : delta column
        # (0, 1) -> horizontal , (1, 0) -> vertical
        # (1, 1) -> diagonal down-right, (-1, 1)-> diagonal up-right


        #3yzeen ntcheck kol position on the board
        for r in range(H):  #loop through all (r)rows   r:current row (0 to height-1)
            for c in range(W):  #loop through all (c)columns  c:current column (0 to width-1)
                for dr, dc in directions: #b3den hcheck all directions from this cell
                    window = []  #temp list le 4 cells fy line
                    for i in range(4):  #i mn 0 le 3 3shan 3yzen 4 in a line
                        rr, cc = r + dr * i, c + dc * i  #row w column of the current cell fy window
                        if 0 <= rr < H and 0 <= cc < W:  #add cell's value lel window , madam cell gowa al board
                            window.append(B[board.get_index(rr, cc)])
                        else:
                            break   #lw row aw column bara al board , stop
                    if len(window) == 4:  #lw 4 hb3tha le evaluate window
                        score += self._evaluate_window(window, player)
                        #add window score


        center_col = W // 2  #geb column aly fy nos
        center_count = sum(1 for r in range(H) if B[board.get_index(r, center_col)] == player)
        #ha3ed kam disc mawgod fy column aly fy nos beny h3de 3ala rows al column dah
        score += center_count * 6  #  higher 34an prioritize center
        #add small bonus le score kol disc fy center 3shan Discs in the center are better
        # because they can connect in more directions (horizontal, diagonal) than side columns

        return score

    def _evaluate_window(self, window, player):
        # Count how many discs the player has in this window
        #Evaluate a 4-cell window.

        player_count = window.count(player) #how many of player’s discs
        empty_count = window.count(0) #how many empty
        opp_count = len(window) - player_count - empty_count # how many opponent’s discs

        # If window contains only player's discs(ai) or empty spaces
        #+ve score
        if opp_count == 0:
            return self.weights.get(player_count, 0)

        # If window contains only opponent's discs or empty
        # , return negative score , potential threat , ai lazm y block
        elif player_count == 0 and opp_count > 0:
            return -self.weights.get(opp_count, 0) // 2

        #lw mixed window fi player(ai)  w opponent
        #can not be completed , score=0
        else:
            return 0


# ============================== Pure Minimax ==============================
class Connect4Minimax:
    def __init__(self, heuristic, max_depth=4, print_tree=False):
        self.heuristic = heuristic
        self.max_depth = max_depth
        self.print_tree = print_tree
        self.nodes = 0

    def minimax(self, board, depth, maxing, indent=0):

      #maxing=True for AI's turn, False for human's turn

        self.nodes += 1
        pre = "  " * indent

        if board.is_full() or depth == 0:
            score = self.heuristic.evaluate(board, 1, -1)
            if self.print_tree:
                self.print_board_score(board, score, "Leaf Node")
                print(f"{pre}[Leaf] score={score}")
            return score, None

        moves = board.generate_moves()
        best = None

        if maxing: # AI by7awel maximize score
            best_val = -math.inf
            for mv in moves:
                board.make_move(mv)
                val, _ = self.minimax(board, depth - 1, False, indent + 1)
                board.undo_move(mv)
                if self.print_tree:
                    print(f"{pre}AI tried column={mv}, val={val}")
                if val > best_val:
                    best_val = val
                    best = mv
            return best_val, best
        else: # Human  by7awel minimize AI score
            best_val = math.inf
            for mv in moves:
                board.make_move(mv)
                val, _ = self.minimax(board, depth - 1, True, indent + 1)
                board.undo_move(mv)
                if self.print_tree:
                    print(f"{pre}Human tried column={mv}, val={val}")
                if val < best_val:
                    best_val = val
                    best = mv
            return best_val, best

    def get_best_move(self, board):   #Return the column chosen by AI as best move
        self.nodes = 0
        v, m = self.minimax(board, self.max_depth, True)
        print(f"[Minimax] move={m} value={v} nodes={self.nodes}")
        return m

    def print_board_score(self, board, score, player_name=""):
        print(f"--- Board Evaluation ({player_name}) ---")
        for r in range(board.height):
            row = board.board[r * board.width:(r + 1) * board.width]
            print(" ".join(f"{x:2}" for x in row))
        print("Heuristic value:", score)
        print("-" * 30)


# ============================== Expectiminimax ==============================
class Connect4Expectiminimax:
    def __init__(self, heuristic, max_depth=4, print_tree=True):
        self.heuristic = heuristic
        self.max_depth = max_depth
        self.print_tree = print_tree
        self.nodes = 0

    def expectiminimax(self, board, depth, maxing, indent=0):
        self.nodes += 1
        pre = "  " * indent
        #bst5dmha fy printing al tree

        #lw borad full aw lw wslna lel max depth
        if board.is_full() or depth == 0:
            val = self.heuristic.evaluate(board, 1, -1)
            #hst5dm heuristic 3shan assign score
            if self.print_tree:
                self.print_board_score(board, val, "Leaf Node")
                print(f"{pre}[Leaf] {val}")
            return val, None
            #hretrun val w none (no move )

        moves = board.generate_moves()
        #generate all possible moves (get all columns aly mshhh full)

        #ai turn ai tries to maximize score
        if maxing:
            best = -math.inf
            best_mv = None
            if self.print_tree:
                print(f"{pre}[MAX]")
            for mv in moves:  #loop through all possible moves
                if self.print_tree:
                    print(f"{pre}Choose column={mv} (Chance node)")
                ev = self._chance_node(board, mv, depth - 1, indent + 2)
                #call chance node , w h calculate expected value lel move de
                if ev > best:  #lw expected valyue a7dan mn best , update best
                    best = ev
                    best_mv = mv
            return best, best_mv  #return best expected value w column chosen

        else:  #human turn , minimize , human hy7awl yminimize al Ai
            best = math.inf  #worst possible score lel ai
            best_mv = None  #hn7awl nala2e move that gives the smalled value (worst for Ai)
            if self.print_tree:
                print(f"{pre}[MIN]")
            for mv in moves: #h3de 3ala kol cols aly human mmkn ya7ot feha
                board.make_move(mv)  #temp place the disc
                val, _ = self.expectiminimax(board, depth - 1, True, indent + 1)  #recursively call the ai turn
                # ,depth b -1  go one level deeper , maxing true --> a5le ai turn w hy7awl y maximize score
                board.undo_move(mv)  #remove human's disc , h3ml restore lel board before testing next move
                #backtracking y3ne

                #lw human moves gives smaller score for Ai than prev moves , update
                if val < best:
                    best = val
                    best_mv = mv
            return best, best_mv
          #return worst case score lel Ai , lw human la3ab optimally , column human would pick

    # ====================== Chance Node ======================
    def _chance_node(self, board, chosen, depth, indent):
        pre = "  " * indent  #spaces lel printt
        exp = 0 #total expected value lel move de
        #Expected value = sum of (probability * score) for all possible outcomes.


        #gebt bs al board dimensions
        W = board.width
        H = board.height

        # Chosen column
        options = [(0.6, chosen)]

        # Check left neighbor
        if chosen - 1 >= 0 and board.heights[chosen - 1] < H:
            options.append((0.2, chosen - 1))
        # Check right neighbor
        if chosen + 1 < W and board.heights[chosen + 1] < H:
            options.append((0.2, chosen + 1))

        # If only one neighbor is available, redistribute probability to 0.4
        if len(options) == 2:  # only chosen + one neighbor
            options[1] = (0.4, options[1][1])

        # Normalize probabilities , safety step , at2akd sum probabilities b 1
        total_prob = sum(p for p, _ in options)
        options = [(p / total_prob, col) for p, col in options]

        # Compute expected value
        for p, col in options:
            board.make_move(col)  #h3ml mv
            val, _ = self.expectiminimax(board, depth, False, indent + 1) #evaluate board
            # , recursively calling expectiminimax le human turn
            board.undo_move(col)  #backtrack /undo
            exp += p * val #multiply result value fy p , add lel expected value
            if self.print_tree:
                print(f"{pre}Chance move column={col}, prob={p:.2f}, val={val}")
                #show chosen column , probabilty , value
        if self.print_tree:
            print(f"{pre}Expected value={exp:.2f}")

        return exp  #return expected value

    # ====================== Get Best Move ======================
    def get_best_move(self, board):
        self.nodes = 0
        v, m = self.expectiminimax(board, self.max_depth, True)
        print(f"[EXPMAX] move={m} value={v} nodes={self.nodes}")
        return m

    # ====================== Print Board and Score ======================
    def print_board_score(self, board, score, player_name=""):
        print(f"--- Board Evaluation ({player_name}) ---")
        for r in range(board.height):
            row = board.board[r * board.width:(r + 1) * board.width]
            print(" ".join(f"{x:2}" for x in row))
        print("Heuristic value:", score)
        print("-" * 30)

# ============================== AlphaBeta Pruning ==============================
class Connect4AlphaBeta:
    def __init__(self, heuristic, max_depth=4, print_tree=False):
        self.heuristic = heuristic
        self.max_depth = max_depth
        self.nodes_evaluated = 0
        self.print_tree = print_tree

    def alpha_beta_pruning(self, board, depth, alpha, beta, maximizing):
        self.nodes_evaluated += 1

        if board.is_full() or depth == 0:
            score = self.heuristic.evaluate(board, 1, -1)
            if hasattr(self, 'print_tree') and self.print_tree:
                self.print_board_score(board, score, "Leaf Node")
                print(f"[Leaf] score={score}")
            return score, None

        best_move = None
        moves = board.generate_moves()

        if maximizing:
            value = -float('inf')
            for move in moves:
                board.make_move(move)
                children, _ = self.alpha_beta_pruning(board, depth - 1, alpha, beta, False)
                board.undo_move(move)
                if self.print_tree:
                    print(f"AI tried column={move}, val={children}")
                if children > value:
                    value = children
                    best_move = move
                alpha = max(value, alpha)
                if alpha >= beta:
                    if self.print_tree:
                        print(f"Pruned at column={move}, alpha={alpha}, beta={beta}")
                    break
            return value, best_move
        else:
            value = float('inf')
            for move in moves:
                board.make_move(move)
                children, _ = self.alpha_beta_pruning(board, depth - 1, alpha, beta, True)
                board.undo_move(move)
                if self.print_tree:
                    print(f"Human tried column={move}, val={children}")
                if children < value:
                    value = children
                    best_move = move
                beta = min(value, beta)
                if alpha >= beta:
                    if self.print_tree:
                        print(f"Pruned at column={move}, alpha={alpha}, beta={beta}")
                    break
            return value, best_move

    def get_best_move(self, board):
        self.nodes_evaluated = 0
        value, move = self.alpha_beta_pruning(board, self.max_depth, -float("inf"), float("inf"), True)
        print(f"[AlphaBeta] Best Move={move}, Value={value}, Nodes Evaluated={self.nodes_evaluated}")
        return move

    def print_board_score(self, board, score, player_name=""):
        print(f"--- Board Evaluation ({player_name}) ---")
        for r in range(board.height):
            row = board.board[r * board.width:(r + 1) * board.width]
            print(" ".join(f"{x:2}" for x in row))
        print("Heuristic value:", score)
        print("-" * 30)
