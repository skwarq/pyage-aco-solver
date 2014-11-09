from random import Random

from aco_solver.sequential.ants import ClassicAnt
from aco_solver.sequential.commons import Path


class AntColony:
    def __init__(self, graph, ants_count, iterations, alpha, beta):
        self.graph = graph
        self.ants_count = ants_count
        self.iterations = iterations
        self.best_path = None
        self.ants = []
        self.random = Random()
        self.initialize_ants(alpha, beta)

    def start_simulation(self):
        for i in range(self.iterations):
            found_new_best_solution = False

            # try to find better solution
            for ant in self.ants:
                new_path = ant.find_path()

                if self.best_path is None or new_path < self.best_path:
                    found_new_best_solution = True
                    self.best_path = new_path

            self.graph.update_pheromones(self.ants)

            if found_new_best_solution:
                print 'Iteration: %s Best: %s' % (i + 1, self.best_path.distance)

        print 'Best: {}'.format(str(self.best_path))

    def initialize_ants(self, alpha, beta):
        for i in range(self.ants_count):
            path = self.__generate_random_path(self.graph.cities)

            ant = ClassicAnt(self.graph, path, alpha, beta)
            self.ants.append(ant)
            print '{} {}: init distance {}'.format(type(ant).__name__, i + 1, ant.path.distance)

    def __generate_random_path(self, available_cities):
        shuffled_cities = list(available_cities)
        self.random.shuffle(shuffled_cities)

        start_city = shuffled_cities.pop(0)

        connection_list = []
        present_city = start_city

        while shuffled_cities:
            next_city = shuffled_cities.pop(0)
            connection_list.append(present_city.find_connection_to_city(next_city))

            present_city = next_city

        return Path(start_city, connection_list)
