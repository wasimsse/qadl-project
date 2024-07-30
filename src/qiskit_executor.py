from qiskit import QuantumCircuit
from qiskit.visualization import circuit_drawer
from qiskit.circuit.library import CRZGate
import numpy as np

def apply_inverse_qft(qc, qubits):
    """Apply the inverse Quantum Fourier Transform."""
    n = len(qubits)
    for qubit in range(n // 2):
        qc.swap(qubits[qubit], qubits[n - qubit - 1])
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / float(2 ** (j - m)), qubits[j], qubits[m])
        qc.h(qubits[j])

def execute_circuit(circuit_def):
    num_qubits = len(circuit_def.qubits)
    num_classical_bits = len(circuit_def.classical_bits)
    qc = QuantumCircuit(num_qubits, num_classical_bits)

    qubit_index = {qubit.name: idx for idx, qubit in enumerate(circuit_def.qubits)}
    classical_bit_index = circuit_def.classical_bits

    for gate in circuit_def.gates:
        if gate.name == 'Hadamard' or gate.name == 'H':
            qc.h(qubit_index[gate.qubits[0]])
        elif gate.name == 'CNOT':
            qc.cx(qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]])
        elif gate.name == 'CZ':
            qc.cz(qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]])
        elif gate.name == 'X':
            qc.x(qubit_index[gate.qubits[0]])
        elif gate.name == 'CR':
            qc.append(CRZGate(0.5), [qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]]])
        elif gate.name == 'CR2':
            qc.append(CRZGate(1.0), [qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]]])
        elif gate.name == 'InverseQFT':
            apply_inverse_qft(qc, [qubit_index[q] for q in gate.qubits])
        elif gate.name == 'CCNOT' or gate.name == 'Toffoli':
            qc.ccx(qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]], qubit_index[gate.qubits[2]])
        elif gate.name == 'Phase':
            qc.p(np.pi / 2, qubit_index[gate.qubits[0]])  # Example phase
        elif gate.name == 'Z':
            qc.z(qubit_index[gate.qubits[0]])
        elif gate.name == 'Oracle':
            pass
        elif gate.name == 'Diffuser':
            pass
        else:
            raise ValueError(f"Unsupported gate: {gate.name}")

    for measurement in circuit_def.measurements:
        qc.measure(qubit_index[measurement.qubit], classical_bit_index[measurement.classical_bit])

    # Handle the conditional operations manually
    if circuit_def.name == "QuantumTeleportation":
        with qc.if_test((classical_bit_index['c0'], 1)):
            qc.z(qubit_index['q2'])
        with qc.if_test((classical_bit_index['c1'], 1)):
            qc.x(qubit_index['q2'])

    qc.draw(output='mpl', filename='quantum_circuit.png')
    return circuit_def.name
