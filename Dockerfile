FROM continuumio/miniconda3

# Install Julia:
ARG julia_version=1.5.4
RUN curl https://raw.githubusercontent.com/JuliaCI/install-julia/master/install-julia.sh | sed -E "s/\bsudo +//g" | bash -s $julia_version

# Create conda environment:
RUN conda config --prepend channels https://conda.m-labs.hk/artiq
RUN conda config --append channels conda-forge
RUN conda create -n artiq artiq notebook matplotlib easydict

# Make RUN commands use the new environment:
RUN echo "conda activate artiq" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

# Demonstrate the environment is activated:
RUN echo "Make sure artiq is installed:"
RUN python -c "import artiq"

# Install and configure pyjulia:
RUN pip install julia
RUN python -c 'from julia import install; install()'

# Install necessary Julia packages:
RUN julia -e 'Pkg.init()' && \
    julia -e 'Pkg.update()' && \
    julia -e 'Pkg.add(PackageSpec(url="https://github.com/HaeffnerLab/IonSim.jl.git"))' && \
    julia -e 'Pkg.add("QuantumOptics")' && \
	julia -e 'Pkg.add("DifferentialEquations")' && \
    julia -e 'Pkg.add("Distributions")' && \
    julia -e 'Pkg.add("DataStructures")' && \
    julia -e 'Pkg.add("IJulia")' && \
    julia -e 'Pkg.add("PyPlot")' && \
    # Update everything
    julia -e 'Pkg.update()' && \
    # Precompile Julia packages
    julia -e 'using IonSim' && \
    julia -e 'using QuantumOptics' && \
    julia -e 'using DifferentialEquations' && \
    julia -e 'using Distributions' && \
	julia -e 'using DataStructures' && \
    julia -e 'using IJulia' && \
	julia -e 'using PyPlot'
