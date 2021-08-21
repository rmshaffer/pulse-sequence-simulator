from pulse_sequence import PulseSequence
from subsequences.rabi_excitation import RabiExcitation
from subsequences.state_preparation import StatePreparation
from artiq.experiment import *


class Spectrum(PulseSequence):
    PulseSequence.accessed_params = {
        "Excitation_729.rabi_excitation_frequency",
        "Excitation_729.rabi_excitation_amplitude",
        "Excitation_729.rabi_excitation_att",
        "Excitation_729.rabi_excitation_phase",
        "Excitation_729.channel_729",
        "Excitation_729.rabi_excitation_duration",
        "Excitation_729.line_selection",
    }
    PulseSequence.scan_params.update(
        spectrum=[
            ("Spectrum", ("Spectrum.carrier_detuning", -150*kHz, 150*kHz, 100, "kHz"))
        ])

    def run_initially(self):
        self.stateprep = self.add_subsequence(StatePreparation)
        self.rabi = self.add_subsequence(RabiExcitation)
        self.set_subsequence["spectrum"] = self.set_subsequence_spectrum

    @kernel
    def set_subsequence_spectrum(self):
        delta = self.get_variable_parameter("Spectrum_carrier_detuning")
        rabi_line = self.rabi.line_selection
        rabi_dds = self.rabi.channel_729
        self.rabi.freq_729 = self.calc_frequency(rabi_line, delta, dds=rabi_dds,
                bound_param="Spectrum_carrier_detuning")
    ###
    @kernel
    def spectrum(self):
        self.stateprep.run(self)
        self.rabi.run(self)