import fmpy
from pathlib import Path
import atexit
import shutil
import numpy as np
from functools import cache


class FMUSimulator:
    def __init__(self, path: Path, starting_time: float, parameters: dict):
        print("Parsing fmu at", path)
        self.model_description = fmpy.read_model_description(path)
        self.parameters = parameters
        self.starting_time = starting_time
        fmpy.dump(path)

        # Collect value references
        self.vrs = {}
        for variable in self.model_description.modelVariables:
            # accepted_causalities = ["input", "output", "parameter"]
            # if variable.causality not in accepted_causalities:
            #     continue

            self.vrs[variable.name] = variable.valueReference
            # print(f"\tmodel {variable.causality}:", variable)

        self.unzipdir = fmpy.extract(path)
        atexit.register(self.remove_unzipdir)

        self.reset()

    @cache
    def get_output_names(self):
        return list(
            map(
                lambda v: v.name,
                filter(
                    lambda v: v.causality == "output",
                    self.model_description.modelVariables,
                ),
            )
        )

    @cache
    def get_input_names(self):
        return list(
            map(
                lambda v: v.name,
                filter(
                    lambda v: v.causality == "input",
                    self.model_description.modelVariables,
                ),
            )
        )

    def reset(self):
        self.fmu = fmpy.fmi2.FMU2Slave(
            guid=self.model_description.guid,
            unzipDirectory=self.unzipdir,
            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
            instanceName="instance1",
        )

        self.t = self.starting_time
        self.fmu.instantiate()
        self.fmu.setupExperiment(startTime=self.t)
        self.fmu.enterInitializationMode()

        parameter_references = [self.vrs[name] for name in self.parameters.keys()]
        parameter_values = list(self.parameters.values())

        self.fmu.setReal(parameter_references, parameter_values)
        self.fmu.exitInitializationMode()
        pass

    def remove_unzipdir(self):
        shutil.rmtree(self.unzipdir, ignore_errors=True)

    def set_input(self, inputs: dict):
        input_references = [self.vrs[name] for name in inputs.keys()]
        input_values = list(inputs.values())
        self.fmu.setReal(input_references, input_values)

    def step(self, dt: float):
        self.fmu.doStep(currentCommunicationPoint=self.t, communicationStepSize=dt)
        self.t += dt

    def get_output(self, value_names: list) -> float:
        value_references = [self.vrs[name] for name in value_names]
        return self.fmu.getReal(value_references)
