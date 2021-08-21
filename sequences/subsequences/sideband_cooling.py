from artiq.experiment import *
from subsequences.optical_pumping import OpticalPumping

class SidebandCooling:
    line_selection="SidebandCooling.line_selection"
    selection_sideband="SidebandCooling.selection_sideband"
    order="SidebandCooling.order"
    stark_shift="SidebandCooling.stark_shift"
    channel_729="SidebandCooling.channel_729"
    repump_additional="OpticalPumpingContinuous.optical_pumping_continuous_repump_additional"
    amplitude_729="SidebandCooling.amplitude_729"
    att_729="SidebandCooling.att_729"
    duration="SidebandCooling.duration"
    sp_amp_729="Excitation_729.single_pass_amplitude"
    sp_att_729="Excitation_729.single_pass_att"
    
    freq_866="SidebandCooling.frequency_866"
    amp_866="SidebandCooling.amplitude_866"
    att_866="SidebandCooling.att_866"
    
    freq_854="SidebandCooling.frequency_854"
    amp_854="SidebandCooling.amplitude_854"
    att_854="SidebandCooling.att_854"

    sideband_cooling_cycles="SidebandCooling.sideband_cooling_cycles"

    sequential_enable="SequentialSBCooling.enable"
    sequential_channel_729="SequentialSBCooling.channel_729"
    sequential_selection_sideband="SequentialSBCooling.selection_sideband"
    sequential_order="SequentialSBCooling.order"

    sequential1_enable="SequentialSBCooling1.enable"
    sequential1_channel_729="SequentialSBCooling1.channel_729"
    sequential1_selection_sideband="SequentialSBCooling1.selection_sideband"
    sequential1_order="SequentialSBCooling1.order"

    sequential2_enable="SequentialSBCooling2.enable"
    sequential2_channel_729="SequentialSBCooling2.channel_729"
    sequential2_selection_sideband="SequentialSBCooling2.selection_sideband"
    sequential2_order="SequentialSBCooling2.order"

    def add_child_subsequences(pulse_sequence):
        s = SidebandCooling
        s.op = pulse_sequence.add_subsequence(OpticalPumping)

    def subsequence(self):
        s = SidebandCooling

        def run_sideband_cooling(self, channel, sideband, sideband_order):
            self.get_729_dds(channel)
            freq_729 = self.calc_frequency(
                            s.line_selection,
                            detuning=s.stark_shift,
                            sideband=sideband,
                            order=sideband_order,
                            dds=channel
                        )
            self.dds_729.set(freq_729, amplitude=s.amplitude_729)
            self.dds_729.set_att(s.att_729)
            sp_freq_729 = 80*MHz + self.get_offset_frequency(channel)
            self.dds_729_SP.set(sp_freq_729, amplitude=s.sp_amp_729)
            self.dds_729_SP.set_att(s.sp_att_729)
            self.dds_854.set(s.freq_854, amplitude=s.amp_854)
            self.dds_854.set_att(s.att_854)
            self.dds_866.set(s.freq_866, amplitude=s.amp_866)
            self.dds_866.set_att(s.att_866)

            with parallel:
                self.dds_854.sw.on()
                self.dds_866.sw.on()
                self.dds_729.sw.on()
                self.dds_729_SP.sw.on()
            delay(s.duration)
            with parallel:
                self.dds_854.sw.off()
                self.dds_866.sw.off()
                self.dds_729.sw.off()
                #self.dds_729_SP.sw.off()  keep SP on all the time 2/24/2020
            s.op.run(self)

        num_cycles = int(s.sideband_cooling_cycles)

        i = 0
        for i in range(num_cycles):
            run_sideband_cooling(
                self,
                s.channel_729,
                s.selection_sideband,
                s.order)
            
            if s.sequential_enable:
                run_sideband_cooling(
                    self,
                    s.sequential_channel_729,
                    s.sequential_selection_sideband,
                    s.sequential_order)

            if s.sequential1_enable:
                run_sideband_cooling(
                    self,
                    s.sequential1_channel_729,
                    s.sequential1_selection_sideband,
                    s.sequential1_order)

            if s.sequential2_enable:
                run_sideband_cooling(
                    self,
                    s.sequential2_channel_729,
                    s.sequential2_selection_sideband,
                    s.sequential2_order)
            
        #
        self.dds_854.set(80*MHz, amplitude=1.0)
        self.dds_854.set_att(5.0)
        self.dds_866.set(80*MHz, amplitude=1.0)
        self.dds_866.set_att(5.0)
        with parallel:
            self.dds_854.sw.on()
            self.dds_866.sw.on()
        #print('repump time',s.repump_additional)
        delay(3 * s.repump_additional)
        with parallel:
            self.dds_854.sw.off()
            self.dds_866.sw.off()
