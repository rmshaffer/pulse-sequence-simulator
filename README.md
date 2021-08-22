# pulse-sequence-simulator
Utilities for simulating ARTIQ pulse sequences for trapped-ion devices using IonSim.jl.

## Installing via Docker

The Python and Julia prerequisites for this repo are packaged into a Docker image here:  
https://hub.docker.com/r/rmshaffer/pulse-sequence-simulator

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

