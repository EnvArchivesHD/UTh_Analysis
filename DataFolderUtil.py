import json
import os
import shutil
import glob
import re


def getFiles(path):
    old_path = os.getcwd()
    os.chdir(path)

    data = glob.glob('.\\*.exp') + glob.glob('data\*.exp')
    blanks = glob.glob('.\\*blk*.exp') + glob.glob('blank\*blk*.exp')
    yhasu = glob.glob('.\\*yhasU*.exp') + glob.glob('yhas_u\*yhasU*.exp')
    yhasth = glob.glob('.\\*yhasTh*.exp') + glob.glob('yhas_th\*yhasTh*.exp')
    hf = glob.glob('.\\*hf*.exp') + glob.glob('hf\*hf*.exp')

    files = {'data': data, 'blank': blanks, 'yhasth': yhasth, 'yhasu': yhasu, 'hf': hf}

    os.chdir(old_path)

    return files


def willFilesBeMoved(path):
    old_path = os.getcwd()
    os.chdir(path)

    if len(glob.glob('.\\*.exp') + glob.glob('.\\*blk*.exp') + glob.glob('.\\*yhasU.exp') + glob.glob(
            '.\\*yhasTh.exp') + glob.glob('.\\*hf*.exp')) > 0:
        os.chdir(old_path)
        return True
    else:
        os.chdir(old_path)
        return False


def willFilesBeDeleted(path):
    old_path = os.getcwd()
    os.chdir(path)

    if len(glob.glob('.\\*.TDT') + glob.glob('.\\*.dat') + glob.glob('.\\*.log') + glob.glob('.\\*.ini') + glob.glob(
            '.\\*.TXT')) > 0:
        os.chdir(old_path)
        return True
    else:
        os.chdir(old_path)
        return False


def findStandardNumber(path, type='string'):
    labNrs = getLabNrsFromList(getFiles(path)['data'], type=type)

    maxN = max(set(labNrs), key=labNrs.count)
    if maxN == '' or labNrs.count(maxN) == 1:
        return None
    else:
        return maxN


def getLabNrsFromList(filenameList, type='string'):
    # gets numbers via the following format: 1. one or more numbers 2. optional non digit characters 3. ends with .exp
    if type == 'string':
        labNrs = [re.search('(\d+\D*)(\.exp)', file).group(1) for file in filenameList]
    elif type == 'int':
        labNrs = [int(re.search('(\d+)(\D*\.exp)', file).group(1)) for file in filenameList]

    return labNrs

def getLabNrRange(path):
    standard = findStandardNumber(path, type='int')

    labNrs = getLabNrsFromList(getFiles(path)['data'], type='int')

    # remove standard
    if standard is not None:
        labNrs = [nr for nr in labNrs if nr != standard]
    return [min(labNrs), max(labNrs)]


def createDataFolders(path):
    old_path = os.getcwd()
    os.chdir(path)

    if os.path.exists('blank') == False:
        os.mkdir('blank')
    if os.path.exists('data') == False:
        os.mkdir('data')
    if os.path.exists('yhas_th') == False:
        os.mkdir('yhas_th')
    if os.path.exists('yhas_u') == False:
        os.mkdir('yhas_u')
    if os.path.exists('hf') == False:
        os.mkdir('hf')

    # blanks
    blanks = glob.glob('.\\*blk*.exp')
    for b in blanks:
        shutil.move(b, 'blank')
    # yhas_u
    yhasu = glob.glob('.\\*yhasU.exp')
    for u in yhasu:
        shutil.move(u, 'yhas_u')
    # yhas_th
    yhasth = glob.glob('.\\*yhasTh.exp')
    for t in yhasth:
        shutil.move(t, 'yhas_th')
    # hf
    hf = glob.glob('.\\*hf*.exp')
    for h in hf:
        shutil.move(h, 'hf')
    # data
    datar = glob.glob('.\\*.exp')
    for d in datar:
        shutil.move(d, 'data')

    os.chdir(old_path)


def removeUnnecessaryFiles(path):
    old_path = os.getcwd()
    os.chdir(path)

    files = glob.glob('.\\*.TDT') + glob.glob('.\\*.dat') + glob.glob('.\\*.log') + glob.glob('.\\*.ini') + glob.glob(
        '.\\*.TXT')
    for file in files:
        os.remove(file)

    os.chdir(old_path)


'''
    used for debugging
    specifically investigation of uncorrected age being lower than corrected age in some cases
'''


def writeList(path, filename, list):
    with open(os.path.join(path, filename), 'w') as file:
        for list_count, sub_list in enumerate(list):
            for i, item in enumerate(sub_list):
                file.write('{}'.format(item))
                if i < len(sub_list) - 1:
                    file.write(',')
            if list_count < len(list) - 1:
                file.write('\n')
        file.close()


def writeLineByLine(path, filename, list):
    with open(os.path.join(path, filename), 'w') as file:
        for element in list:
            file.write('{}\n'.format(element))
        file.close()


def findCurrentOutputNumber(path):
    maxNumber = 0
    for file in [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]:
        reResult = re.findall('.*(\d+)\.xlsx', file)
        if reResult:
            maxNumber = max(maxNumber, int(reResult[0]))
    return maxNumber


def tryCreateOutputFolder(dataPath, outputPath, outputDict):
    folderName = 'PUA_{}-{} {}'.format(outputDict['min_lab_nr'], outputDict['max_lab_nr'], outputDict['name'])
    dataOutputPath = os.path.join(outputPath, folderName)

    # Get connections dictionary
    connectionsPath = os.path.join(outputPath, 'connections.json')
    if os.path.exists(connectionsPath):
        with open(connectionsPath, 'r') as file:
            connectionsDict = json.loads(file.read().replace('\n', ''))
    else:
        connectionsDict = {}

    baseDataFolder = baseName(dataPath)

    if baseDataFolder in connectionsDict:
        os.rename(os.path.join(outputPath, connectionsDict[baseDataFolder]), dataOutputPath)
    else:
        if not os.path.exists(dataOutputPath):
            os.mkdir(dataOutputPath)
    dict_path = os.path.join(dataOutputPath, 'info.json')
    with open(dict_path, 'w') as file:
        json.dump(outputDict, file, indent=4)

    connectionsDict[baseDataFolder] = folderName

    with open(connectionsPath, 'w') as file:
        json.dump(connectionsDict, file, indent=4)


def baseName(path):
    return os.path.basename(os.path.normpath(path))