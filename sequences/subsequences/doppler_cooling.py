from artiq.experiment import *


class DopplerCooling:
    duration="DopplerCooling.doppler_cooling_duration"
    additional_repump_duration="DopplerCooling.doppler_cooling_repump_additional"
    pre_duration="DopplerCooling.pre_duration"
    frequency_397="DopplerCooling.doppler_cooling_frequency_397"
    amplitude_397="DopplerCooling.doppler_cooling_amplitude_397"
    att_397="DopplerCooling.doppler_cooling_att_397"
    frequency_866="DopplerCooling.doppler_cooling_frequency_866"
    amplitude_866="DopplerCooling.doppler_cooling_amplitude_866"
    att_866="DopplerCooling.doppler_cooling_att_866"

    def subsequence(self):
        d = DopplerCooling
        self.dds_397.set(60*MHz, amplitude=d.amplitude_397)
        self.dds_397.set_att(d.att_397)
        self.dds_866.set(d.frequency_866, amplitude=d.amplitude_866)
        self.dds_866.set_att(d.att_866)
        with parallel:
            self.dds_397.sw.on()
            self.dds_866.sw.on()
        delay(d.pre_duration)
        self.dds_397.set(d.frequency_397, amplitude=d.amplitude_397)
        delay(d.duration)
        self.dds_397.sw.off()
        self.dds_397.set(20*MHz, amplitude=0.)
        delay(d.additional_repump_duration)
        self.dds_866.sw.off()