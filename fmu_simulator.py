import fmpy
import atexit
import shutil
import numpy as np


class FMUSimulator:
    def __init__(self, path: str, starting_time: float, parameters: dict):
        model_description = fmpy.read_model_description(path)

        # Collect value references
        self.vrs = {}
        for variable in model_description.modelVariables:
            self.vrs[variable.name] = variable.valueReference

        self.unzipdir = fmpy.extract(path)
        atexit.register(self.remove_unzipdir)
        print("Unzip directory", self.unzipdir)

        self.fmu = fmpy.fmi2.FMU2Slave(
                guid=model_description.guid,
                unzipDirectory=self.unzipdir,
                modelIdentifier=model_description.coSimulation.modelIdentifier,
                instanceName='instance1')

        self.t = starting_time
        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=self.t)
        self.fmu.enterInitializationMode()

        parameter_references = [self.vrs[name] for name in parameters.keys()]
        parameter_values = list(parameters.values())

        self.fmu.setReal(parameter_references, parameter_values)
        self.fmu.exitInitializationMode()


    def remove_unzipdir(self):
        print("Deleting unzipdir")
        shutil.rmtree(self.unzipdir, ignore_errors=True)


    def set_input(self, u: float):
        self.fmu.setReal([self.vrs["u"]], [u])

    def step(self, dt: float):
        self.fmu.doStep(currentCommunicationPoint=self.t, communicationStepSize=dt)
        self.t += dt

    def get_output(self) -> float:
        return self.fmu.getReal([self.vrs["x"]])[0]


