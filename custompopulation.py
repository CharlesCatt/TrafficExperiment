"""Implements the core evolution algorithm."""
# from __future__ import print_function

from neat.reporting import ReporterSet
from neat.math_util import mean
from neat.six_util import iteritems, itervalues
import time


class CompleteExtinctionException(Exception):
    pass


class CustomPopulation(object):
    """
    This class implements the core evolution algorithm:
        1. Evaluate fitness of all genomes.
        2. Check to see if the termination criterion is satisfied; exit if it is.
        3. Generate the next generation from the current population.
        4. Partition the new generation into species based on genetic similarity.
        5. Go to 1.
    """

    def __init__(self, config, initial_state=None):
        self.reporters = ReporterSet()
        self.config = config
        stagnation = config.stagnation_type(config.stagnation_config, self.reporters)
        self.reproduction = config.reproduction_type(config.reproduction_config,
                                                     self.reporters,
                                                     stagnation)
        if config.fitness_criterion == 'max':
            self.fitness_criterion = max
        elif config.fitness_criterion == 'min':
            self.fitness_criterion = min
        elif config.fitness_criterion == 'mean':
            self.fitness_criterion = mean
        elif not config.no_fitness_termination:
            raise RuntimeError(
                "Unexpected fitness_criterion: {0!r}".format(config.fitness_criterion))

        if initial_state is None:
            # Create a population from scratch, then partition into species.
            self.population = [self.reproduction.create_new(config.genome_type,
                                                           config.genome_config,
                                                           config.pop_size),
                                self.reproduction.create_new(config.genome_type,
                                                           config.genome_config,
                                                           config.pop_size),
                                self.reproduction.create_new(config.genome_type,
                                                           config.genome_config,
                                                           config.pop_size)]

            self.species = [config.species_set_type(config.species_set_config, self.reporters),
                            config.species_set_type(config.species_set_config, self.reporters),
                            config.species_set_type(config.species_set_config, self.reporters)]
            self.generation = 0
            self.species[0].speciate(config, self.population[0], self.generation)
            self.species[1].speciate(config, self.population[1], self.generation)
            self.species[2].speciate(config, self.population[2], self.generation)
        else:
            self.population, self.species, self.generation = initial_state

        self.best_genome = [None, None, None]

    def add_reporter(self, reporter):
        self.reporters.add(reporter)

    def remove_reporter(self, reporter):
        self.reporters.remove(reporter)

    def run(self, fitness_function, n=None):
        """
        Runs NEAT's genetic algorithm for at most n generations.  If n
        is None, run until solution is found or extinction occurs.

        The user-provided fitness_function must take only two arguments:
            1. The population as a list of (genome id, genome) tuples.
            2. The current configuration object.

        The return value of the fitness function is ignored, but it must assign
        a Python float to the `fitness` member of each genome.

        The fitness function is free to maintain external state, perform
        evaluations in parallel, etc.

        It is assumed that fitness_function does not modify the list of genomes,
        the genomes themselves (apart from updating the fitness member),
        or the configuration object.
        """

        if self.config.no_fitness_termination and (n is None):
            raise RuntimeError("Cannot have no generational limit with no fitness termination")

        k = 0
        while n is None or k < n:
            k += 1

            self.reporters.start_generation(self.generation)

            # Evaluate all genomes using the user-provided function.
            fitness_function(list(iteritems(self.population[0])), list(iteritems(self.population[1])), list(iteritems(self.population[2])), self.config, self.generation)


            for i in range(len(self.population)):
                # Gather and report statistics.
                best = None
                for g in itervalues(self.population[i]):
                    if best is None or g.fitness > best.fitness:
                        best = g
                self.reporters.post_evaluate(self.config, self.population[i], self.species[i], best)

                # Track the best genome ever seen.
                if self.best_genome[i] is None or best.fitness > self.best_genome[i].fitness:
                    self.best_genome[i] = best

                if not self.config.no_fitness_termination:
                    # End if the fitness threshold is reached.
                    fv = self.fitness_criterion(g.fitness for g in itervalues(self.population[i]))
                    if fv >= self.config.fitness_threshold:
                        self.reporters.found_solution(self.config, self.generation, best)
                        break

                # Create the next generation from the current generation.
                self.population[i] = self.reproduction.reproduce(self.config, self.species[i],
                                                              self.config.pop_size, self.generation)

                # Check for complete extinction.
                if not self.species[i].species:
                    self.reporters.complete_extinction()

                    # If requested by the user, create a completely new population,
                    # otherwise raise an exception.
                    if self.config.reset_on_extinction:
                        self.population[i] = self.reproduction.create_new(self.config.genome_type,
                                                                       self.config.genome_config,
                                                                       self.config.pop_size)
                    else:
                        raise CompleteExtinctionException()

                # Divide the new population into species.
                self.species[i].speciate(self.config, self.population[i], self.generation)

                self.reporters.end_generation(self.config, self.population[i], self.species[i])

            self.generation += 1

        if self.config.no_fitness_termination:
            self.reporters.found_solution(self.config, self.generation, self.best_genome[0])

        return self.best_genome
