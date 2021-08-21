import simulated_parameter_vault
import simulated_pulse_sequence

#
# Single-ion Rabi flopping
#
simulated_parameter_vault.set_parameter(["IonsOnCamera", "ion_number"], 1)
simulated_parameter_vault.set_parameter(["StateReadout", "readout_mode"], "pmt")

rabi_result = simulated_pulse_sequence.run_simulation(
    "sequences/rabi_flopping.py",
    "RabiFlopping",
    {
        "RabiFlopping-Scan_Selection": "RabiFlopping.duration",
        "RabiFlopping:RabiFlopping.duration": {
            "ty": "RangeScan",
            "start": 0,
            "stop": 100e-6,
            "npoints": 20
        },
    },
)

#
# Two-ion MS gate
#
simulated_parameter_vault.set_parameter(["IonsOnCamera", "ion_number"], 2)
simulated_parameter_vault.set_parameter(["StateReadout", "readout_mode"], "camera_states")

ms_result = simulated_pulse_sequence.run_simulation(
    "sequences/molmer_sorensen.py",
    "MolmerSorensenGate",
    {
        "MolmerSorensen-Scan_Selection": "MolmerSorensen.duration",
        "MolmerSorensen:MolmerSorensen.duration": {
            "ty": "RangeScan",
            "start": 0,
            "stop": 100e-6,
            "npoints": 20
        },
    },
)

#
# Print results
#
print("*** Single-ion Rabi flopping results ***")
print(rabi_result)

print("*** Two-ion MS gate results ***")
print(ms_result)
