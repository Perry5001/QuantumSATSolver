# Quantum SAT Solver
This project finds solutions to Boolean satisfiability problems by creating quantum circuits to utilize Grover's algorithm. It will simulate running this circuit on a classical computer through Qiskit, but can be modified to work with IBM quantum computers. I also authored a paper that outlines how each circuit is created and how it is able to find the solution.

The project website has a limited memory space.

Link to Project: https://quantumsatsolver.onrender.com/

Link to Paper:

## How To Use:
1. Create a `CNF` object
    a. Initialize it with a 2D array with each row representing a clause and each value as a number representation of the variable (one-indexed)
    b. Or parse a CNF statement in DIMACS format using `CNF.parse()`
2. Create a `SATSolver` object
    a. Initialize it with the CNF object and the number of solutions-default is 1.
3. Run the `solve()` method to get a satisfiable solution.
4. Or run the `sample()` method to get a distribution of outputs for given `shots`

