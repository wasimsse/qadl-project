@startqadl
Circuit ExampleCircuit {
    // Declare qubits
    qubit q0
    qubit q1
    qubit q2

    // Apply gates
    gate Hadamard q0
    gate CNOT q0 q1
    gate Toffoli q0 q1 q2
    gate Swap q1 q2
    gate Phase q2

    // Measure qubits
    measure q0 -> c0
    measure q1 -> c1
    measure q2 -> c2

    // Control flow
    if (c0 == 1) {
        gate X q1
    }
    while (c1 == 0) {
        gate H q2
    }

    // Error correction
    error_correction Shor q0 q1 q2

    // Hardware configuration
    hardware {
        qubit_connectivity {
            q0 - q1
            q1 - q2
        }
        decoherence_rate q0 0.01
        decoherence_rate q1 0.02
    }

    // Modular circuit definitions
    module SubModule {
        qubit q3
        gate Hadamard q3
        measure q3 -> c3
    }

    // Annotations and metadata
    @annotation Created by User
    @annotation Date: 2024-07-25
}
@endqadl
