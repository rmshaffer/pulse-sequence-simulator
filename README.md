# pulse-sequence-simulator
Utilities for simulating ARTIQ pulse sequences for trapped-ion devices using IonSim.jl.

In particular, this is designed to simulating the behavior of the ARTIQ pulse sequences used in Haeffner Lab at UC Berkeley. These experimental pulse sequences can be found at:  
https://github.com/HaeffnerLab/artiq-work-lattice

## Installing via Docker (recommended)

The Python and Julia prerequisites for this repo are packaged into a Docker image here:  
https://hub.docker.com/r/rmshaffer/pulse-sequence-simulator

Installing via Docker is much easier than manual installation, particularly because Docker is a fully containerized environment, which means you don't have to worry about affecting any other Python or Julia installations you already have on your machine.

### 1. Install Docker Desktop
First, install Docker Desktop, if you don't already have it:
https://www.docker.com/products/docker-desktop

### 2. Launch an instance of the Docker image
Then, from a terminal, run the following commands to launch an instance of the Docker image:
```
docker pull rmshaffer/pulse-sequence-simulator
docker run -it -p 8888:8888 rmshaffer/pulse-sequence-simulator
```

This should bring you to a bash shell inside your container, something like:  
`(artiq) root@6ee27adf04cf:/repo#`

### 3. Launch Jupyter Notebook from inside the container
Now, from that bash shell, simply run this command to launch a Jupyter Notebook server:
```
jupyter notebook --ip 0.0.0.0 --port 8888 --no-browser --allow-root
```

This should produce output like:
```
    To access the notebook, open this file in a browser:
        file:///root/.local/share/jupyter/runtime/nbserver-19-open.html
    Or copy and paste one of these URLs:
        http://6ee27adf04cf:8888/?token=292807c7badcf0db5957a6caa5f691fa970b286db9ece62e
     or http://127.0.0.1:8888/?token=292807c7badcf0db5957a6caa5f691fa970b286db9ece62e
```

Open that `http://127.0.0.1:8888/?token=...` link in your browser and you should see the familiar Jupyter UI:

![image](https://user-images.githubusercontent.com/3620100/130338466-a4d2fcff-5fb3-421b-a2b0-a93bbf887946.png)

## Installing locally

Installing locally can be quite time-consuming and error-prone, especially if you are not familiar with Julia and PyJulia. But depending on what you are doing, you may prefer to have a local installation.

If you want to try, the detailed setup steps (for Linux, although translating for Windows/Mac should be straightforward) can be found in the [Dockerfile](./Dockerfile). In general, the steps are:
1. [Install Julia](https://julialang.org/downloads/) and ensure that the `julia` command is on your system path.
2. [Install Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you don't already have conda on your system.
3. Create a conda environment and install the [required conda packages](https://github.com/rmshaffer/pulse-sequence-simulator/blob/d572d61b869c4d31da48753d229fb3be4ffa7caf/Dockerfile#L14-L17).
4. Run `conda activate artiq` to activate the new environment (where `artiq` is the name of the new environment you just created).
5. Install and precompile the [required Julia packages](https://github.com/rmshaffer/pulse-sequence-simulator/blob/d572d61b869c4d31da48753d229fb3be4ffa7caf/Dockerfile#L27-L45).
6. [Install and configure `pyjulia`](https://github.com/rmshaffer/pulse-sequence-simulator/blob/d572d61b869c4d31da48753d229fb3be4ffa7caf/Dockerfile#L47-L49) for use with your local Julia installation.
7. Clone this repo and `cd` into the cloned directory.
8. (Linux/Mac only) [Pre-compile a Julia sysimage](https://github.com/rmshaffer/pulse-sequence-simulator/blob/d572d61b869c4d31da48753d229fb3be4ffa7caf/Dockerfile#L55-L56) so that PyCall will work properly. Note that the code in this repo expects the sysimage to be named `sys.so` in the root folder of the cloned repo.

That should be it. To test your installation, run the test script included in this repo:
```
python ./test_simulated_pulse_sequence.py
```
If this completes with no errors and outputs some results, you should be good to go.
