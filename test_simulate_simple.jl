using IonSim
using QuantumOptics
using DifferentialEquations
using Distributions
using DataStructures

num_ions = 1
b_field = 3.799953549
carrier_frequency = 2127405.1614560783


for duration in 0:5:50  #0:2e-6:50e-6

    #############################################
    # Create and load the ions
    S = ["S-1/2", "S+1/2"]
    D = ["D-5/2", "D-3/2", "D-1/2" ,"D+1/2", "D+3/2", "D+5/2"]
    ions = Array{Ca40}(undef, num_ions)
    for i = 1:num_ions
        ions[i] = Ca40([S; D])
    end

    axial_frequency = 900e3
    radial_frequency_1 = 1.3e6
    radial_frequency_2 = 1.6e6
    chain = LinearChain(
        ions=ions,
        com_frequencies=(x=radial_frequency_1, y=radial_frequency_2, z=axial_frequency),
        vibrational_modes=(;z=[1]))

    #############################################
    # Set up the lasers and the trap
    laser = Laser(
        k=(x̂ + ẑ)/√2,
        ϵ=(x̂ - ẑ)/√2,
        Δ=carrier_frequency + axial_frequency,
        pointing=[(1, 1.)],
    )

    trap = Trap(configuration=chain, B=b_field*1e-4, Bhat=ẑ, δB=0, lasers=[laser])
    mode = trap.configuration.vibrational_modes.z[1]

    #laser.Δ = transition_frequency(trap, 1, ("S-1/2", "D-1/2")) + axial_frequency
    global_beam!(trap, laser)

    simulation_start_time = 0
    simulation_stop_time = duration
    simulation_tstops = [simulation_start_time, simulation_stop_time]
    simulation_tspan = range(simulation_start_time - 1e-3, simulation_stop_time + 1e-3, length=2)

    #############################################
    # Set up the time-dependent E-field
    intensity_factor = 10^(-0.5) # this corresponds to pi time 3 μs
    pi_min = 3e-6
    amp = 1.0
    att = 6.0
    
    function step_interval(t, t_begin, t_end)
        t >= t_begin && t < t_end ? 1 : 0
    end

    t_pi = pi_min * sqrt(intensity_factor / (amp * 10^(-1.5 * att / 10)))
    E = Efield_from_pi_time(t_pi, trap.Bhat, laser, ions[1], ("S-1/2", "D-1/2"))
    laser.E = t -> E * step_interval(t, simulation_start_time, simulation_stop_time)
        
    #############################################
    # Run the simulation
    initial_state = ionstate(trap, "S-1/2")
    h = hamiltonian(trap, lamb_dicke_order=1, timescale=1e-6, rwa_cutoff=1e5)
    @time tout, solution = timeevolution.schroedinger_dynamic(
        simulation_tspan,
        tensor(initial_state, fockstate(mode, 0)),
        h,
        callback=PresetTimeCallback(simulation_tstops, integrator -> return)
        );
    solution = solution[end]

    #############################################
    # Print the result
    function project(solution, states...)
        real.(expect(ionprojector(trap, states...), solution))
    end

    result = Dict(
        "S" => sum([project(solution, state) for state=S]),
        "D" => sum([project(solution, state) for state=D]),
        )

    println("Results: $result")

end
