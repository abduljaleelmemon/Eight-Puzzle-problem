# Eight Puzzle problem

An agent for an Eight puzzle problem. The goal of an agent is to complete the Eight puzzle in fixed number of moves. 

## Problem Description:

• Available actions are Left, Right, Up, Down, NoOp. \
• The termination criterion is that the agent runs out of moves or the puzzle is completed. \

Environment announces when this criterion is met and stops the execution. \

• The performance of an agent is calculated after the termination criteria is met. The performance measure of an agent is the (# of correctly placed items) / (number of steps used). Note that there will be early termination if puzzle is solved before expiry of maximum number of moves. \
• The environment is deterministic and partially observable. \
• Agent knows the size of puzzle (grid n x n) and the content of the cell they land in, location of the landing cell (coordinates) is not known. \
• The perception is given by the environment and includes, cell coordinates and if the current piece in the cell is rightly placed or not. \
• Starting position of the agent is random and not known beforehand plus puzzle contents are randomized at each start. \
