import os
import sys
import optparse
import neat
import random

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options

class SimulationController(object):
    """docstring for SimulationController."""

    def __init__(self, log):
        super(SimulationController, self).__init__()
        self.log = log
        # intersection parameter template:
        # ~~~~~
        # num_cars:     numcars that have gone through the intersection in the last phase
        # av_speed:     average speed of cars through the intersection in the last phase
        # N_dets_time:  North detectors' measurement of the time since a car arrived at the intersection
        # S_dets_time:  South "
        # E_dets_time:  East  "
        # W_dets_time:  West  "
        # N_car_flow:   North lanes' allowed movement, indicating the number of open connections allowed at the current time
        # S_car_flow:   South "
        # E_car_flow:   East  "
        # W_car_flow:   West  "
        # yellow_phase: True/False if this phase is a 'yellow' phase, which are typically shorter
        # ~~~~~
        p = {'num_cars': 0, 'av_speed' : 0, 'N_dets_time': 0,'S_dets_time': 0,'E_dets_time': 0,'W_dets_time': 0, 'N_car_flow': 0, 'S_car_flow': 0, 'E_car_flow': 0, 'W_car_flow': 0, 'yellow_phase': 0}
        self.intersection_parameters = {'CC': p, 'EC': p, 'WC': p}
        self.intersection_speeds = {'CC': [], 'EC': [], 'WC': []}

        self.penalties = { 'CC': 0, 'EC': 0, 'WC': 0 }

    def start(self, gui='nogui'):
        options = get_options()

        # check binary
        if gui=='nogui':
            sumoBinary = checkBinary('sumo')
        else:
            sumoBinary = checkBinary('sumo-gui')
        traci.start([sumoBinary, "--start", "-c", "corridor.sumocfg", "--tripinfo-output", "tripinfo.xml"])

    #

    def get_params(self):
        for index in self.intersection_parameters:
            speed_array = self.intersection_speeds[index]
            av_speed = 0
            if len(speed_array) != 0:
                av_speed = sum(speed_array)/len(speed_array)
            self.intersection_parameters[index]['av_speed'] = av_speed


            flow = self.get_flow(index)
            self.intersection_parameters[index]['N_car_flow'] = flow[0]
            self.intersection_parameters[index]['S_car_flow'] = flow[1]
            self.intersection_parameters[index]['E_car_flow'] = flow[2]
            self.intersection_parameters[index]['W_car_flow'] = flow[3]

            self.intersection_parameters[intersection]['yellow_phase'] = 0
            if 'y' in traci.trafficlight.getRedYellowGreenState(intersection):
                self.intersection_parameters[intersection]['yellow_phase'] = 1

        return self.intersection_parameters

    def get_params_for(self, intersection, source):
        speed_array = self.intersection_speeds[intersection]


        av_speed = 0
        if len(speed_array) != 0:
            av_speed = sum(speed_array)/len(speed_array)
        self.intersection_parameters[intersection]['av_speed'] = av_speed

        flow = self.get_flow(intersection)
        self.intersection_parameters[intersection]['N_car_flow'] = flow[0]
        self.intersection_parameters[intersection]['S_car_flow'] = flow[1]
        self.intersection_parameters[intersection]['E_car_flow'] = flow[2]
        self.intersection_parameters[intersection]['W_car_flow'] = flow[3]

        self.intersection_parameters[intersection]['yellow_phase'] = 0
        if 'y' in traci.trafficlight.getRedYellowGreenState(intersection):
            self.intersection_parameters[intersection]['yellow_phase'] = 1


        self.intersection_parameters[intersection]['is_timeout'] = 1 if source == 'timeout' else 0
        self.intersection_parameters[intersection]['is_inductor'] = 1 if source == 'inductor' else 0
        # self.intersection_parameters[intersection]['is_pedestrian'] = 1 if source == 'pedestrian' else 0




        return list(self.intersection_parameters[intersection].values())



    # hard coding these values for now, bigger model will need more sophisticated methods
    # far out, if i use getControlledLinks it shows it in the traffic state thing order
    def get_flow(self, intersection):
        ryg_state = traci.trafficlight.getRedYellowGreenState(intersection)
        phase = traci.trafficlight.getPhase(intersection)

        # print(intersection + " " + str(phase))
        # returned string in format:
        #               N, S, E, W:
        if intersection == 'CC':
            if phase == 0:
                return [0, 0, 3, 2]
            elif phase == 1:
                return [0, 0, 0, 1]
            elif phase == 2:
                return [2, 0, 1, 1]
            elif phase == 3:
                return [0, 0, 1, 0]
        elif intersection == 'EC':
            if phase == 0:
                return [0, 0, 4, 4]
            elif phase == 1:
                return [0, 0, 0, 0]
            elif phase == 2:
                return [4, 4, 0, 0]
            elif phase == 3:
                return [0, 0, 0, 0]
        elif intersection == 'WC':
            if phase == 0:
                return [0, 0, 4, 4]
            elif phase == 1:
                return [0, 0, 4, 0]
            elif phase == 2:
                return [1, 0, 4, 0]
            elif phase == 3:
                return [1, 0, 0, 0]
            elif phase == 4:
                return [4, 4, 0, 0]
            elif phase == 5:
                return [0, 1, 0, 0]
            elif phase == 6:
                return [0, 1, 0, 4]
            elif phase == 7:
                return [0, 0, 0, 4]




    def get_duration(self, params, net):
        output = net.activate(params)
        change = output[0]
        duration = output[1]

        self.log.info('next duration, from {} to {}'.format(duration, duration * 98.5 + 1.5))
        # linear mapping of number between 0 and 1
        # to number between 1.5 and 100.
        # 50% chance of changing if output is truly random
        return (round(change), duration * 98.5 + 1.5)

    def light_trigger(self, light, net, source):

        change, duration = self.get_duration(self.get_params_for(light, source), net)

        # add the change option to the current light phase number
        # means decision to change as 0 won't change phase,
        # and 1 means change
        traci.trafficlight.setPhase(light, traci.trafficlight.getPhase(light) + change % len(traci.trafficlight.getCompleteRedYellowGreenDefinition(light)))
        traci.trafficlight.setPhaseDuration(light, duration)






    def run(self, networks):
        step = 0

        car_number = 0

        vehicle_last_intersection_step = {}
        vehicle_last_intersection_id = {}

        # maybe for measuring overall performance of system
        vehicle_number_of_stops = {}
        vehicle_trip_time = {}
        vehicle_is_stopped = {}
        vehicle_stop_time = {}

        lights = traci.trafficlight.getIDList()
        detectors = traci.inductionloop.getIDList()

        random.seed(a=1234) # seed for replicability

        # while traci.simulation.getMinExpectedNumber() > 0:
        while True:

            if step > 1200:
                # apply penalties to instersections
                vehs = traci.vehicle.getIDList()

                for veh in vehs: # usually just one here
                    intersection = traci.vehicle.getNextTLS(veh)
                    # print(intersection)
                    # update penalties and parameters
                    if len(intersection) != 0:
                        self.penalties[intersection[0][0]] -= step - vehicle_last_intersection_step[veh]
                        self.penalties[intersection[0][0]] -= vehicle_number_of_stops[veh]
                        vehicle_last_intersection_id[veh] = detector


                # finish simulation
                break

            # generate cars before time step
            if step % 20 == 0:
                cars_generated = random.randint(10,40)
                for car in range(cars_generated):
                    gen_number = random.random()
                    # route 0 and 1 are more likely:
                    if gen_number < 0.35:
                        traci.vehicle.add('vehicle_'+str(car_number), 'route_0')
                    elif gen_number < 0.7:
                        traci.vehicle.add('vehicle_'+str(car_number), 'route_1')
                    else:
                        # choose other random route 30% of the time
                        route_number = random.randint(2, 13)
                        traci.vehicle.add('vehicle_'+str(car_number), 'route_'+str(route_number))
                    car_number += 1




            # simulation step
            traci.simulationStep()




            # initialise vehicle time tracking for new vehicles for use in scoring intersections
            vehicles = traci.vehicle.getIDList()
            for vehicle in vehicles:

                # initialise item in to dicts
                if vehicle not in vehicle_is_stopped:
                    vehicle_is_stopped[vehicle] = 0
                    vehicle_number_of_stops[vehicle] = 0
                    vehicle_stop_time[vehicle] = 0

                # record stop
                if traci.vehicle.isStopped(vehicle) == True and vehicle_is_stopped[vehicle] != 0:
                    vehicle_is_stopped[vehicle] = 1
                    vehicle_number_of_stops[vehicle] += 1
                    vehicle_stop_time[vehicle] = step

                # reset stop status
                if traci.vehicle.isStopped(vehicle) == False and vehicle_is_stopped[vehicle] != 0:
                    vehicle_is_stopped[vehicle] = 0

                if vehicle_last_intersection_step.get(vehicle) == None:
                    vehicle_last_intersection_step[vehicle] = step
                    vehicle_last_intersection_id[vehicle] = None

            #

            # apply penalty to upcoming intersection if the deceleration exceeds the defined emergency deceleration
            stopping_vehicles = traci.simulation.getEmergencyStoppingVehiclesIDList()
            # if len(stopping_vehicles) > 0:
            for vehicle in stopping_vehicles:
                self.log.warning('~~~~~ noticed emergency stop from vehicle {}, penalising {}'.format(vehicle, traci.vehicle.getNextTLS(vehicle)[0][0]))
                self.penalties[traci.vehicle.getNextTLS(vehicle)[0][0]] -= 20



            # can't penalise the right intersection here
            #
            # teleporting_vehicles = traci.simulation.getStartingTeleportIDList()
            # for vehicle in teleporting_vehicles:
            #     print('next intersections: \n{}'.format(traci.vehicle.getNextTLS(vehicle)))
            #     print('~~~~~ noticed teleport from vehicle {}, penalising {}'.format(vehicle, traci.vehicle.getNextTLS(vehicle)[0][0]))
            #     self.penalties[traci.vehicle.getNextTLS(vehicle)[0][0]] -= 20


            for detector in detectors:
                vehs = traci.inductionloop.getLastStepVehicleIDs(detector)
                intersection = detector.split('_')[0]

                if traci.inductionloop.getLastStepMeanSpeed(detector) > 0:
                    self.intersection_speeds[intersection].append(traci.inductionloop.getLastStepMeanSpeed(detector))

                for veh in vehs: # usually just one here

                    # update penalties and parameters
                    if vehicle_last_intersection_id[veh] != detector:
                        self.penalties[intersection] -= step - vehicle_last_intersection_step[veh]
                        self.penalties[intersection] -= vehicle_number_of_stops[veh]
                        self.intersection_parameters[intersection]['num_cars'] += 1
                        self.intersection_parameters[intersection][detector.split('_')[-1] + '_dets_time'] = step
                        vehicle_last_intersection_id[veh] = detector
                    else:
                        self.penalties[intersection] -= 1
                    #

                    #reset vehicle's step
                    vehicle_last_intersection_step[veh] = step
                #
            #



            # actual cool decision making stuff happens here:
            for light in lights:
                if (traci.trafficlight.getNextSwitch(light) - step) == 1:
                    # use the neural network to make decisions (cool)

                    self.light_trigger(light, networks[light], 'timeout')


            step += 1

        traci.close()
        # print('penalties: ')
        # print(penalties)
        # print('intersection params: ')
        # print(get_params())
        # sys.stdout.flush()
        return self.penalties
