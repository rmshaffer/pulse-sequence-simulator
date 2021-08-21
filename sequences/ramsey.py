from pulse_sequence import PulseSequence
from subsequences.rabi_excitation import RabiExcitation
from subsequences.rabi_excitation2 import RabiExcitation2  #Fix this later
from subsequences.state_preparation import StatePreparation
from artiq.experiment import *

class Ramsey(PulseSequence):
    PulseSequence.accessed_params = {
        "Ramsey.wait_time",
        "Ramsey.phase",
        "Ramsey.selection_sideband",
        "Ramsey.order",
        "Ramsey.channel_729",
        "Ramsey.detuning",
        "Ramsey.echo",
        "Ramsey.no_return",
        "Ramsey.bsb_pulse",
        "Rotation729L1.pi_time",
        "Rotation729L1.line_selection",
        "Rotation729L1.amplitude",
        "Rotation729L1.att",
        "Rotation729L2.pi_time",
        "Rotation729L1.bsb_amplitude",
        "Rotation729L1.bsb_att",
        "Rotation729L1.bsb_pi_time",
        "Rotation729L2.line_selection",
        "Rotation729L2.amplitude",
        "Rotation729L2.att",
        "Rotation729G.pi_time",
        "Rotation729G.line_selection",
        "Rotation729G.amplitude",
        "Rotation729G.att",
        "RabiFlopping.detuning"
    }

    PulseSequence.scan_params = dict(
        Ramsey=[
            ("Ramsey", ("Ramsey.wait_time", 0*ms, 5*ms, 100, "ms")),
            ("Ramsey", ("Ramsey.phase", 0., 360., 20, "deg"))
        ])
    
    def run_initially(self):
        self.stateprep = self.add_subsequence(StatePreparation)
        self.rabi = self.add_subsequence(RabiExcitation)
        self.rabi.channel_729 = self.p.Ramsey.channel_729  
        self.bsb_rabi = self.add_subsequence(RabiExcitation2)
        self.bsb_rabi.channel_729 = self.p.Ramsey.channel_729
        self.set_subsequence["Ramsey"] = self.set_subsequence_ramsey
        if self.p.Ramsey.channel_729 == "729L1":
            self.pi_time = self.p.Rotation729L1.pi_time
            self.line_selection = self.p.Rotation729L1.line_selection
            self.amplitude = self.p.Rotation729L1.amplitude
            self.att = self.p.Rotation729L1.att

            self.bsb_pi_time = self.p.Rotation729L1.bsb_pi_time
            self.bsb_amplitude = self.p.Rotation729L1.bsb_amplitude
            self.bsb_att = self.p.Rotation729L1.bsb_att
        elif self.p.Ramsey.channel_729 == "729L2":
            self.pi_time = self.p.Rotation729L2.pi_time
            self.line_selection = self.p.Rotation729L2.line_selection
            self.amplitude = self.p.Rotation729L2.amplitude
            self.att = self.p.Rotation729L2.att

            self.bsb_pi_time = self.p.Rotation729L1.bsb_pi_time
            self.bsb_amplitude = self.p.Rotation729L1.bsb_amplitude
            self.bsb_att = self.p.Rotation729L1.bsb_att
        elif self.p.Ramsey.channel_729 == "729G":
            self.pi_time = self.p.Rotation729G.pi_time
            self.line_selection = self.p.Rotation729G.line_selection
            self.amplitude = self.p.Rotation729G.amplitude
            self.att = self.p.Rotation729G.att

            self.bsb_pi_time = self.p.Rotation729L1.bsb_pi_time
            self.bsb_amplitude = self.p.Rotation729L1.bsb_amplitude
            self.bsb_att = self.p.Rotation729L1.bsb_att
        self.wait_time = 0.
        self.phase = 0.
        
    @kernel
    def set_subsequence_ramsey(self):
        self.rabi.duration = self.pi_time / 2
        self.rabi.amp_729 = self.amplitude
        self.rabi.att_729 = self.att
        self.rabi.freq_729 = self.calc_frequency(
            self.line_selection, 
            detuning=self.Ramsey_detuning,
            sideband=self.Ramsey_selection_sideband,
            order=self.Ramsey_order, 
            dds=self.Ramsey_channel_729
        )
        print("freq: ", self.rabi.freq_729)
        self.bsb_rabi.duration = self.bsb_pi_time
        self.bsb_rabi.amp_729 = self.bsb_amplitude
        self.bsb_rabi.att_729 = self.bsb_att
        self.bsb_rabi.freq_729 = self.calc_frequency(
            self.line_selection, 
            detuning=self.RabiFlopping_detuning,
            sideband=self.Ramsey_selection_sideband,
            order=1.0, 
            dds=self.Ramsey_channel_729
        )
        print("freqbsb: ", self.bsb_rabi.freq_729)
        self.wait_time = self.get_variable_parameter("Ramsey_wait_time")

    @kernel
    def Ramsey(self):
        self.rabi.phase_ref_time = now_mu()
        self.bsb_rabi.phase_ref_time = self.rabi.phase_ref_time
        self.stateprep.run(self)
        self.rabi.phase_729 = 0.
        if not self.Ramsey_echo:
            self.rabi.run(self)
            if self.Ramsey_bsb_pulse:
                self.bsb_rabi.run(self)
            delay_mu(self.core.seconds_to_mu(self.wait_time))
            self.rabi.phase_729 = self.get_variable_parameter("Ramsey_phase")
            if not self.Ramsey_no_return:
                if self.Ramsey_bsb_pulse:
                    # self.bsb_rabi.phase_729 = 90.0
                    self.bsb_rabi.run(self)
                self.rabi.run(self)
        else:
            self.rabi.run(self)
            if self.Ramsey_bsb_pulse:
                self.bsb_rabi.run(self)
            delay(self.wait_time / 2)
            if self.Ramsey_bsb_pulse:
                self.bsb_rabi.run(self)
            self.rabi.duration = self.pi_time
            self.rabi.run(self)
            if self.Ramsey_bsb_pulse:
                self.bsb_rabi.run(self)
            delay(self.wait_time / 2)
            if self.Ramsey_bsb_pulse:
                # self.bsb_rabi.phase_729 = 90.0
                self.bsb_rabi.run(self)
            self.rabi.duration = self.pi_time / 2
            if self.selected_scan_name == "Ramsey_phase":
                self.rabi.phase_729 = self.get_variable_parameter("Ramsey_phase")
            self.rabi.run(self)