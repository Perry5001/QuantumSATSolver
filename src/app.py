from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time

from solver import CNF, SATSolver

app = Flask(__name__, static_folder='static')
CORS(app)  # Allow requests from JS (like http://localhost:5500)

@app.route('/')
def serve_index():
  return send_from_directory('.', 'index.html')

def find_solution(dimacs):
    cnf = CNF.parse(dimacs)
    startTime = time.time()
    solver = SATSolver(cnf)
    solution = solver.solve()
    endTime = time.time()
    print(f'Solution found in {endTime - startTime} seconds')
    return solution

@app.route('/call-solution', methods=['POST'])
def call_files():
    data = request.json
    arg = data.get('arg', '')
    result = find_solution(arg)
    return jsonify({"message": result})

if __name__ == '__main__':
    app.run(port=5000)