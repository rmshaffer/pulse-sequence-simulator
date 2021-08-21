from artiq.experiment import *


class OpticalPumpingContinuous:
    frequency_866="DopplerCooling.doppler_cooling_frequency_866"
    amplitude_866="DopplerCooling.doppler_cooling_amplitude_866"
    att_866="DopplerCooling.doppler_cooling_att_866"
    frequency_854="OpticalPumping.optical_pumping_frequency_854"
    amplitude_854="OpticalPumping.optical_pumping_amplitude_854"
    att_854="OpticalPumping.optical_pumping_att_854"
    line_selection="OpticalPumping.line_selection"
    channel_729="StatePreparation.channel_729"
    duration="OpticalPumpingContinuous.optical_pumping_continuous_duration"
    rempump_duration="OpticalPumpingContinuous.optical_pumping_continuous_repump_additional"
    amplitude_729="OpticalPumping.amplitude_729"
    att_729="OpticalPumping.att_729"
    sp_amp_729="Excitation_729.single_pass_amplitude"
    sp_att_729="Excitation_729.single_pass_att"

    def subsequence(self):
        o = OpticalPumpingContinuous
        self.get_729_dds(o.channel_729)
        self.dds_866.set(o.frequency_866,
                         amplitude=o.amplitude_866)
        self.dds_866.set_att(o.att_866)
        self.dds_854.set(o.frequency_854,
                         amplitude=o.amplitude_854)
        self.dds_854.set_att(o.att_854)
        freq_729 = self.calc_frequency(
            o.line_selection,
            dds=o.channel_729
        )
        self.dds_729.set(freq_729, 
                         amplitude=o.amplitude_729)
        self.dds_729.set_att(o.att_729)
        sp_freq_729 = 80*MHz + self.get_offset_frequency(o.channel_729)
        self.dds_729_SP.set(sp_freq_729, amplitude=o.sp_amp_729)
        self.dds_729_SP.set_att(o.sp_att_729)

        with parallel:
            self.dds_866.sw.on()
            self.dds_854.sw.on()
            self.dds_729.sw.on()
            self.dds_729_SP.sw.on()
        delay(o.duration)
        with parallel:
            self.dds_729.sw.off()
            # self.dds_729_SP.sw.off()
        delay(2 * o.rempump_duration)
        with parallel:
            self.dds_854.sw.off()
            self.dds_866.sw.off()

