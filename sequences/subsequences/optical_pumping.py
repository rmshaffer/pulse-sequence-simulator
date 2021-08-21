from artiq.experiment import *
from subsequences.optical_pumping_pulsed import OpticalPumpingPulsed
from subsequences.optical_pumping_continuous import OpticalPumpingContinuous
from subsequences.aux_optical_pumping import AuxOpticalPumping

class OpticalPumping:
    enable_pulsed_optical_pumping="StatePreparation.pulsed_optical_pumping"
    enable_aux="StatePreparation.aux_optical_pumping_enable"

    def add_child_subsequences(pulse_sequence):
        o = OpticalPumping
        o.opp = pulse_sequence.add_subsequence(OpticalPumpingPulsed)
        o.opc = pulse_sequence.add_subsequence(OpticalPumpingContinuous)
        o.aux_opc = pulse_sequence.add_subsequence(AuxOpticalPumping)

    def subsequence(self):
        o = OpticalPumping
        if o.enable_pulsed_optical_pumping:
            o.opp.run(self)
        else:
            o.opc.run(self)
        if o.enable_aux:
            o.aux_opc.run(self)
