from onto.ontopathsloader import OntoPathsLoader
from onto.ontoreader import OntoReader
from semsim.semsim_lin import SemLin
from semsim.semsin_resnik import SemResnik

DEFAULT_HPO_FILE = 'resources/hp.obo'
DEFAULT_PATHS_FILE = 'resources/hp_paths.list'
DEFAULT_IC_FILE = 'resources/hp_ic.list'
DEFAULT_SPEC_FILE = 'resources/hp_spec.list'


class ModelsList:
    modelsData = {}
    ontoReader = None

    semSims = {}
    ontoPathsMap = {}
    icData = {}
    specData = {}

    def __init__(self, modelsFile, hpoFile=DEFAULT_HPO_FILE,
                 ontoPathsFile=DEFAULT_PATHS_FILE,
                 hpICFile=DEFAULT_IC_FILE,
                 hpSpecFile=DEFAULT_SPEC_FILE):
        self.ontoReader = OntoReader(hpoFile)

        self.loadPrerequisites(ontoPathsFile, hpICFile, hpSpecFile)

        self.modelsData = {}
        self.readModelsFile(modelsFile)

    def loadPrerequisites(self, ontoPathsFile, hpICFile, hpSpecFile):
        self.ontoPathsMap = OntoPathsLoader(ontoPathsFile).getOntoPathsMap()
        self.icData = self.loadData(hpICFile)
        self.specData = self.loadData(hpSpecFile)

        self.semSims = {
            'resnik': SemResnik(self.ontoPathsMap, self.icData, self.specData),
            'lin': SemLin(self.ontoPathsMap, self.icData, self.specData)
        }

    def loadData(self, dataFile):
        with open(dataFile, 'r') as fh:
            lines = fh.readlines()
        data = {}
        for line in lines:
            line = line.strip()
            if line:
                segs = line.split('\t')
                data[segs[0].strip()] = float(segs[1].strip())
        return data

    def readModelsFile(self, modelsFile):
        with open(modelsFile, 'r') as fh:
            lines = fh.readlines()

        for line in lines:
            line = line.strip()
            segs = line.split('=')
            hpoId = segs[0]
            flag = segs[1]

            consolidatedHPOId = self.ontoReader.consolidate(hpoId)
            if not consolidatedHPOId:
                print('Term {} from the models file does not exist.'.format(hpoId))
                continue
            val = False
            if flag.lower() == 'y':
                val = True
            if consolidatedHPOId in self.modelsData:
                val = val or self.modelsData[consolidatedHPOId]
            self.modelsData[consolidatedHPOId] = val

    def getBestModelForTerm(self, term: str, semsim: str, useIC=True, threshold=0.0):
        consolidatedTerm = self.ontoReader.consolidate(term)
        if not consolidatedTerm:
            print('Term {} does no longer exist in the ontology'.format(term))
            return None, -1.0

        if consolidatedTerm in self.modelsData:
            if self.modelsData[consolidatedTerm]:
                return consolidatedTerm, -1.0
            else:
                print(
                    'Term {} (consolidated as {}) exists in the models list, but without a model. Returning the best match with a model.'.format(
                        term, consolidatedTerm))

        max = None
        maxVal = 0.0
        for entry in self.modelsData:
            if not self.modelsData[entry]:
                continue

            semVal = self.semSims[semsim].compute(consolidatedTerm, entry, useIC)
            if semVal >= threshold:
                if semVal > maxVal:
                    maxVal = semVal
                    max = entry

        if max:
            print('Best model for term {} is: {} ({})'.format(term, max, maxVal))
            return max, maxVal

        return None, -1.0

    def getBestModelsForList(self, termList: [str], semsim: str, useIC=True, threshold=0.0):
        result = {}
        for term in termList:
            max, maxVal = self.getBestModelForTerm(term, semsim, useIC, threshold)
            if max:
                result[term] = (max, maxVal)
        return result


def main():
    modelsListFile = 'resources/example_models.list'
    modelsList = ModelsList(modelsListFile)

    max, maxVal = modelsList.getBestModelForTerm('HP:0001248', 'lin')
    if max:
        print('{} - {}'.format(max, maxVal))


if __name__ == '__main__':
    main()
