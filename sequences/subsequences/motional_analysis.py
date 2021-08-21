from artiq.experiment import *


class MotionalAnalysis:
    freq_397="DopplerCooling.doppler_cooling_frequency_397"
    amp_397="MotionAnalysis.amplitude_397"
    att_397="MotionAnalysis.att_397"

    freq_866="DopplerCooling.doppler_cooling_frequency_866"
    amp_866="DopplerCooling.doppler_cooling_amplitude_866"
    att_866="DopplerCooling.doppler_cooling_att_866"

    pulse_width="MotionAnalysis.pulse_width_397"


    def subsequence(self):
        m = MotionalAnalysis
        self.dds_397.set(m.freq_397,
                         amplitude=m.amp_397)
        self.dds_397.set_att(m.att_397)
        self.dds_866.set(m.freq_866,
                         amplitude=m.amp_866)
        self.dds_866.set_att(m.att_866)
        with parallel:
            self.dds_866.sw.on()
            self.dds_397.sw.on()
            self.mod397.on()
        delay(m.pulse_width)
        with parallel:
            self.dds_397.sw.off()
            self.mod397.off()
        delay(50*us)
        self.dds_866.sw.off()
