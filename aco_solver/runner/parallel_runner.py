from multiprocessing import Process, Pipe
from optparse import OptionParser
import os
import pickle
import sys

from aco_solver.algorithm import graph
from aco_solver.algorithm.results import ResultConverter
from aco_solver.utils.cities_reader import CitiesReader
from aco_solver.algorithm.ant_colony import ControlSampleColony, HighAltercentricityCondition, \
    LowAltercentricityCondition, \
    ClassicAntColony
from aco_solver.algorithm.graph import Graph


def start_simulation(ants_count, iterations, distance_matrix, positions, rho, q, type, alpha, beta, pipe):
    colony = None

    if type == "ca":  # Classical Ants
        graph = Graph(distance_matrix, positions, rho, q, 0.01)
        colony = ClassicAntColony(ants_count, graph, alpha, beta, iterations)
    elif type == "cs":  # Control Sample
        graph = create_graph_with_default_pheromone_value(distance_matrix, positions, rho, q)
        colony = ControlSampleColony(ants_count, graph, iterations)
    elif type == "ha":  # High Altercentricity Condition
        graph = create_graph_with_default_pheromone_value(distance_matrix, positions, rho, q)
        colony = HighAltercentricityCondition(ants_count, graph, iterations)
    elif type == "la":  # Low Altercentricity Condition
        graph = create_graph_with_default_pheromone_value(distance_matrix, positions, rho, q)
        colony = LowAltercentricityCondition(ants_count, graph, iterations)

    result = colony.start_simulation()
    # to avoid problems with deep recursion while serializing large objects with pickle
    sys.setrecursionlimit(30000)
    pipe.send(pickle.dumps(result))


def create_graph_with_default_pheromone_value(cities_distances, positions, rho, q):
    return Graph(cities_distances, positions, rho, q, (1.0 / graph.compute_average_distance(cities_distances)) ** 2.0)


def main():
    usage = "usage: %prog [options] number_of_ants iterations dataset_name"

    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--type", default="cs", type="string", dest="type")
    parser.add_option("-a", "--alpha", default="3.0", type="float", help="pheromone influence [default: %default]",
                      dest="alpha")
    parser.add_option("-b", "--beta", default="2.0", type="float", help="distance influence [default: %default]",
                      dest="beta")
    parser.add_option("-r", "--rho", default="0.01", type="float",
                      help="pheromone evaporation coefficient [default: %default]",
                      dest="rho")
    parser.add_option("-q", "--q", default="2.0", type="float", help="pheromone deposit factor [default: %default]",
                      dest="q")
    parser.add_option("-p", "--p", default="1", type="int", help="number of processes [default: %default]",
                      dest="p")

    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error("incorrect number of arguments")

    ants_count = int(args[0])
    iterations = int(args[1])
    cities_filename = args[2]

    cities_reader = CitiesReader(cities_filename)
    cities_reader.read_file()
    distance_matrix = cities_reader.create_distance_matrix()
    positions = cities_reader.get_positions()

    print "File:", cities_filename, "Type:", options.type, "Ants:", ants_count, "Iterations:", iterations

    processes = []
    pipes = []
    # start concurrent processes
    for i in range(options.p):
        pipes.append(Pipe(False))
    for i in range(options.p):
        processes.append(Process(target=start_simulation, args=(
            ants_count, iterations, distance_matrix, positions, options.rho, options.q, options.type, options.alpha,
            options.beta, pipes[i][1],)))
    for i in range(options.p):
        processes[i].start()

    best_result = None
    result_list = []
    for i in range(options.p):
        present_result = pickle.loads(pipes[i][0].recv())

        if best_result is None or present_result.best_path < best_result.best_path:
            best_result = present_result

        result_list.append(present_result)

    output_directory_name = "outputs/"
    if not os.path.exists(output_directory_name):
        os.makedirs(output_directory_name)

    for i in range(len(result_list)):
        f = open(output_directory_name + cities_filename + '_'
                 + str(ants_count) + '_'
                 + str(iterations) + '_'
                 + options.type + '_' + str(i) + '.dat', 'w')
        f.write(str(result_list[i]))
        f.close()

    f = open(output_directory_name + cities_filename + '_'
             + str(ants_count) + '_'
             + str(iterations) + '_'
             + options.type + '_best.dat', 'w')
    f.write(str(best_result))
    f.close()

    f = open(output_directory_name + cities_filename + '_'
             + str(ants_count) + '_'
             + str(iterations) + '_'
             + options.type + '_fitness.dat', 'w')
    f.write(best_result.fitness_to_string())
    f.close()

    f = open(output_directory_name + cities_filename + '_'
             + str(ants_count) + '_'
             + str(iterations) + '_'
             + options.type + '_path.dat', 'w')
    f.write(str(best_result.best_path.get_points_gnuplot()))
    f.close()

    f = open(output_directory_name + cities_filename + '_'
             + str(ants_count) + '_'
             + str(iterations) + '_'
             + options.type + '_avg.dat', 'w')
    f.write(ResultConverter(result_list).covert_to_avg_results())
    f.close()

    for i in range(options.p):
        processes[i].join()


if __name__ == "__main__":
    main()