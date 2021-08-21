from artiq.experiment import *
from artiq.coredevice.ad9910 import RAM_MODE_RAMPUP, RAM_DEST_ASF
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING, PHASE_MODE_ABSOLUTE
import numpy as np


class BichroExcitation:
    bichro_enable="MolmerSorensen.bichro_enable"
    due_carrier_enable="MolmerSorensen.due_carrier_enable"
    sp_due_enable="MolmerSorensen.sp_due_enable"
    sp_line1_amp="MolmerSorensen.sp_line1_amp"
    sp_line2_amp="MolmerSorensen.sp_line2_amp"
    sp_line1_att="MolmerSorensen.sp_line1_att"
    sp_line2_att="MolmerSorensen.sp_line2_att"
    sp_line1_blue_amp="MolmerSorensen.sp_line1_blue_amp"
    sp_line2_blue_amp="MolmerSorensen.sp_line2_blue_amp"
    sp_line1_blue_att="MolmerSorensen.sp_line1_blue_att"
    sp_line2_blue_att="MolmerSorensen.sp_line2_blue_att"
    sp_line1_red_amp="MolmerSorensen.sp_line1_red_amp"
    sp_line2_red_amp="MolmerSorensen.sp_line2_red_amp"
    sp_line1_red_att="MolmerSorensen.sp_line1_red_att"
    sp_line2_red_att="MolmerSorensen.sp_line2_red_att"
    channel="MolmerSorensen.channel_729"
    shape_profile="MolmerSorensen.shape_profile"
    amp_blue="MolmerSorensen.amp_blue"
    amp_blue_noise_std="MolmerSorensen.amp_blue_noise_std"
    att_blue="MolmerSorensen.att_blue"
    amp_blue_ion2="MolmerSorensen.amp_blue_ion2"
    att_blue_ion2="MolmerSorensen.att_blue_ion2"
    amp_red="MolmerSorensen.amp_red"
    att_red="MolmerSorensen.att_red"
    amp_red_ion2="MolmerSorensen.amp_red_ion2"
    att_red_ion2="MolmerSorensen.att_red_ion2"
    amp="MolmerSorensen.amplitude"
    att="MolmerSorensen.att"
    amp_ion2="MolmerSorensen.amplitude_ion2"
    att_ion2="MolmerSorensen.att_ion2"
    phase="MolmerSorensen.phase"
    line_selection="MolmerSorensen.line_selection"
    line_selection_ion2="MolmerSorensen.line_selection_ion2"
    selection_sideband="MolmerSorensen.selection_sideband"
    duration="MolmerSorensen.duration"
    detuning="MolmerSorensen.detuning"
    detuning_carrier_1="MolmerSorensen.detuning_carrier_1"
    detuning_carrier_2="MolmerSorensen.detuning_carrier_2"
    default_sp_amp_729="Excitation_729.single_pass_amplitude"
    default_sp_att_729="Excitation_729.single_pass_att"
    phase_ref_time=np.int64(-1)
    ramp_has_been_programmed=False  # always initialize to False; gets set to True inside setup_ramping
    use_single_pass_freq_noise=False
    local_spec_enable="LocalSpec.enable"
    local_spec_detuning="LocalSpec.detuning"
    local_spec_att="LocalSpec.att"
    local_spec_amp="LocalSpec.amp"
    local_spec_duration="LocalSpec.duration"
    local_spec_line_selection="LocalSpec.line_selection"
    local_spec_sp_amp_729="Excitation_729.single_pass_amplitude"
    local_spec_sp_att_729="Excitation_729.single_pass_att"
    ac_stark_shift="MolmerSorensen.ac_stark_shift"

    def add_child_subsequences(pulse_sequence):
        b = BichroExcitation
    
    def setup_noisy_single_pass(pulse_sequence, freq_noise):
        b = BichroExcitation
        b.use_single_pass_freq_noise = freq_noise
        pulse_sequence.generate_single_pass_noise_waveform(
            mean=b.amp_blue,
            std=b.amp_blue_noise_std,
            freq_noise=freq_noise)

    @kernel
    def setup_ramping(pulse_sequence):
        # This function programs the appropriate ramp into the DDS memory.
        #
        # If a PulseSequence wants to use ramping, call setup_ramping() inside 
        # its set_subsequence function.
        # To disable ramping for a PulseSequence, the easiest way to do this is
        # comment or remove the call to setup_ramping() in the set_subsequence function.
        b = BichroExcitation
        
        pulse_sequence.prepare_pulse_with_amplitude_ramp(
            pulse_duration=b.duration,
            ramp_duration=2.0*us,
            dds1_amp=b.amp)
        b.ramp_has_been_programmed = True
        pulse_sequence.prepare_noisy_single_pass(freq_noise=b.use_single_pass_freq_noise)    
    

    def subsequence(self):
        b = BichroExcitation
        trap_frequency = self.get_trap_frequency(b.selection_sideband)
        freq_red = 80*MHz - trap_frequency - b.detuning
        freq_blue = 80*MHz + trap_frequency + b.detuning
        if b.channel == "global":
            offset = self.get_offset_frequency("729G")
            freq_blue += offset
            freq_red += offset
            
            if not b.sp_due_enable:
                self.get_729_dds("729G", id=0)
                
                dp_freq = self.calc_frequency(
                    b.line_selection,
                    detuning=b.detuning_carrier_1,
                    dds="729G"
                )

                if b.bichro_enable:
                    self.dds_729_SP.set(freq_blue, amplitude=b.amp_blue, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP.set_att(b.att_blue)
                    self.dds_729_SP_bichro.set(freq_red, amplitude=b.amp_red, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP_bichro.set_att(b.att_red)

                    self.start_noisy_single_pass(b.phase_ref_time,
                        freq_noise=b.use_single_pass_freq_noise,
                        freq_sp=freq_blue, amp_sp=b.amp_blue, att_sp=b.att_blue,
                        use_bichro=True,
                        freq_sp_bichro=freq_red, amp_sp_bichro=b.amp_red, att_sp_bichro=b.att_red)

                    if b.ramp_has_been_programmed:
                        
                        # Set double-pass to correct frequency and phase,
                        # and set amplitude to zero before starting the ramp.
                        self.dds_729.set(dp_freq,
                            amplitude=0.,
                            phase=b.phase / 360,
                            ref_time_mu=b.phase_ref_time)
                        self.execute_pulse_with_amplitude_ramp(
                            dds1_att=b.att,
                            dds1_freq=dp_freq)
                    else:
                        self.dds_729.set(dp_freq,
                            amplitude=b.amp,
                            phase=b.phase / 360,
                            ref_time_mu=b.phase_ref_time)
                        self.dds_729.set_att(b.att)
                        self.dds_729.sw.on()
                        # self.dds_729_SP.sw.on()
                        # self.dds_729_SP_bichro.sw.on()
                        delay(b.duration)
                        self.dds_729.sw.off()

                    self.stop_noisy_single_pass(use_bichro=True)

                else:
                    # bichro disabled
                    self.dds_729.set(dp_freq,
                        amplitude=b.amp,
                        phase=b.phase / 360,
                        ref_time_mu=b.phase_ref_time)
                    self.dds_729.set_att(b.att)
                    sp_freq_729 = 80*MHz + offset
                    self.dds_729_SP.set(sp_freq_729, amplitude=b.default_sp_amp_729, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP.set_att(b.default_sp_att_729)
                    with parallel:
                        self.dds_729.sw.on()
                        self.dds_729_SP.sw.on()
                    delay(b.duration)
                    with parallel:
                        self.dds_729.sw.off()
                        self.dds_729_SP.sw.off()
            
            elif b.sp_due_enable:
                self.get_729_dds(id=2)
                
                line1_freq = self.calc_frequency(
                    b.line_selection,
                )

                line2_freq = self.calc_frequency(
                    b.line_selection_ion2,
                    detuning=b.detuning_carrier_2,
                )

                if line2_freq > line1_freq:
                    sp_line1_freq = -(line2_freq - line1_freq) / 2
                    sp_line2_freq = -sp_line1_freq
                else:
                    sp_line2_freq = -(line2_freq - line1_freq) / 2
                    sp_line1_freq = -sp_line2_freq
                
                line1_freq_actual = self.calc_frequency(
                    b.line_selection,
                    detuning=b.detuning_carrier_1,
                    dds="729G"
                )

                line2_freq_actual = self.calc_frequency(
                    b.line_selection_ion2,
                    detuning=b.detuning_carrier_2,
                    dds="729G"
                )

                if line2_freq_actual > line1_freq_actual:
                    dp_freq_actual = line2_freq_actual - (line2_freq_actual - line1_freq_actual) / 2
                else:
                    dp_freq_actual = line1_freq_actual - (line1_freq_actual - line2_freq_actual) / 2

                self.dds_729.set(dp_freq_actual,
                    amplitude=b.amp,
                    phase=b.phase / 360,
                    ref_time_mu=b.phase_ref_time)

                freq_blue_line1 = 80*MHz + offset + sp_line1_freq + trap_frequency + b.detuning  # needs to be checked
                freq_red_line1 = 80*MHz + offset + sp_line1_freq - trap_frequency - b.detuning  # needs to be checked
                freq_blue_line2 = 80*MHz + offset + sp_line2_freq + trap_frequency + b.detuning + b.ac_stark_shift  # needs to be checked
                freq_red_line2 = 80*MHz + offset + sp_line2_freq - trap_frequency - b.detuning  - b.ac_stark_shift# needs to be checked

                if not b.bichro_enable:
                    #I guess we want two carrier tone come out from the SP if we disable the bichro
                    # self.dds_729.set_amplitude(b.amp)
                    self.dds_729.set_att(b.att)
                    sp_freq_729_line1 = 80*MHz + sp_line1_freq + offset
                    sp_freq_729_line2 = 80*MHz + sp_line2_freq + offset
                    self.dds_729_SP_line1.set(sp_freq_729_line1, amplitude=b.sp_line1_amp, ref_time_mu=b.phase_ref_time)
                    #Need to add new parameter sp_amp_729_line1 in MolmerSorenson
                    self.dds_729_SP_line1.set_att(b.sp_line1_att)# Need to add new parameter att_line1 in MolmerSorenson 
                    self.dds_729_SP_line2.set(sp_freq_729_line2, amplitude=b.sp_line2_amp, ref_time_mu=b.phase_ref_time)
                    #Need to add new parameter sp_amp_729_line2 in MolmerSorenson
                    self.dds_729_SP_line2.set_att(b.sp_line2_att)# Need to add new parameter att_line2 in MolmerSorenson
                    
                    with parallel:
                        self.dds_729.sw.on()
                        self.dds_729_SP_line1.sw.on()
                        self.dds_729_SP_line2.sw.on()
                    delay(b.duration)
                    with parallel:
                        self.dds_729.sw.off()
                        self.dds_729_SP_line1.sw.off()
                        self.dds_729_SP_line2.sw.off()
                
                if b.bichro_enable:
                    self.dds_729.set_amplitude(b.amp)
                    self.dds_729.set_att(b.att)
                    
                    self.dds_729_SP_line1.set(freq_blue_line1, amplitude=b.sp_line1_blue_amp, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP_line1.set_att(b.sp_line1_blue_att)
                    self.dds_729_SP_line1_bichro.set(freq_red_line1, amplitude=b.sp_line1_red_amp, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP_line1.set_att(b.sp_line1_red_att)
                    
                    self.dds_729_SP_line2.set(freq_blue_line2, amplitude=b.sp_line2_blue_amp, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP_line2.set_att(b.sp_line2_blue_att) # need to add parameter att_blue_line2
                    self.dds_729_SP_line2_bichro.set(freq_red_line2, amplitude=b.sp_line2_red_amp, ref_time_mu=b.phase_ref_time)
                    self.dds_729_SP_line2.set_att(b.sp_line2_red_att)

                    if not b.local_spec_enable:
                        with parallel:
                            self.dds_729.sw.on()
                            self.dds_729_SP_line1.sw.on()
                            self.dds_729_SP_line2.sw.on()
                            self.dds_729_SP_line1_bichro.sw.on()
                            self.dds_729_SP_line2_bichro.sw.on()
                        delay(b.duration)
                        with parallel:
                            self.dds_729.sw.off()
                            self.dds_729_SP_line1.sw.off()
                            self.dds_729_SP_line2.sw.off()
                            self.dds_729_SP_line1_bichro.sw.off()
                            self.dds_729_SP_line2_bichro.sw.off()
                    else:
                        p_freq = self.calc_frequency(
                            b.local_spec_line_selection,
                            detuning=b.local_spec_detuning,
                            dds="729L1"
                        )
                        self.dds_729L1.set(p_freq, amplitude=b.local_spec_amp, ref_time_mu=b.phase_ref_time)
                        self.dds_729L1.set_att(b.local_spec_att)
                        local_offset_freq = 80*MHz + self.get_offset_frequency("729L1")
                        self.dds_SP_729L1.set(local_offset_freq, amplitude=b.local_spec_sp_amp_729, ref_time_mu=b.phase_ref_time)
                        self.dds_SP_729L1.set_att(b.local_spec_sp_att_729)
                        # print("dp: ", p_freq)
                        # print("sp: ", local_offset_freq)
                        with parallel:
                            self.dds_729.sw.on()
                            self.dds_729_SP_line1.sw.on()
                            self.dds_729_SP_line2.sw.on()
                            self.dds_729_SP_line1_bichro.sw.on()
                            self.dds_729_SP_line2_bichro.sw.on()
                            self.dds_729L1.sw.on()
                            self.dds_SP_729L1.sw.on()
                        delay(b.duration)
                        with parallel:
                            self.dds_729.sw.off()
                            self.dds_729_SP_line1.sw.off()
                            self.dds_729_SP_line2.sw.off()
                            self.dds_729_SP_line1_bichro.sw.off()
                            self.dds_729_SP_line2_bichro.sw.off()
                            self.dds_729L1.sw.off()
                            self.dds_SP_729L1.sw.off()



#############################################################################################################################3
        elif b.channel == "local":
            self.get_729_dds("729L1")
            self.get_729_dds("729L2", id=1)
            offset1 = self.get_offset_frequency("729L1")
            freq_blue1 = freq_blue + offset1
            freq_red1 = freq_red + offset1
            offset2 = self.get_offset_frequency("729L2")
            freq_blue2 = freq_blue + offset2
            freq_red2 = freq_red + offset2
            dp_freq1 = self.calc_frequency(
                b.line_selection,
                detuning=b.detuning_carrier_1,
                dds="729L1"
            )
            if b.due_carrier_enable:
                dp_freq2 = self.calc_frequency(
                    b.line_selection_ion2,
                    detuning=b.detuning_carrier_2,
                    dds="729L2"
                )
            else:
                dp_freq2 = self.calc_frequency(
                    b.line_selection,
                    dds="729L2"
                )
            self.dds_729.set(dp_freq1,
                             amplitude=b.amp,
                             phase=b.phase / 360,
                             ref_time_mu=b.phase_ref_time)
            self.dds_729.set_att(b.att)
            self.dds_7291.set(dp_freq2,
                             amplitude=b.amp_ion2,
                             phase=b.phase / 360,
                             ref_time_mu=b.phase_ref_time)
            self.dds_7291.set_att(b.att_ion2)
            if b.bichro_enable:
                self.dds_729_SP.set(freq_blue1, amplitude=b.amp_blue, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP.set_att(b.att_blue)
                self.dds_729_SP_bichro.set(freq_red1, amplitude=b.amp_red, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP_bichro.set_att(b.att_red)
                self.dds_729_SP1.set(freq_blue2, amplitude=b.amp_blue_ion2, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP1.set_att(b.att_blue_ion2)
                self.dds_729_SP_bichro1.set(freq_red2, amplitude=b.amp_red_ion2, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP_bichro1.set_att(b.att_red_ion2)
                with parallel:
                    self.dds_729.sw.on()
                    self.dds_729_SP.sw.on()
                    self.dds_729_SP_bichro.sw.on()
                    self.dds_7291.sw.on()
                    self.dds_729_SP1.sw.on()
                    self.dds_729_SP_bichro1.sw.on()
                delay(b.duration)
                with parallel:
                    self.dds_729.sw.off()
                    self.dds_729_SP.sw.off()
                    self.dds_729_SP_bichro.sw.off()
                    self.dds_7291.sw.off()
                    self.dds_729_SP1.sw.off()
                    self.dds_729_SP_bichro1.sw.off()
            else:
                # bichro disabled
                sp_freq_7291 = 80*MHz + offset1
                self.dds_729_SP.set(sp_freq_7291, amplitude=b.default_sp_amp_729, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP.set_att(b.default_sp_att_729)
                sp_freq_7292 = 80*MHz + offset2
                self.dds_729_SP1.set(sp_freq_7292, amplitude=b.default_sp_amp_729, ref_time_mu=b.phase_ref_time)
                self.dds_729_SP1.set_att(b.default_sp_att_729)
                with parallel:
                    self.dds_729.sw.on()
                    self.dds_729_SP.sw.on()
                    self.dds_7291.sw.on()
                    self.dds_729_SP1.sw.on()
                delay(b.duration)
                with parallel:
                    self.dds_729.sw.off()
                    self.dds_729_SP.sw.off()
                    self.dds_7291.sw.off()
                    self.dds_729_SP1.sw.off()