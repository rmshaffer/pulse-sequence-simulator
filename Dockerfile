FROM continuumio/miniconda3

# Install Julia:
ARG julia_version=1.5.4
RUN apt-get update && apt-get install -y curl
RUN curl https://raw.githubusercontent.com/JuliaCI/install-julia/master/install-julia.sh | sed -E "s/\bsudo +//g" | bash -s $julia_version
ENV PATH="/usr/local/bin/julia:${PATH}"

# Demonstrate that julia is available on the path:
RUN echo "Make sure Julia is installed:"
RUN julia -e "println(VERSION)"

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

# Install necessary Julia packages:
RUN julia -e 'using Pkg; Pkg.update()' && \
    julia -e 'using Pkg; Pkg.add(PackageSpec(url="https://github.com/HaeffnerLab/IonSim.jl.git"))' && \
    julia -e 'using Pkg; Pkg.add("QuantumOptics")' && \
	julia -e 'using Pkg; Pkg.add("DifferentialEquations")' && \
    julia -e 'using Pkg; Pkg.add("Distributions")' && \
    julia -e 'using Pkg; Pkg.add("DataStructures")' && \
    julia -e 'using Pkg; Pkg.add("IJulia")' && \
    julia -e 'using Pkg; Pkg.add("PyPlot")' && \
    # Update everything
    julia -e 'using Pkg; Pkg.update()' && \
    # Precompile Julia packages
    julia -e 'using IonSim' && \
    julia -e 'using QuantumOptics' && \
    julia -e 'using DifferentialEquations' && \
    julia -e 'using Distributions' && \
	julia -e 'using DataStructures' && \
    julia -e 'using IJulia' && \
	julia -e 'using PyPlot'

# Install and configure pyjulia:
RUN pip install julia
RUN python -c 'from julia import install; install()'
