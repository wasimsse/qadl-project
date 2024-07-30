import re

class Qubit:
    def __init__(self, name):
        self.name = name

class QuantumGate:
    def __init__(self, name, qubits):
        self.name = name
        self.qubits = qubits

class Measurement:
    def __init__(self, qubit, classical_bit):
        self.qubit = qubit
        self.classical_bit = classical_bit

class QuantumCircuitDef:
    def __init__(self, name):
        self.name = name
        self.qubits = []
        self.gates = []
        self.measurements = []
        self.classical_bits = {}
        self.control_flow = []
        self.error_correction = []
        self.hardware_config = {}
        self.modules = {}
        self.annotations = []

    def add_qubit(self, qubit):
        self.qubits.append(qubit)

    def add_gate(self, gate):
        self.gates.append(gate)

    def add_measurement(self, measurement):
        if measurement.classical_bit not in self.classical_bits:
            self.classical_bits[measurement.classical_bit] = len(self.classical_bits)
        self.measurements.append(measurement)

    def add_control_flow(self, control):
        self.control_flow.append(control)

    def add_error_correction(self, correction):
        self.error_correction.append(correction)

    def add_hardware_config(self, config):
        self.hardware_config.update(config)

    def add_module(self, name, module):
        self.modules[name] = module

    def add_annotation(self, annotation):
        self.annotations.append(annotation)

def parse_qadl(script):
    lines = script.split('\n')
    circuit = None
    line_number = 0
    control_flow_pattern = re.compile(r'if\s*\(.*\)\s*{|\s*while\s*\(.*\)\s*{')
    in_hardware_block = False
    hardware_config = {}

    def parse_block(lines, start_index):
        block_lines = []
        depth = 0
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line.startswith('{'):
                depth += 1
                if depth == 1:
                    continue
            elif line.startswith('}'):
                depth -= 1
                if depth == 0:
                    return block_lines, i
            block_lines.append(line)
        return block_lines, len(lines) - 1

    for i, line in enumerate(lines):
        line_number += 1
        line = line.strip()

        if not line or line.startswith('//') or line.startswith('/*') or line.startswith('@'):
            continue

        if line.startswith('Circuit'):
            parts = line.split()
            if len(parts) != 3 or parts[2] != '{':
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid circuit declaration. Expected 'Circuit <name> {{'")
            circuit = QuantumCircuitDef(parts[1])

        elif line.startswith('qubit') and circuit:
            parts = line.split()
            if len(parts) != 2:
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid qubit declaration. Expected 'qubit <name>'")
            circuit.add_qubit(Qubit(parts[1]))

        elif line.startswith('gate') and circuit:
            parts = line.split()
            if len(parts) < 3:
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid gate declaration. Expected 'gate <name> <qubits...>'")
            gate_name = parts[1]
            qubits = parts[2:]
            circuit.add_gate(QuantumGate(gate_name, qubits))

        elif line.startswith('measure') and circuit:
            parts = line.split()
            if len(parts) != 4 or parts[2] != '->':
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid measurement declaration. Expected 'measure <qubit> -> <classical_bit>'")
            qubit = parts[1]
            classical_bit = parts[3]
            circuit.add_measurement(Measurement(qubit, classical_bit))

        elif control_flow_pattern.match(line) and circuit:
            circuit.add_control_flow(line)

        elif line.startswith('error_correction') and circuit:
            parts = line.split()
            if len(parts) < 2:
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid error correction declaration. Expected 'error_correction <technique> <parameters>'")
            circuit.add_error_correction(line)

        elif line.startswith('hardware') and circuit:
            in_hardware_block = True
            hardware_config = {}
            block_lines, end_index = parse_block(lines, i + 1)
            for hw_line in block_lines:
                hw_parts = hw_line.split()
                if len(hw_parts) < 2:
                    raise SyntaxError(f"Syntax error on line {line_number}: Invalid hardware configuration.")
                if hw_parts[0] == "qubit_connectivity":
                    connectivity = []
                    for conn_line in block_lines:
                        if conn_line.strip() == '}':
                            break
                        connectivity.append(conn_line)
                    hardware_config["qubit_connectivity"] = connectivity
                else:
                    hardware_config[hw_parts[0]] = hw_parts[1:]
            circuit.add_hardware_config(hardware_config)
            in_hardware_block = False
            line_number = end_index

        elif line.startswith('module') and circuit:
            parts = line.split()
            if len(parts) != 3 or parts[2] != '{':
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid module declaration. Expected 'module <name> {{'")
            module_name = parts[1]
            block_lines, end_index = parse_block(lines, i + 1)
            module_script = '\n'.join(block_lines)
            circuit.add_module(module_name, parse_qadl(module_script))
            line_number = end_index

        elif line.startswith('}') and circuit:
            break  # End of circuit

        elif line.startswith('@') and circuit:
            circuit.add_annotation(line)

        else:
            raise SyntaxError(f"Syntax error on line {line_number}: Unrecognized statement.")

    if not circuit:
        raise SyntaxError("No valid circuit found in the script.")
    return circuit
