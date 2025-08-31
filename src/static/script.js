const input = document.getElementById('input');
const output = document.getElementById('cnf-output');
const solveBtn = document.getElementById('solve-btn');
const randomBtn = document.getElementById('random-btn');
const solutionOutput = document.getElementById('solution');

const API_BASE = window.location.hostname.includes("127.0.0.1")
  ? "http://localhost:5000"
  : "https://quantumsatsolver.onrender.com";


function renderCNF() {
    const lines = input.value.trim().split('\n').filter(l => l.trim());
    const clauses = lines.map(line => {
    const vars = line.trim().split(/\s+/).map(Number);
    return '(' + vars.map(v => v > 0 ? `x${v}` : `¬x${Math.abs(v)}`).join(' ∨ ') + ')';
    });
    const statement = clauses.length ? clauses.join(' ∧ ') : '';
    if(statement.includes('NaN')) {
        output.innerHTML = 'Invalid input detected. Please ensure all entries are integers.';
        return;
    }
    output.innerHTML = statement ? statement : '';
}

function getDIMACS() {
    const lines = input.value.trim().split('\n').filter(l => l.trim());
    const clauses = lines.map(line => line.trim() + ' 0');
    const numVars = Math.max(...lines.flatMap(l => l.split(/\s+/).map(Number).map(Math.abs)));
    const dimacs = `p cnf ${numVars} ${clauses.length}\n` + clauses.join('\n');
    console.log(dimacs);
    return dimacs;
}

function solve() {
    const dimacs = getDIMACS();
    solutionWaiting();
    getSolution(dimacs);
}

function randomCnf(){
    console.log("Fetching random CNF...");
    getRandom("random");
}

function solutionWaiting(){
    solutionOutput.innerHTML = "Solving...";
}

function solutionError(error){
    solutionOutput.innerHTML = "Error: Unable to solve the problem.";
    console.error('Error fetching solution:', error);
}

function populateSolution(solution) {
    solutionOutput.innerHTML = solution ? "Solution: " + solution : 'X';
}

function populateRandom(cnf) {
    input.value = cnf;
    renderCNF();
}

loadBackend("Frontend loaded");
solveBtn.addEventListener('click', solve);
randomBtn.addEventListener('click', randomCnf);
input.addEventListener('input', renderCNF);
renderCNF();

// Example function to call your Python endpoint
function getSolution(arg) {
    fetch(`${API_BASE}/call-solution`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ arg: arg})
    })
    .then(response => response.json())
    .then(data => {
        populateSolution(data.message);
    })
    .catch(error => {solutionError(error);});
}

function getRandom(arg){
    fetch(`${API_BASE}/call-random`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ arg: arg})
    })
    .then(response => response.json())
    .then(data => {
        populateRandom(data.message);
    })
    .catch(error => {"Error fetching random CNF:", console.error(error);});
}

function loadBackend(arg) {
    fetch(`${API_BASE}/hello`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ arg: arg})
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
    })
    .catch(error => {console.error('Error connecting to backend:', error);});
}