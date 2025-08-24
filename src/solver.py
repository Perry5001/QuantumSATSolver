import math

from qiskit import QuantumCircuit , transpile, QuantumRegister, AncillaRegister
from qiskit.circuit.library import GroverOperator, MCMT, ZGate, PhaseOracle
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_distribution, plot_histogram

#from qiskit_aer import Aer

#from qiskit_ibm_runtime import QiskitRuntimeService
#from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit.primitives import StatevectorSampler as Sampler

def quantCirc(qubits, ancillas):
    reg = QuantumRegister(qubits)
    qc = QuantumCircuit(reg)
    anc = AncillaRegister(ancillas)
    qc.add_register(anc)
    return qc

def andGate(numInputs: int):
    qc = QuantumCircuit(numInputs + 1)
    qc.mcx(list(range(numInputs)), numInputs)
    return qc

def orGate(numInputs: int):
    qc = QuantumCircuit(numInputs + 1)
    qc.x(range(numInputs))
    qc.mcx(list(range(numInputs)), numInputs)
    qc.x(range(numInputs))
    qc.x(numInputs)
    return qc

def orGateInv(numInputs: int):
    qc = QuantumCircuit(numInputs + 1)
    qc.x(numInputs)
    qc.x(range(numInputs))
    qc.mcx(list(range(numInputs)), numInputs)
    qc.x(range(numInputs))
    return qc

def notGate():
    qc = QuantumCircuit(1)
    qc.x(0)
    return qc

def phaseKickback(gate):
    qc = QuantumCircuit(gate.num_qubits)
    qc.x(gate.num_qubits-1)
    qc.h(gate.num_qubits-1)
    qc.compose(gate,range(gate.num_qubits), inplace=True)
    qc.h(gate.num_qubits-1)
    qc.x(gate.num_qubits-1)
    return qc

def diffusion(n):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    qc.x(range(n))
    qc.h(n-1)
    qc.mcx(list(range(n-1)),n-1)
    qc.h(n-1)
    qc.x(range(n))
    qc.h(range(n))
    return qc

class CNF:
    def __init__(self, clauses: list):
        self.numClauses = len(clauses)
        self.numVars = max(abs(var) for clause in clauses for var in clause)
        self.clauses = clauses
        self.qc: QuantumCircuit = None

    def append(self, clause: list):
        self.numClauses += 1
        self.clauses.append(clause)

    def test(self, assigments: list):
        """Tests a given assignment of Booleans on the CNF statement"""
        if len(assigments) != self.numVars:
            raise ValueError("Number of variables do not match")

        cnf_satisfied = True
        clause_num = 0
        while cnf_satisfied and clause_num < len(self.clauses):
            clause_satisfied = False
            clause = self.clauses[clause_num]
            var_num = 0
            print(f'Clause: {clause_num}')
            while not clause_satisfied and var_num < len(clause):
                var = clause[var_num]
                if var > 0 and assigments[abs(var)-1]:
                    clause_satisfied = True
                elif var < 0 and not assigments[abs(var)-1]:
                    clause_satisfied = True
                var_num += 1
            if not clause_satisfied:
                cnf_satisfied = False
            clause_num += 1
        return cnf_satisfied


    # Static method to parse a CNF string from DIMACS format
    @staticmethod
    def parse(cnfString: str):
        lines = cnfString.strip().split('\n',1)
        header = lines[0].split()
        numVars = int(header[2])
        numClauses = int(header[3])
        clauses = []
        clauseStrings = lines[1].strip().split("0")
        for clauseString in clauseStrings:
            if clauseString == '':
                continue
            clause = list(map(int, clauseString.split()))
            clauses.append(clause)
        print(len(clauses))
        cnf = CNF(clauses)
        return cnf
    
    def print(self):
        print(f"Number of Variables: {self.numVars}")
        print(f"Number of Clauses: {self.numClauses}")
        print("Clauses:")
        for clause in self.clauses:
            print(clause)

    def quantAlgo(self):
        qc = quantCirc(self.numVars+ self.numClauses+1,0)
        ancillaBit = self.numVars
        for clause in self.clauses:
            qc.barrier()
            for bit in clause:
                if bit > 0:
                    qc.x(abs(bit)-1)
            # Ensure unique qubit indices for each clause
            clause_qubits = list(set([abs(x)-1 for x in clause]))
            qc.compose(andGate(len(clause_qubits)), clause_qubits + [ancillaBit], inplace=True)
            qc.x(ancillaBit)
            for bit in clause:
                if bit > 0:
                    qc.x(abs(bit)-1)
            ancillaBit += 1
        qc.barrier()
        qc.compose(phaseKickback(andGate(self.numClauses)), [x+self.numVars for x in range(self.numClauses+1)], inplace=True)
        qc.barrier()
        ancillaBit -= 1
        for i in range(len(self.clauses)-1, -1, -1):
            clause = self.clauses[i]
            for bit in clause:
                if bit > 0:
                    qc.x(abs(bit)-1)
            qc.x(ancillaBit)
            clause_qubits = list(set([abs(x)-1 for x in clause]))
            qc.compose(andGate(len(clause_qubits)), clause_qubits + [ancillaBit], inplace=True)
            for bit in clause:
                if bit > 0:
                    qc.x(abs(bit)-1)
            qc.barrier()
            ancillaBit -= 1

        qc.compose(diffusion(self.numVars), range(self.numVars), inplace=True)
        self.qc = qc

class SATSolver:
    def __init__(self, cnf: CNF, num_of_solutions=1):
        self.cnf = cnf
        self.num_of_iterations = math.floor((math.pi / 4) * math.sqrt(math.pow(2, self.cnf.numVars)/num_of_solutions))
        self.qc = None
        self.make_qc()
        self.dist = None

    def sample(self, shots=1):
        """Makes the quantum circuit if not already made, runs it for # of shots, and returns the distribution."""
        if self.qc == None:
            self.make_qc()
        print("Running quantum circuit...")
        sampler = Sampler()
        result = sampler.run([self.qc],shots=shots).result()
        dist = result[0].data.c.get_counts()
        self.dist = dist
        print("Quantum circuit run complete.")
        return dist
    
    def make_qc(self):
        print("Making quantum circuit...")
        self.cnf.quantAlgo()
        qc = QuantumCircuit(self.cnf.qc.num_qubits,self.cnf.numVars)
        qc.h(range(self.cnf.numVars))
        qc.compose(self.cnf.qc.power(self.num_of_iterations), inplace=True)
        qc.measure(range(self.cnf.numVars),range(self.cnf.numVars-1, -1, -1))
        print("Quantum circuit made.")
        self.qc = qc
    
    def solve(self):
        total = 0
        tries = 0
        solved = False
        result = None
        breaking = False
        while not solved and not breaking:
            dist = self.sample()
            result = max(dist, key=dist.get)
            print(f'Try: {tries}, Result: {result}')
            bool_vars = [bool(int(x)) for x in result]
            if(self.cnf.test(bool_vars)):
                solved = True
            tries += 1
            total += 1
            if tries > 2:
                self.reduceIteration()
                breaking = True if self.num_of_iterations <= 0 else False
                print(f'Iterations reduced to {self.num_of_iterations}')
                tries = 0
        print(f'Total tries: {total}')
        if solved:
            return result
        else:
            return "No solution found"
    
    def reduceIteration(self):
        self.num_of_iterations -= 1
        self.make_qc()
    
    def print(self):
        print(f"Number of Variables: {self.cnf.numVars}")
        print("Clauses:")
        for clause in self.cnf.clauses:
            print(clause)
        print(f"Number of Iterations: {self.num_of_iterations}")
        if self.dist:
            print("Distribution:", self.dist)
        else:
            print("No distribution available. Run the solve method first.")