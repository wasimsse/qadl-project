import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
from qiskit import QuantumCircuit
from qiskit.visualization import circuit_drawer
from qiskit.circuit.library import CRZGate
import numpy as np
import os

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

    def add_qubit(self, qubit):
        self.qubits.append(qubit)

    def add_gate(self, gate):
        self.gates.append(gate)

    def add_measurement(self, measurement):
        if measurement.classical_bit not in self.classical_bits:
            self.classical_bits[measurement.classical_bit] = len(self.classical_bits)
        self.measurements.append(measurement)

def parse_qadl(script):
    lines = script.split('\n')
    circuit = None
    line_number = 0

    for line in lines:
        line_number += 1
        line = line.strip()

        if not line or line.startswith('//') or line.startswith('/*') or line.startswith('@'):
            continue

        if line.startswith('Circuit'):
            parts = line.split()
            if len(parts) != 3 or parts[2] != '{':
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid circuit declaration. Expected 'Circuit <name> {{'.")
            circuit = QuantumCircuitDef(parts[1])

        elif line.startswith('qubit') and circuit:
            parts = line.split()
            if len(parts) != 2:
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid qubit declaration. Expected 'qubit <name>'.")
            circuit.add_qubit(Qubit(parts[1]))

        elif line.startswith('gate') and circuit:
            parts = line.split()
            if len(parts) < 3:
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid gate declaration. Expected 'gate <name> <qubits...>'.")
            gate_name = parts[1]
            qubits = parts[2:]
            circuit.add_gate(QuantumGate(gate_name, qubits))

        elif line.startswith('measure') and circuit:
            parts = line.split()
            if len(parts) != 4 or parts[2] != '->':
                raise SyntaxError(f"Syntax error on line {line_number}: Invalid measurement declaration. Expected 'measure <qubit> -> <classical_bit>'.")
            qubit = parts[1]
            classical_bit = parts[3]
            circuit.add_measurement(Measurement(qubit, classical_bit))

        elif line.startswith('}'):
            break  # End of circuit

        else:
            raise SyntaxError(f"Syntax error on line {line_number}: Unrecognized statement.")

    if not circuit:
        raise SyntaxError("No valid circuit found in the script.")
    return circuit

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
        if gate.name == 'Hadamard':
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
        elif gate.name == 'CCNOT':
            qc.ccx(qubit_index[gate.qubits[0]], qubit_index[gate.qubits[1]], qubit_index[gate.qubits[2]])
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

class QADLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QADL GUI with Qiskit")
        self.filename = None
        self.create_widgets()

    def create_widgets(self):
        self.create_menu()
        self.create_toolbar()
        self.create_text_editor()
        self.create_output_display()
        self.create_status_bar()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit Menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Clear", command=self.clear_text)
        edit_menu.add_command(label="Cut", command=lambda: self.script_input.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", command=lambda: self.script_input.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", command=lambda: self.script_input.event_generate("<<Paste>>"))
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help Contents", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        new_icon = self.load_icon("new_file.png")
        open_icon = self.load_icon("open_file.png")
        save_icon = self.load_icon("save_file.png")
        run_icon = self.load_icon("run.png")
        clear_icon = self.load_icon("clear.png")
        screenshot_icon = self.load_icon("screenshot.png")

        tk.Button(toolbar, image=new_icon, command=self.new_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, image=open_icon, command=self.open_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, image=save_icon, command=self.save_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, image=run_icon, command=self.run_qadl).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, image=clear_icon, command=self.clear_text).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, image=screenshot_icon, command=self.take_screenshot).pack(side=tk.LEFT, padx=2, pady=2)

        toolbar.images = [new_icon, open_icon, save_icon, run_icon, clear_icon, screenshot_icon]
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def load_icon(self, filename):
        try:
            filepath = os.path.join("icons", filename)
            image = Image.open(filepath)
            image = image.resize((32, 32), Image.LANCZOS)  # Resize to appropriate size for toolbar
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Icon load error: {e}")
            return tk.PhotoImage(width=32, height=32)

    def create_text_editor(self):
        self.text_editor_frame = tk.Frame(self.root)
        self.text_editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.script_input = scrolledtext.ScrolledText(self.text_editor_frame, height=30, width=40)
        self.script_input.pack(expand=True, fill=tk.BOTH)

    def create_output_display(self):
        self.output_display_frame = tk.Frame(self.root)
        self.output_display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_display = tk.Label(self.output_display_frame)
        self.output_display.pack(expand=True, fill=tk.BOTH)

    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        self.status_bar.config(text=message)

    def clear_text(self):
        self.script_input.delete('1.0', tk.END)
        self.update_status("Cleared")

    def new_file(self):
        self.script_input.delete('1.0', tk.END)
        self.filename = None
        self.update_status("New File")

    def open_file(self):
        self.filename = filedialog.askopenfilename(defaultextension=".qadl", filetypes=[("QADL Files", "*.qadl"), ("All Files", "*.*")])
        if self.filename:
            with open(self.filename, "r") as file:
                self.script_input.delete('1.0', tk.END)
                self.script_input.insert(tk.END, file.read())
            self.update_status(f"Opened {os.path.basename(self.filename)}")

    def save_file(self):
        if self.filename:
            with open(self.filename, "w") as file:
                file.write(self.script_input.get("1.0", tk.END))
            self.update_status(f"Saved {os.path.basename(self.filename)}")
        else:
            self.save_file_as()

    def save_file_as(self):
        self.filename = filedialog.asksaveasfilename(defaultextension=".qadl", filetypes=[("QADL Files", "*.qadl"), ("All Files", "*.*")])
        if self.filename:
            with open(self.filename, "w") as file:
                file.write(self.script_input.get("1.0", tk.END))
            self.update_status(f"Saved As {os.path.basename(self.filename)}")

    def run_qadl(self):
        script = self.script_input.get("1.0", tk.END)
        try:
            circuit_def = parse_qadl(script)
            circuit_name = execute_circuit(circuit_def)
            
            if os.path.exists("quantum_circuit.png"):
                img = Image.open("quantum_circuit.png")
                img = img.resize((600, 400), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                self.output_display.config(image=img)
                self.output_display.image = img
                self.update_status(f"Executed {circuit_name}")
        except SyntaxError as se:
            self.update_status(f"Syntax Error: {se}")
        except Exception as e:
            self.update_status(f"Error: {e}")

    def take_screenshot(self):
        screenshot_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if screenshot_path:
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            self.update_status(f"Screenshot saved as {screenshot_path}")

    def show_about(self):
        messagebox.showinfo("About", "QADL Editor with Qiskit Integration\nDesigned for Quantum Circuit Visualization")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("QADL Help and Demo")
        help_text = scrolledtext.ScrolledText(help_window, height=30, width=100)
        help_text.pack(expand=True, fill=tk.BOTH)

        try:
            with open("QADL_Help_Demo.qadl", "r") as help_file:
                help_text.insert(tk.END, help_file.read())
        except Exception as e:
            help_text.insert(tk.END, f"Error loading help file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QADLApp(root)
    root.mainloop()
