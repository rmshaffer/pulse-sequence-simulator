from pulse_sequence import PulseSequence
from subsequences.rabi_excitation import RabiExcitation
from subsequences.rabi_excitation2 import RabiExcitation2 #fix later
from subsequences.composite_pi import CompositePi #added for composite_pi 02/20/2020
from subsequences.state_preparation import StatePreparation
from subsequences.bichro_excitation import BichroExcitation
from subsequences.szx import SZX
import numpy as np
from artiq.experiment import *
#from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING, PHASE_MODE_ABSOLUTE

class MolmerSorensenGate(PulseSequence):
    PulseSequence.accessed_params = {
        "MolmerSorensen.duration",
        "MolmerSorensen.line_selection",
        "MolmerSorensen.line_selection_ion2",
        "MolmerSorensen.due_carrier_enable",
        "MolmerSorensen.selection_sideband",
        "MolmerSorensen.detuning",
        "MolmerSorensen.detuning_carrier_1",
        "MolmerSorensen.detuning_carrier_2",
        "MolmerSorensen.amp_red",
        "MolmerSorensen.att_red",
        "MolmerSorensen.amp_blue",
        "MolmerSorensen.amp_blue_noise_std",
        "MolmerSorensen.att_blue",
        "MolmerSorensen.amplitude",
        "MolmerSorensen.att",
        "MolmerSorensen.amplitude_ion2",
        "MolmerSorensen.att_ion2",
        "MolmerSorensen.analysis_pulse_enable",
        "MolmerSorensen.SDDS_enable",
        "MolmerSorensen.SDDS_rotate_out",
        "MolmerSorensen.rotate_in_with_global",
        "MolmerSorensen.shape_profile",
        "MolmerSorensen.bichro_enable",
        "MolmerSorensen.analysis_duration",
        "MolmerSorensen.analysis_amplitude",
        "MolmerSorensen.analysis_att",
        "MolmerSorensen.analysis_amplitude_ion2",
        "MolmerSorensen.analysis_att_ion2",
        "MolmerSorensen.channel_729",
        "MolmerSorensen.ramsey_duration",
        "MolmerSorensen.override_readout",
        "MolmerSorensen.ms_phase",
        "MolmerSorensen.sp_line1_amp",
        "MolmerSorensen.sp_line2_amp",
        "MolmerSorensen.sp_line1_att",
        "MolmerSorensen.sp_line2_att",
        "MolmerSorensen.sp_line1_blue_amp",
        "MolmerSorensen.sp_line2_blue_amp",
        "MolmerSorensen.sp_line1_blue_att",
        "MolmerSorensen.sp_line2_blue_att",
        "MolmerSorensen.sp_line1_red_amp",
        "MolmerSorensen.sp_line2_red_amp",
        "MolmerSorensen.sp_line1_red_att",
        "MolmerSorensen.sp_line2_red_att",
        "MolmerSorensen.sp_due_enable",
        "Rotation729L1.amplitude",
        "Rotation729L1.att",
        "Rotation729L1.pi_time",
        "Rotation729L1.composite_pi_rotation", #added for composite_pi 02/20/2020
        "Rotation729G.amplitude",
        "Rotation729G.att",
        "Rotation729G.pi_time",
        "Rotation729G.line_selection",
        "StatePreparation.aux_optical_pumping_enable",
        "LocalSpec.enable",
        "LocalSpec.detuning",
        "LocalSpec.att",
        "LocalSpec.amp",
        # "LocalSpec.duration",
        "LocalSpec.line_selection",
        "MolmerSorensen.ac_stark_shift"
    }

    PulseSequence.scan_params.update(
        MolmerSorensen=[
            ("Molmer-Sorensen", ("MolmerSorensen.duration", 0., 400*us, 20, "us")),
            ("Molmer-Sorensen", ("MolmerSorensen.amplitude", 0., 1., 20)),
            ("Molmer-Sorensen", ("MolmerSorensen.amplitude_ion2", 0., 1., 20)),
            ("Molmer-Sorensen", ("MolmerSorensen.detuning_carrier_1", -10*kHz, 10*kHz, 20, "kHz")),
            ("Molmer-Sorensen", ("MolmerSorensen.detuning_carrier_2", -10*kHz, 10*kHz, 20, "kHz")),
            ("Molmer-Sorensen", ("MolmerSorensen.ramsey_duration", 0., 2*ms, 40, "ms")),
            ("Molmer-Sorensen", ("MolmerSorensen.ms_phase", 0., 360., 20, "deg")),
            ("Molmer-Sorensen", ("LocalSpec.detuning", -10*kHz, 10*kHz, 20, "kHz")),
            ("Molmer-Sorensen", ("MolmerSorensen.ac_stark_shift", -10*kHz, 10*kHz, 20, "kHz")),
        ]
    )

    def run_initially(self):
        self.stateprep = self.add_subsequence(StatePreparation)
        self.ms = self.add_subsequence(BichroExcitation)
        self.rabi = self.add_subsequence(RabiExcitation)
        self.rotate_in = self.add_subsequence(RabiExcitation2)
        self.composite = self.add_subsequence(CompositePi)
        self.rabi.channel_729 = "729G"
        self.rotate_in.channel_729 = "729L1" if not self.p.MolmerSorensen.rotate_in_with_global else "729G"
        self.phase_ref_time = np.int64(0)
        self.szx = self.add_subsequence(SZX)
        self.set_subsequence["MolmerSorensen"] = self.set_subsequence_ms
        if self.p.MolmerSorensen.bichro_enable:
            self.ms.setup_noisy_single_pass(self, freq_noise=False)
        if not self.p.MolmerSorensen.override_readout:
            ss = self.selected_scan["MolmerSorensen"]
            if self.p.MolmerSorensen.bichro_enable:
                if ss == "MolmerSorensen.ms_phase" or ss == "MolmerSorensen.ramsey_duration":
                    self.p.StateReadout.readout_mode = "camera_parity"
                else:
                    self.p.StateReadout.readout_mode = "camera_states"
            else:
                self.p.StateReadout.readout_mode = "camera"
            if ss == "LocalSpec.detuning":
                self.p.StateReadout.readout_mode = "camera"

    @kernel
    def set_subsequence_ms(self):
        self.ms.duration = self.get_variable_parameter("MolmerSorensen_duration")
        self.ms.amp = self.get_variable_parameter("MolmerSorensen_amplitude")
        self.ms.amp_ion2 = self.get_variable_parameter("MolmerSorensen_amplitude_ion2")
        self.ms.detuning_carrier_1 = self.get_variable_parameter("MolmerSorensen_detuning_carrier_1")
        self.ms.detuning_carrier_2 = self.get_variable_parameter("MolmerSorensen_detuning_carrier_2")
        self.ms.ac_stark_shift = self.get_variable_parameter("MolmerSorensen_ac_stark_shift")
        if self.LocalSpec_enable:
            self.ms.local_spec_detuning = self.get_variable_parameter("LocalSpec_detuning")
        # self.rabi.phase_729 = self.get_variable_parameter("MolmerSorensen_ms_phase")
        self.rabi.amp_729 = self.MolmerSorensen_analysis_amplitude
        self.rabi.att_729 = self.MolmerSorensen_analysis_att
        self.rabi.duration = self.MolmerSorensen_analysis_duration
        self.rabi.freq_729 = self.calc_frequency(
            self.MolmerSorensen_line_selection, 
            detuning=self.ms.detuning_carrier_1,
            dds="729G")
        if not self.MolmerSorensen_rotate_in_with_global:
            self.rotate_in.amp_729 = self.Rotation729L1_amplitude
            self.rotate_in.att_729 = self.Rotation729L1_att
            self.rotate_in.duration = self.Rotation729L1_pi_time
            #self.rotate_in.composite_pi_rotation = self.Rotation729L1_composite_pi_rotation 02/20/2020
            self.rotate_in.freq_729 = self.calc_frequency(
                self.MolmerSorensen_line_selection, 
                dds="729L1")
            self.composite.amp_729 = self.Rotation729L1_amplitude
            self.composite.att_729 = self.Rotation729L1_att
            self.composite.duration = self.Rotation729L1_pi_time
            self.composite.freq_729 = self.calc_frequency(
                self.MolmerSorensen_line_selection, 
                dds="729L1")
        else:
            self.rotate_in.amp_729 = self.Rotation729G_amplitude
            self.rotate_in.att_729 = self.Rotation729G_att
            self.rotate_in.duration = self.Rotation729G_pi_time
            self.rotate_in.freq_729 = self.calc_frequency(
                self.Rotation729G_line_selection, 
                dds="729G")
        
        # Comment out this block of code to disable ramping for MolmerSorensen bichro
        if self.MolmerSorensen_bichro_enable:
            self.ms.setup_ramping(self)

    @kernel
    def MolmerSorensen(self):
        self.phase_ref_time = now_mu()
        self.ms.phase_ref_time = self.phase_ref_time
        self.rabi.phase_ref_time = self.phase_ref_time
        

        self.stateprep.run(self)
        if self.MolmerSorensen_SDDS_enable:
            if self.Rotation729L1_composite_pi_rotation: # added for compostie pi
                self.composite.run(self)
            else:
                self.rotate_in.run(self)
        self.ms.run(self)
        if self.MolmerSorensen_SDDS_rotate_out:
            self.rotate_in.run(self)
        if self.MolmerSorensen_analysis_pulse_enable:
            self.rabi.phase_729 = self.get_variable_parameter("MolmerSorensen_ms_phase")
            delay(self.get_variable_parameter("MolmerSorensen_ramsey_duration"))
            self.rabi.run(self)
