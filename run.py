#!/usr/local/bin/python3

import os
import sys
import optparse
import neat
import custompopulation
import simulationcontroller
import logging



# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars
import traci


log = logging.Logging(logging.Level.WARNING.value, logging.Level.DEBUG.value, "experiment_output")

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options



def score_genomes(pop1, pop2, pop3, config, gen):
    for i in range(max(len(pop1), len(pop2), len(pop3))):

        # in the case of species stagnation, any number of members may be removed from a population
        # so we just re-use and re-score genomes in that case, not counting their first score
        pops = {}
        pops['WC'] = pop1[i % len(pop1)][1]
        pops['CC'] = pop2[i % len(pop2)][1]
        pops['EC'] = pop3[i % len(pop3)][1]
        nets = {'WC': None, 'CC': None, 'EC': None}

        # initialise new simulation
        sim = simulationcontroller.SimulationController(log)
        # if gen % 10 == 0 and i == 0:
        #     sim.start('gui')
        # else:
        sim.start()

        for pop, net in zip(pops, nets):


            # initialise fitness and the networks
            pops[pop].fitness = 0.0
            nets[net] = neat.nn.FeedForwardNetwork.create(pops[pop], config)


        # traci starts sumo as a subprocess and then this script connects and runs
        # traci.start([sumoBinary, "-c", "corridor.sumocfg",
        #                          "--tripinfo-output", "tripinfo.xml"])
        scores = sim.run(nets)
        for net, score in zip(nets, scores):
            if scores[score] == None:
                print('ERROR: Score is None, setting to -1500 to keep things running...')
                pops[pop].fitness = -1500
            else:
                pops[net].fitness = scores[score]




# main entry point
if __name__ == "__main__":

    # log = logger.Logger(1, 5, "experiment_output")

    i = 0
    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         "neat_configuration")


    # Add a stdout reporter to show progress in the terminal.
    pop = custompopulation.CustomPopulation(config)
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(5))

    best = pop.run(score_genomes, 1)
    print(best)


    winners = {'WC': best[0], 'CC': best[1], 'EC': best[2]}

    nets = {'WC': None, 'CC': None, 'EC': None}

    # initialise new simulation
    sim = simulationcontroller.SimulationController(log)
    # if gen % 10 == 0 and i == 0:
    #     sim.start('gui')
    # else:
    sim.start('gui')

    for pop, net in zip(winners, nets):
        # initialise fitness and the networks
        nets[net] = neat.nn.FeedForwardNetwork.create(winners[pop], config)

    scores = sim.run(nets)
    print('scores:')
    print(scores)

    # print(pop.population)
