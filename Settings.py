import os
import json


class Settings:
    def __init__(self):
        self.settingsPath = os.path.join(os.getcwd(), 'settings.settings')
        self.dict = {}
        self.load()

    def __setitem__(self, key, value):
        self.dict[key] = value
        self.save()

    def __getitem__(self, key):
        if key in self.dict:
            return self.dict[key]
        else:
            return ''

    def load(self):
        if not os.path.isfile(self.settingsPath):
            with open(self.settingsPath, 'w') as file:
                json.dump({'default_constants': '',
                           'style': ''}, file, indent=4)
        with open(self.settingsPath, 'r') as file:
            self.dict = json.loads(file.read().replace('\n', ''))

    def save(self):
        with open(self.settingsPath, 'w') as file:
            json.dump(self.dict, file, indent=4)

    def getDefaultConstantsFile(self):
        settingsPath = os.path.join(os.getcwd(), 'settings.settings')
        if not os.path.isfile(settingsPath):
            with open(settingsPath, 'w') as file:
                json.dump({'default_constants': ''}, file, indent=4)
        with open(settingsPath, 'r') as file:
            return json.loads(file.read().replace('\n', ''))['default_constants']

    def setConstantsAsDefault(self):
        with open(os.path.join(os.getcwd(), 'settings.settings'), 'w') as file:
            json.dump({'default_constants': self.constantsFileEdit.text()}, file, indent=4)
        self.defaultConstantsButton.setEnabled(False)

    def append(self, key, item, position=None):
        if self.__getitem__(key) == '':
            self.dict[key] = []
        if position is not None:
            self.dict[key].insert(position, item)
        else:
            self.dict[key].append(item)
        self.save()
