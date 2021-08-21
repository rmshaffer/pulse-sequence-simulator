parameter_vault = {
    "DopplerCooling": {
        "doppler_cooling_duration": 0e-6,
        "doppler_cooling_repump_additional": 0e-6,
        "pre_duration": 0e-6,
        "doppler_cooling_frequency_397": 80e6,
        "doppler_cooling_amplitude_397": 0.0,
        "doppler_cooling_att_397": 0.0,
        "doppler_cooling_frequency_866": 40e6,
        "doppler_cooling_amplitude_866": 0.0,
        "doppler_cooling_att_866": 0.0,
    },
    "DriftTracker": {
        "current_b_field": 4.0,
        "current_line_center": 0.0,
    },
    "Excitation_729": {
        "rabi_excitation_frequency": 0e3,
        "rabi_excitation_amplitude": 1.0,
        "rabi_excitation_att": 0.0,
        "rabi_excitation_phase": 0.0,
        "channel_729": "729G",
        "rabi_excitation_duration": 0e-6,
        "line_selection": "S-1/2D-1/2",
        "single_pass_amplitude": 1.0,
        "single_pass_att": 0.0,
    },
    "IonsOnCamera": {
        "ion_number": 1,
    },
    "OpticalPumping": {
        "amplitude_729": 1.0,
        "att_729": 0.0,
        "optical_pumping_frequency_854": 30e6,
        "optical_pumping_amplitude_854": 1.0,
        "optical_pumping_att_854": 0.0,
        "line_selection": "S-1/2D+3/2",        
    },
    "OpticalPumpingContinuous": {
        "optical_pumping_continuous_duration": 100e-6,
        "optical_pumping_continuous_repump_additional": 0e-6,
    },
    "RabiFlopping": {
        "line_selection": "S-1/2D-1/2",
        "amplitude_729": 1.0,
        "att_729": 0.0,
        "channel_729": "729G",
        "duration": 5e-6,
        "selection_sideband": "axial_frequency",
        "order": 0,
        "detuning": 0.0,
        "composite_pi_rotation": False,
        "noise": False,
    },
    "SidebandCooling": {
        "line_selection": "S-1/2D-5/2",
        "selection_sideband": "axial_frequency",
        "order": 1,
        "stark_shift": 0e3,
        "channel_729": "729G",
        "amplitude_729": 1.0,
        "att_729": 0.0,
        "duration": 100e-6,
        "frequency_866": 40e6,
        "amplitude_866": 1.0,
        "att_866": 0.0,
        "frequency_854": 20e6,
        "amplitude_854": 1.0,
        "att_854": 0.0,
        "sideband_cooling_cycles": 1,
    },
    "SequentialSBCooling": {
        "enable": False,
        "channel_729": "729G",
        "selection_sideband": "axial_frequency",
        "order": 1,
    },
    "SequentialSBCooling1": {
        "enable": False,
        "channel_729": "729G",
        "selection_sideband": "axial_frequency",
        "order": 1,
    },
    "SequentialSBCooling2": {
        "enable": False,
        "channel_729": "729G",
        "selection_sideband": "axial_frequency",
        "order": 1,
    },
    "StatePreparation": {
        "optical_pumping_enable": False,
        "aux_optical_pumping_enable": False,
        "pulsed_optical_pumping": False,
        "sideband_cooling_enable": False,
        "post_delay": 0e-6,
        "number_of_cycles": 1,
        "pulsed_854_duration": 100e-6,
        "pi_time": 10e-6,
        "channel_729": "729G",
        "pulsed_amplitude": 1.0,
        "pulsed_att": 0.0,
    },
    "StateReadout": {
        "readout_mode": "camera",
        "repeat_each_measurement": 100,
    },
    "TrapFrequencies": {
        "axial_frequency": 1e6,
        "radial_frequency_1": 2e6,
        "radial_frequency_2": 2.4e6,
    },
}

def get_collections():
    return parameter_vault.keys()

def get_parameter_names(collection):
    return parameter_vault[collection].keys()

def get_parameter(path):
    collection = path[0]
    name = path[1]
    return parameter_vault[collection][name]

def set_parameter(path, value):
    collection = path[0]
    name = path[1]
    parameter_vault[collection][name] = value
