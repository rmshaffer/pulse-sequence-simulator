from artiq.language import core as core_language
from sipyco.pc_rpc import Client
from datetime import datetime
from easydict import EasyDict as edict
import importlib
import importlib.machinery
import importlib.util
import json
import logging
import numpy as np
import os
import traceback
import sys

logger = logging.getLogger(__name__)

def unitless(param):
    return param

#
# Entry point to trigger a simulation of a particular experiment
#
def run_simulation(file_path, class_, argument_values):
    try:
        # define a function to import a modified source file
        def modify_and_import(module_name, path, modification_func):
            # adapted from https://stackoverflow.com/questions/41858147/how-to-modify-imported-source-code-on-the-fly
            loader = importlib.machinery.SourceFileLoader(module_name, path)
            source = loader.get_source(module_name)
            new_source = modification_func(source)
            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            codeobj = compile(new_source, module.__spec__.origin, 'exec')
            exec(codeobj, module.__dict__)
            sys.modules[module_name] = module
            return module

        # import all of the subsequences and strip out the @kernel decorators
        subsequences_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sequences", "subsequences")
        num_attempts = 2 # some may fail on first try due to dependencies, but will succeed eventually
        for attempt in range(1, num_attempts+1):
            for path, subdirs, files in os.walk(subsequences_folder):
                for filename in files:
                    filename_without_extension, extension = os.path.splitext(filename)
                    if extension == ".py":
                        try:
                            module_name = "simulated_subsequences." + filename_without_extension
                            experiment_file_full_path = os.path.join(path, filename)
                            modify_and_import(module_name, experiment_file_full_path, lambda src:
                                src.replace("@kernel", ""))
                        except:
                            if attempt == num_attempts:
                                logger.error("Error importing subsequence " + filename_without_extension + ": " + traceback.format_exc())
                            continue

        # import all of the auto calibration sequences and strip out the @kernel decorators
        auto_calibration_sequences_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_calibration", "sequences")
        for path, subdirs, files in os.walk(auto_calibration_sequences_folder):
            for filename in files:
                filename_without_extension, extension = os.path.splitext(filename)
                if extension == ".py":
                    try:
                        module_name = "auto_calibration.simulated_sequences." + filename_without_extension
                        experiment_file_full_path = os.path.join(path, filename)
                        modify_and_import(module_name, experiment_file_full_path, lambda src:
                            src.replace("from pulse_sequence", "from simulated_pulse_sequence")
                            .replace("from subsequences.", "from simulated_subsequences.")
                            .replace("from .", "from simulated_subsequences.")
                            .replace("from auto_calibration.sequences.", "from auto_calibration.simulated_sequences.")
                            .replace("@kernel", ""))
                    except:
                        logger.error("Error importing auto calibration sequence " + filename_without_extension + ": " + traceback.format_exc())
                        continue

        # load the experiment source and make the necessary modifications
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        mod = modify_and_import(class_, file_path, lambda src: 
            src.replace("from pulse_sequence", "from simulated_pulse_sequence")
            .replace("from subsequences.", "from simulated_subsequences.")
            .replace("from .", "from simulated_subsequences.")
            .replace("from auto_calibration.sequences.", "from auto_calibration.simulated_sequences.")
            .replace("@kernel", ""))

        # execute the simulated pulse sequence
        pulse_sequence = getattr(mod, class_)()
        pulse_sequence.set_submission_arguments(argument_values)
        pulse_sequence.simulate()

        return pulse_sequence.data
    except:
        logger.error("Error simulating pulse sequence" + traceback.format_exc())

class SimulatedDDSSwitch:
    def __init__(self, dds):
        self.dds = dds
        self.is_on = False
    def on(self):
        if not self.is_on:
            self.is_on = True
            self.dds._switched_on()
    def off(self):
        if self.is_on:
            self.is_on = False
            self.dds._switched_off()
    def toggle(self):
        if self.is_on:
            self.off()
        else:
            self.on()

class SimulatedDDS:

    def __init__(self, name, pulse_sequence):
        self.name = name
        self.pulse_sequence = pulse_sequence
        self.sw = SimulatedDDSSwitch(self)
        self.freq = 0.0
        self.amplitude = 0.0
        self.phase = 0.0
        self.ref_time_mu = 0
        self.att = 8.0

    def _switched_on(self):
        self.time_switched_on = self.pulse_sequence.time_manager.get_time()

    def _switched_off(self):
        if self.time_switched_on is not None:
            time_switched_off = self.pulse_sequence.time_manager.get_time()
            self.pulse_sequence.report_pulse(self, self.time_switched_on, time_switched_off)
            self.time_switched_on = None

    def set(self, freq, amplitude=None, phase=None, ref_time_mu=None):
        self.freq = float(unitless(freq))
        if amplitude is not None:
            self.amplitude = float(unitless(amplitude))
        if phase is not None:
            self.phase = float(unitless(phase))
        if ref_time_mu is not None:
            self.ref_time_mu = float(unitless(ref_time_mu))

    def set_amplitude(self, amplitude):
        self.amplitude = float(unitless(amplitude))

    def set_att(self, att):
        self.att = float(unitless(att))

class _FakeCore:
    def seconds_to_mu(self, time):
        return time

class SimulationScheduler:
    def submit(self, scheduler_name, expid, priority=None):
        run_simulation(expid["file"], expid["class_name"], expid["arguments"])

    def get_status(self):
        return dict()

class FitError(Exception):
    pass

class PulseSequence:

    scan_params = dict()

    def __init__(self):
        self.p = None
        self.set_subsequence = dict()
        self.run_after = dict()
        self.selected_scan = dict()
        self.time_manager = None
        self.parameter_dict = None
        self.simulated_pulses = None
        self.core = _FakeCore()
        self.data = edict()
        self.scheduler = SimulationScheduler()
        self.rcg_tabs = dict()
        
        self.grapher = None
        self.visualizer = None
        self.logger = None
        self.setup_rpc_connections()

        self.sequence_name = type(self).__name__
        self.frequency_scan_sequence_names = ["Spectrum", "CalibAllLines", "CalibSideband"]
        self.rcg_tabs[self.sequence_name] = dict()
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime("%H%M_%S")
        self.dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "simulation",
                                datetime.now().strftime("%Y-%m-%d"), self.sequence_name)
        os.makedirs(self.dir, exist_ok=True)
        os.chdir(self.dir)

    def set_submission_arguments(self, submission_arguments):
        self.submission_arguments = submission_arguments
    
    def write_line(self, output_file, line):
        # writes a line to both the file and the logger (if uncommented)
        output_file.write(line + "\n")
        #self.logger.info(line)

    def load_parameters(self):
        if not self.p:
            self.p = self.load_parameter_vault()

        self.parameter_dict = {}

        # add accessed params to parameter_dict
        for collection_name in self.p:
            for param_name in self.p[collection_name]:
                self.parameter_dict[collection_name + "." + param_name] = self.p[collection_name][param_name]

        # update trap frequencies in member variables
        self.trap_frequency_names = list()
        self.trap_frequency_values = list()
        for name, value in self.p.TrapFrequencies.items():
            self.trap_frequency_names.append(name)
            self.trap_frequency_values.append(value)
    
    def write_parameters_for_scan(self, scan_name):
        if not self.p:
            self.load_parameters()

        # add scan params to parameter_dict
        self.parameter_dict["Scan.sequence_name"] = self.sequence_name
        self.parameter_dict["Scan.scan_name"] = scan_name
        self.parameter_dict["Scan.parameter_name"] = self.scan_parameter_name
        for k,v in self.scan_settings.items():
            self.parameter_dict["Scan." + k] = v

        # write all the parameters to a file
        filename = self.timestamp + "_params_" + scan_name + ".txt"
        with open(filename, "w") as param_file:
            self.write_line(param_file, str(self.parameter_dict))
        print("Parameters written to " + os.path.join(self.dir, filename))

    def report_pulse(self, dds, time_switched_on, time_switched_off):
        simulated_pulse = {
            "dds_name": dds.name,
            "time_on": time_switched_on,
            "time_off": time_switched_off,
            "freq": dds.freq,
            "amp": dds.amplitude,
            "att": dds.att,
            "phase": dds.phase,
        }
        self.simulated_pulses.append(simulated_pulse)

    def combine_laser_pulses(self):
        # First, post-process the simulated_pulses to combine pulses that belong
        # to the same laser tone, e.g. 729G and SP_729G or SP_729G_bichro
        
        # for each pulse with dds_name == SP_foo
            # for each overlapping pulse with dds_name == foo
                # create a new pulse with dds_name == foo
                    # amp: product
                    # att: sum
                    # freq: sum - 80*MHz
                    # phase: sum
                    # time_off: min
                    # time_on: max
        self.combined_laser_pulses = []
        for pulse in self.simulated_pulses:
            if pulse["dds_name"].startswith("SP_"):
                pulse["processed"] = True
                for other_pulse in self.simulated_pulses:
                    # pulse is a single-pass, e.g. SP_729G or SP_729G_bichro
                    # looking for other_pulse to be the double-pass 729G
                    laser_name = pulse["dds_name"][3:]
                    if laser_name.startswith(other_pulse["dds_name"]):
                        other_pulse["processed"] = True
                        combined_time_on = max(pulse["time_on"], other_pulse["time_on"])
                        combined_time_off = min(pulse["time_off"], other_pulse["time_off"])
                        if combined_time_on < combined_time_off:
                            new_pulse = {
                                "dds_name": laser_name,
                                "time_on": combined_time_on,
                                "time_off": combined_time_off,
                                "freq": pulse["freq"] + other_pulse["freq"] - 80e6,
                                "amp": pulse["amp"] * other_pulse["amp"],
                                "att": pulse["att"] + other_pulse["att"],
                                "phase": pulse["phase"] + other_pulse["phase"],
                            }
                            self.combined_laser_pulses.append(new_pulse)

        self.combined_laser_pulses.extend([pulse for pulse in self.simulated_pulses if "processed" not in pulse])

    def simulate_with_ion_sim(self):
        try:
            return self.julia_simulation_function(
                self.parameter_dict,
                self.combined_laser_pulses,
                self.num_ions,
                self.current_b_field)
        except:
            self.logger.error("Error running IonSim simulation: " + traceback.format_exc())
            raise

    def simulate(self):
        self.load_parameters()
        self.setup_carriers()
        self.setup_dds()
        
        self.N = int(self.p.StateReadout.repeat_each_measurement)

        self.num_ions = int(self.p.IonsOnCamera.ion_number)

        # Import the Julia simulation function
        try:
            # Check to see if a precompiled system image exists
            path_to_sys_so = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sys.so")
            if os.path.exists(path_to_sys_so):
                from julia import Julia
                _ = Julia(sysimage=path_to_sys_so)

            path_to_simulate_jl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulate.jl")
            from julia import Main
            Main.include(path_to_simulate_jl)
            self.julia_simulation_function = Main.simulate_with_ion_sim
        except:
            self.logger.error("Error loading Julia file simulate.jl: " + traceback.format_exc())
            raise
        
        run_initially_complete = False
        for scan_name in PulseSequence.scan_params:
            self.data[scan_name] = edict(x=[], y=[])
            x_data = np.array([], dtype=float)
            y_data = {}
            
            # Look up the settings for the current scan.
            scan_selection = scan_name + "-Scan_Selection"
            if not scan_selection in self.submission_arguments:
                continue
            self.scan_parameter_name = self.submission_arguments[scan_selection]
            self.scan_settings = self.submission_arguments[scan_name + ":" + self.scan_parameter_name]
            self.selected_scan[scan_name] = self.scan_parameter_name
            
            # Output parameters to be used for the current scan.
            self.write_parameters_for_scan(scan_name)

            # Call run_initially, but only if this is the first scan.
            if not run_initially_complete:
                self.run_initially()
                run_initially_complete = True
            
            # Determine the list of scan points.
            variable_param_name = self.scan_parameter_name.replace(".", "_")
            scan_points = [self.get_variable_parameter(variable_param_name)]
            if self.scan_settings["ty"] == "RangeScan":
                scan_points = np.linspace(self.scan_settings["start"], self.scan_settings["stop"], self.scan_settings["npoints"])

            # Iterate over the scan points and simulate one pulse sequence per point.
            for scan_idx, scan_point in enumerate(scan_points):
                # Reset the timer and stored pulse sequence.
                self.setup_time_manager()
                self.simulated_pulses = []

                # Overwrite the scan parameter value with the current scan point.
                setattr(self, variable_param_name, scan_point)
                self.parameter_dict[self.scan_parameter_name] = scan_point

                # Set the current x value for plotting. May be overwritten inside a pulse sequence.
                self.current_x_value = scan_point

                # Initialize the sequence by calling set_subsequence.
                self.set_subsequence[scan_name]()

                # Run the pulse sequence function to generate the pulse sequence.
                current_sequence = getattr(self, scan_name)
                current_sequence()

                # Write the generated pulse sequences to a file.
                filename = self.timestamp + "_pulses_" + scan_name + "_" + str(scan_idx) + ".txt"
                with open(filename, "w") as pulses_file:
                    self.write_line(pulses_file, json.dumps(self.simulated_pulses, sort_keys=True, indent=4))
                print("Pulse sequence written to " + os.path.join(self.dir, filename))

                # Post-process the pulses to combine single-pass and double-pass pulses
                # into laser pulses, and also write these to a file.
                self.combine_laser_pulses()
                filename = self.timestamp + "_lasers_" + scan_name + "_" + str(scan_idx) + ".txt"
                with open(filename, "w") as lasers_file:
                    self.write_line(lasers_file, json.dumps(self.combined_laser_pulses, sort_keys=True, indent=4))
                print("Laser sequence written to " + os.path.join(self.dir, filename))
                
                # Call IonSim code to simulate the dynamics.
                print("Calling IonSim with num_ions=" + str(self.num_ions) + ", " + self.scan_parameter_name + "=" + str(scan_point))
                result_data = self.simulate_with_ion_sim()
                
                # Guess the plot range.
                range_offset = self.current_x_value - scan_point
                range_guess = (scan_points[0] + range_offset, scan_points[-1] + range_offset)
                
                # Adjustment for absolute frequency scans, which should be displayed in MHz.
                if self.sequence_name in self.frequency_scan_sequence_names:
                    self.current_x_value = self.current_x_value * 1e-6
                    range_guess = (range_guess[0] * 1e-6, range_guess[1] * 1e-6)

                # Record and plot the result.
                x_data = np.append(x_data, self.current_x_value)
                self.perform_state_readout(result_data, y_data)
                if self.grapher:
                    for curve_name, curve_values in sorted(y_data.items()):
                        plot_title = self.timestamp + " - " + scan_name + " - " + curve_name
                        self.grapher.plot(x_data, curve_values,
                            tab_name=PulseSequence.scan_params[scan_name][0][0],
                            plot_title=plot_title, append=True,
                            file_="", range_guess=range_guess)
        
            # Add the results to self.data and output to file.
            self.data[scan_name]["x"] = x_data
            for y_name, y_data in y_data.items():
                self.data[scan_name]["y"].append(y_data)
            filename = self.timestamp + "_results_" + scan_name + ".txt"
            with open(filename, "w") as results_file:
                self.write_line(results_file, str(self.data[scan_name]))
            print("Results written to " + os.path.join(self.dir, filename))
            
            # Visualize the most recent pulse sequence.
            if self.visualizer:
                try:
                    dds, ttl, channels = self.make_human_readable_pulses()
                    self.visualizer.plot_simulated_pulses(dds, ttl, channels)
                except:
                    self.logger.warning("Failed to plot pulse sequence visualization:" + traceback.format_exc(), exc_info=True)
            
            if scan_name in self.run_after:
                try:
                    self.run_after[scan_name]()
                except FitError:
                    self.logger.error("FitError encountered in run_after for " + scan_name, exc_info=True)
                    raise

        try:
            self.run_finally()
        except FitError:
            self.logger.error("FitError encountered in run_finally", exc_info=True)
            raise
        
        self.logger.info(self.sequence_name + " complete! Timestamp " + self.timestamp + ", output files saved to " + self.dir)

        if self.grapher:
            try:
                self.grapher.close_rpc()
            except:
                pass
        if self.visualizer:
            try:
                self.visualizer.close_rpc()
            except:
                pass
        if self.logger:
            try:
                self.logger.close_rpc()
            except:
                pass

    def perform_state_readout(self, result_data, y_data):
        # Takes the data points contained in result_data and appends them
        # to the accumulated data stored in y_data, taking into account the
        # setting of the StateReadout.readout_mode parameter. 
        def ensure_curve_exists(y_data, curve_name):
            if not curve_name in y_data:
                y_data[curve_name] = np.array([], dtype=float)
        readout_mode = self.parameter_dict["StateReadout.readout_mode"]
        if readout_mode in ["pmt", "pmtMLE", "pmt_parity", "pmt_states"]:
            # Curves are named num_dark:1, num_dark:2, ..., num_dark:self.num_ions
            for num_dark in range(1, self.num_ions + 1):
                curve_name = "num_dark:" + str(num_dark)
                ensure_curve_exists(y_data, curve_name)
                y_value = np.sum([result_value for result_name, result_value in result_data.items() if result_name.count('D') == num_dark])
                y_data[curve_name] = np.append(y_data[curve_name], y_value)
            if readout_mode == "pmt_parity":
                # TODO: Add parity curve (pmt_parity is not currently implemented)
                pass
            elif readout_mode == "pmt_states":
                # TODO: Add states (pmt_states is not currently implemented)
                pass
        elif readout_mode in ["camera"]:
            # Curves are named dark_ion:0, dark_ion:1, ...
            for ion_idx in range(self.num_ions):
                curve_name = "dark_ion:" + str(ion_idx)
                ensure_curve_exists(y_data, curve_name)
                y_value = np.sum([result_value for result_name, result_value in result_data.items() if result_name[ion_idx] == 'D'])
                y_data[curve_name] = np.append(y_data[curve_name], y_value)
        elif readout_mode in ["camera_states", "camera_parity"]:
            # Curves are named state:SS, state:SD, etc.
            for result_name, result_value in result_data.items():
                curve_name = "state:" + str(result_name)
                ensure_curve_exists(y_data, curve_name)
                y_data[curve_name] = np.append(y_data[curve_name], result_value)
            if readout_mode == "camera_parity":
                # Add parity curve
                curve_name = "parity"
                ensure_curve_exists(y_data, curve_name)
                y_value = np.sum([y_value * (-1)**curve_name.count('D') for curve_name, y_value in result_data.items()])
                y_data[curve_name] = np.append(y_data[curve_name], y_value)

    def make_human_readable_pulses(self):
        # Converts self.simulated_pulses into the "human readable" format expected
        # by the pulse sequence visualizer GUI.
        # Returns a tuple: (dds, ttl, channels)
        times = set()
        dds_names = set()
        for simulated_pulse in self.simulated_pulses:
            dds_names.add(simulated_pulse["dds_name"])
            times.add(simulated_pulse["time_on"])
            times.add(simulated_pulse["time_off"])
        dds_names = sorted(dds_names)
        times = sorted(times)
        times = times + [times[-1]*1.01] + [times[-1]*1.02]

        raw_channels = [["AdvanceDDS", 0]] + [["unused" + str(i), i] for i in range(1, 32)]
        raw_ttl = [[time, [1] + [0] * 31] for time in times]

        def freq_and_amp(dds_name, time):
            freq = 0.0
            amp = 0.0
            for simulated_pulse in self.simulated_pulses:
                if dds_name == simulated_pulse["dds_name"] and time > simulated_pulse["time_on"] and time <= simulated_pulse["time_off"]:
                    freq = simulated_pulse["freq"] / 1e6
                    amp = simulated_pulse["amp"] * (10 ** (-simulated_pulse["att"] / 20))
                    break
            return freq, amp

        raw_dds = []
        for time in times[:-1]:
            for dds_name in dds_names:
                freq, amp = freq_and_amp(dds_name, time)
                raw_dds.append([dds_name, freq, amp])

        return raw_dds, raw_ttl, raw_channels

    def setup_rpc_connections(self):
        try:
            self.logger = Client("::1", 3289, "simulation_logger")
        except:
            self.logger = logging.getLogger("** SIMULATION **")
            #self.logger.warning("Failed to connect to remote logger", exc_info=True)

        if not self.grapher:
            try:
                self.grapher = Client("::1", 3286, "rcg")
            except:
                #self.logger.warning("Failed to connect to RCG grapher", exc_info=True)
                self.grapher = None

        if not self.visualizer:
            try:
                self.visualizer = Client("::1", 3289, "pulse_sequence_visualizer")
                pass
            except:
                #self.logger.warning("Failed to connect to pulse sequence visualizer", exc_info=True)
                self.visualizer = None

    def setup_carriers(self):
        self.carrier_names = [
            "S+1/2D-3/2", "S-1/2D-5/2", "S+1/2D-1/2", "S-1/2D-3/2", "S+1/2D+1/2",
            "S-1/2D-1/2", "S+1/2D+3/2", "S-1/2D+1/2", "S+1/2D+5/2", "S-1/2D+3/2"]
        self.carrier_dict = {}
        for idx, name in enumerate(self.carrier_names):
            self.carrier_dict[name] = idx

        self.current_line_center = self.p.DriftTracker.current_line_center
        self.current_b_field = self.p.DriftTracker.current_b_field

        import sd_calculator
        current_lines = sd_calculator.get_sd_transition_energies(
            self.current_b_field, self.current_line_center)
        _list = [0.] * 10
        for carrier, frequency in current_lines:
            abs_freq = unitless(frequency)
            for i in range(10):
                if carrier == self.carrier_names[i]:
                    # for simulation, express carrier frequencies relative to line center
                    _list[i] = abs_freq - self.current_line_center
                    break
        self.carrier_values = _list

    def get_trap_frequency(self, name):
        freq = 0.
        for i in range(len(self.trap_frequency_names)):
            if self.trap_frequency_names[i] == name:
                freq = unitless(self.trap_frequency_values[i])
                return freq
        return 0.

    def make_dds(self, name):
        return SimulatedDDS(name, self)

    def setup_dds(self):
        self.dds_729G = self.make_dds("729G")
        self.dds_729L1 = self.make_dds("729L1")
        self.dds_729L2 = self.make_dds("729L2")
        self.dds_SP_729G = self.make_dds("SP_729G")
        self.dds_SP_729L1 = self.make_dds("SP_729L1")
        self.dds_SP_729L2 = self.make_dds("SP_729L2")
        self.dds_SP_729G_bichro = self.make_dds("SP_729G_bichro")
        self.dds_SP_729L1_bichro = self.make_dds("SP_729L1_bichro")
        self.dds_SP_729L2_bichro = self.make_dds("SP_729L2_bichro")
        self.dds_397 = self.make_dds("397")
        self.dds_854 = self.make_dds("854")
        self.dds_866 = self.make_dds("866")

    def setup_time_manager(self):
        class _FakeTimeManager:
            def __init__(self):
                self.time = 0.

            def _noop(self, *args, **kwargs):
                pass

            def _take_time(self, duration):
                self.time += unitless(duration)

            def _get_time(self):
                return self.time

            enter_sequential = _noop
            enter_parallel = _noop
            exit = _noop
            set_time_mu = _noop
            get_time_mu = _get_time
            get_time = _get_time
            take_time_mu = _take_time
            take_time = _take_time

        self.time_manager = _FakeTimeManager()
        core_language.set_time_manager(self.time_manager)
                
    def get_729_dds(self, name="729G", id=0):
        if id == 0:
            self.dds_729 =           self.dds_729G if name == "729G" else self.dds_729L1 if name == "729L1" else self.dds_729L2
            self.dds_729_SP =        self.dds_SP_729G if name == "729G" else self.dds_SP_729L1 if name == "729L1" else self.dds_SP_729L2
            self.dds_729_SP_bichro = self.dds_SP_729G_bichro if name == "729G" else self.dds_SP_729L1_bichro if name == "729L1" else self.dds_SP_729L2_bichro
        elif id == 1:
            self.dds_7291 =           self.dds_729G if name == "729G" else self.dds_729L1 if name == "729L1" else self.dds_729L2
            self.dds_729_SP1 =        self.dds_SP_729G if name == "729G" else self.dds_SP_729L1 if name == "729L1" else self.dds_SP_729L2
            self.dds_729_SP_bichro1 = self.dds_SP_729G_bichro if name == "729G" else self.dds_SP_729L1_bichro if name == "729L1" else self.dds_SP_729L2_bichro
        elif id == 2:
            self.dds_729 =           self.dds_729G
            self.dds_729_SP_line1 =        self.dds_SP_729G 
            self.dds_729_SP_line1_bichro = self.dds_SP_729G_bichro 
            self.dds_729_SP_line2 =        self.dds_SP_729L2 
            self.dds_729_SP_line2_bichro = self.dds_SP_729L2_bichro 

    def make_random_list(self, n, mean, std, min=None, max=None):
        #
        # Returns a list of n values pulled from a Gaussian distribution
        # with the given mean and standard deviation, in the range [min, max].
        #
        values = (std * np.random.randn(n) + mean).tolist()
        for i in range(len(values)):
            # make sure the values are between min and max
            if min is not None:
                values[i] = max(min, values[i])
            if max is not None:
                values[i] = min(max, values[i])
        return values

    def make_random_amplitudes(self, n, mean, std):
        #
        # Returns a list of n amplitudes pulled from a Gaussian distribution
        # with the given mean and standard deviation, in the range [0,1].
        #
        return self.make_random_list(n, mean, std, min=0.0, max=1.0)

    def make_random_frequencies(self, n, mean, std):
        #
        # Returns a list of n frequencies pulled from a Gaussian distribution
        # with the given mean and standard deviation, in the range [0,].
        #
        return self.make_random_list(n, mean, std, min=0.0)

    def generate_single_pass_noise_waveform(self, mean, std, freq_noise=False):
        pass
    
    def prepare_noisy_single_pass(self, freq_noise=False, id=0):
        pass

    def start_noisy_single_pass(self, phase_ref_time, freq_noise=False,
        freq_sp=80e6, amp_sp=1.0, att_sp=8.0, phase_sp=0.,
        use_bichro=False, freq_sp_bichro=80e6, amp_sp_bichro=1.0, att_sp_bichro=8.0, phase_sp_bichro=0.,
        id=0):
        # TODO: this doesn't add any noise right now.
        dds = self.dds_729_SP
        dds_bichro = self.dds_729_SP_bichro
        if id == 1:
            dds = self.dds_729_SP1
            dds_bichro = self.dds_729_SP_bichro1

        dds.set(freq_sp, amplitude=amp_sp, phase=phase_sp, ref_time_mu=phase_ref_time)
        dds.set_att(att_sp)
        dds.sw.on()
        if use_bichro:
            dds_bichro.set(freq_sp_bichro, amplitude=amp_sp_bichro, phase=phase_sp_bichro, ref_time_mu=phase_ref_time)
            dds_bichro.set_att(att_sp_bichro)
            dds_bichro.sw.on()

    def stop_noisy_single_pass(self, use_bichro=False, id=0):
        dds = self.dds_729_SP
        dds_bichro = self.dds_729_SP_bichro
        if id == 1:
            dds = self.dds_729_SP1
            dds_bichro = self.dds_729_SP_bichro1

        # Turn off the DDS outputs.
        dds.sw.off()
        if use_bichro:
            dds_bichro.sw.off()

    def prepare_pulse_with_amplitude_ramp(self, pulse_duration, ramp_duration, dds1_amp=0., use_dds2=False, dds2_amp=0.):
        self.pulse_duration = pulse_duration
        self.ramp_duration = ramp_duration
        self.dds1_amp = dds1_amp
        if use_dds2:
            self.dds2_amp = dds2_amp
        
    def execute_pulse_with_amplitude_ramp(self, dds1_att=8.0, dds1_freq=0.,
                                          use_dds2=False, dds2_att=8.0, dds2_freq=0.):
        # TODO: currently this doesn't actually do any ramping
        self.dds_729.set(dds1_freq, self.dds1_amp)
        self.dds_729.set_att(dds1_att)
        self.dds_729.sw.on()
        if use_dds2:
            self.dds_7291.set(dds2_freq, self.dds2_amp)
            self.dds_7291.set_att(dds2_att)
            self.dds_7291.sw.on()

        self.time_manager.take_time(self.pulse_duration)

        self.dds_729.sw.off()
        if use_dds2:
            self.dds_7291.sw.off()

    def add_subsequence(self, subsequence):
        self._set_subsequence_defaults(subsequence)
        subsequence.run = subsequence.subsequence
        try:
            subsequence.add_child_subsequences(self)
        except AttributeError:
            pass
        return subsequence

    def _set_subsequence_defaults(self, subsequence):
        d = subsequence.__dict__
        kwargs = dict()
        for key, value in d.items():
            if type(value) == str:
                try:
                    c, v = value.split(".")
                except AttributeError:
                    continue
                except ValueError:
                    continue
                try:
                    pv_collection = self.p[c]
                except KeyError:
                    continue # ignore, could be an unrelated class attribute
                try:
                    pv_value = pv_collection[v]
                except KeyError:
                    raise Exception("Failed to find parameter: " + value)
                try:
                    pv_value = float(pv_value)
                except:
                    pass
                kwargs[key] = pv_value
        for key, value in kwargs.items():
            setattr(subsequence, key, value)
            
    def get_offset_frequency(self, name):
        return 0.

    def calc_frequency(self, line, detuning=0.,
                    sideband="", order=0., dds="", bound_param=""):
        freq = detuning
        abs_freq = 0.
        line_set = False
        sideband_set = True if sideband == "" else False
        for i in range(10):
            if line == self.carrier_names[i]:
                freq += self.carrier_values[i]
                line_set = True
            if sideband != "" and i <= len(self.trap_frequency_names) - 1:
                if sideband == self.trap_frequency_names[i]:
                    freq += self.trap_frequency_values[i] * order
                    sideband_set = True
            if line_set and sideband_set:
                abs_freq = freq
                break

        # Plot absolute frequencies for frequency scans.
        if self.sequence_name in self.frequency_scan_sequence_names:
            self.current_x_value = abs_freq + self.current_line_center

        return freq

    def get_variable_parameter(self, name):
        # All params are fixed in simulation mode for now
        return getattr(self, name)

    def load_parameter_vault(self):
        # Grab parametervault params:
        import simulated_parameter_vault as p
        collections = p.get_collections()
        D = dict()
        for collection in collections:
            d = dict()
            names = p.get_parameter_names(collection)
            for name in names:
                try:
                    param = unitless(p.get_parameter([collection, name]))
                    d[name] = param
                    setattr(self, collection + "_" + name, param)
                except:
                    # broken parameter
                    continue
            D[collection] = d
        return edict(D)

    def run_initially(self):
        # individual pulse sequences should override this
        pass

    def sequence(self):
        # individual pulse sequences should override this
        raise NotImplementedError

    def run_finally(self):
        # individual pulse sequences should override this
        pass
