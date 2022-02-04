import pandas as pd
import numpy as np
from scipy.stats import median_abs_deviation, iqr


class Inspector:
    desc = {
        '233U': 0,
        '234U': 1,
        '235U': 2,
        '236U': 3,
        '238U': 4,
        '229Th': 5,
        '230Th': 6,
        '232Th': 7,
        # '229Th (2)': 8,
    }

    def __init__(self):
        self.data_dict = None

    def inspect(self, path):
        raw = pd.read_table(path, sep='\t')
        infoCol = raw['Neptune Analysis Data Report']

        rowOffset = 0
        if 'Filename' not in infoCol[0]:
            rowOffset += 1

        for value in infoCol:
            value_str = str(value)
            if value_str.startswith('Sample ID'):
                self.labNr = value.replace('Sample ID: ', '')
            elif value_str.startswith('Analysis date:'):
                self.date = value.replace('Analysis date: ', '')
            elif value_str.startswith('Analysis time:'):
                self.time = value.replace('Analysis time: ', '')

        self.load_data(path)

    def load_data(self, path):
        cc = pd.read_table(path, sep='\t')  # read in files from Neptune software
        raw = pd.DataFrame(cc)
        sub_cc = raw['Unnamed: 1']  # gets second column

        sub_cc = sub_cc.values
        rowCup = np.where(sub_cc == 'Cup')[0][0]
        rawnew = raw.iloc[rowCup]
        rawnew = rawnew.values

        c3 = []
        for j in range(len(rawnew)):
            if rawnew[j] == 'C(C)':
                c3.append(j)

        sub_help = raw['Neptune Analysis Data Report']
        searchCycle = sub_help.str.contains('Cycle')
        rowphelp = None
        for k in range(len(searchCycle)):
            if searchCycle[k] == True:
                rowphelp = k
        # data starts on column 2 (always?)
        col233 = 2

        data = raw.iloc[(rowphelp + 1):rowCup, col233:(col233 + 9)]
        data = data.values
        data = data.astype(np.float)

        self.data_dict = {}

        for isotope, isotope_index in self.desc.items():
            if isotope not in self.data_dict:
                self.data_dict[isotope] = np.zeros(len(data))
            for value_index in range(len(data)):
                self.data_dict[isotope][value_index] = data[value_index, self.desc[isotope]]
            # remove nans (happened with SPA52: C:\Neptune\User\Neptune\Data\UTh\2015\0815\012_blk.dat)
            self.data_dict[isotope] = self.data_dict[isotope][~np.isnan(self.data_dict[isotope])]

    def get_stats(self, isotope, mean_option='median', dev_option='std'):
        X = self.data_dict[isotope]

        mean = None
        std = None

        if mean_option == 'mean':
            mean = np.mean(X)
        elif mean_option == 'median':
            mean = np.median(X)

        if dev_option == 'std':
            std = np.std(X)
        elif dev_option == 'mad':
            std = median_abs_deviation(X)
        elif dev_option == 'iqr':
            std = iqr(X)

        return mean, std

        '''X = X[np.where(np.logical_and(X >= mean - 2 * std, X <= mean + 2 * std))]

        if mean_option == 'mean':
            mean = np.mean(X)
        elif mean_option == 'median':
            mean = np.median(X)

        if dev_option == 'std':
            std = np.std(X)
        elif dev_option == 'mad':
            std = median_abs_deviation(X)
        elif dev_option == 'iqr':
            std = iqr(X)

        return mean, std'''
