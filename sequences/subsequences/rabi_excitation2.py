from artiq.experiment import *
import numpy as np
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING, PHASE_MODE_ABSOLUTE

class RabiExcitation2:
    freq_729="Excitation_729.rabi_excitation_frequency"
    amp_729="Excitation_729.rabi_excitation_amplitude"
    att_729="Excitation_729.rabi_excitation_att"
    phase_729="Excitation_729.rabi_excitation_phase"
    channel_729="Excitation_729.channel_729"
    duration="Excitation_729.rabi_excitation_duration"
    line_selection="Excitation_729.line_selection"
    sp_amp_729="Excitation_729.single_pass_amplitude"
    sp_att_729="Excitation_729.single_pass_att"
    phase_ref_time=np.int64(-1)
    use_ramping=False

    @kernel
    def setup_ramping(self):
        r = RabiExcitation2        
        self.get_729_dds(r.channel_729)
        self.prepare_pulse_with_amplitude_ramp(
            pulse_duration=r.duration,
            ramp_duration=2*us,
            dds1_amp=r.amp_729)
        r.use_ramping = True

    def subsequence(self):
        r = RabiExcitation2
        self.get_729_dds(r.channel_729)

        if r.use_ramping:
            self.dds_729.set(r.freq_729,
                            amplitude=0.,
                            ref_time_mu=r.phase_ref_time)
        else:
            self.dds_729.set(r.freq_729,
                            amplitude=r.amp_729,
                            ref_time_mu=r.phase_ref_time)
            self.dds_729.set_att(r.att_729)

        sp_freq_729 = 80*MHz + self.get_offset_frequency(r.channel_729)
        self.dds_729_SP.set(sp_freq_729, amplitude=r.sp_amp_729, 
                         phase=r.phase_729 / 360., ref_time_mu=r.phase_ref_time)
        self.dds_729_SP.set_att(r.sp_att_729)
        
        if r.use_ramping:
            self.dds_729_SP.sw.on()
            self.execute_pulse_with_amplitude_ramp(
                dds1_att=r.att_729,
                dds1_freq=r.freq_729)
            self.dds_729_SP.sw.off()
        else:
            with parallel:
                self.dds_729.sw.on()
                self.dds_729_SP.sw.on()
            delay(r.duration)
            with parallel:
                self.dds_729.sw.off()
                self.dds_729_SP.sw.off()