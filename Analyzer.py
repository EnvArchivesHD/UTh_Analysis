import numpy as np
import pandas as pd

from pandas import ExcelWriter

import DataFolderUtil
from random import random
import Util
import Globals
import os

import ExcelFormatter
from AnalyzerMethods import thu_alter_kombi, montealter, marincorr_age_error, taylor_err, marincorr_age


class Analyzer:
    def __init__(self):
        self.data_root_folder = None
        self.calculate_age_errors = True

    def set_path(self, path, find_standard=True):
        self.data_root_folder = path
        if find_standard:
            self.standard = DataFolderUtil.findStandardNumber(path)

    def set_constants(self, constants):
        self.constantsType = constants['type']

        self.constants = constants

        # spike impurities
        self.R34_33 = constants['R3433']
        self.R35_33 = constants['R3533']
        self.R30_29 = constants['R3029']

        # constants
        self.mf48 = constants['mf48']
        self.mf36 = constants['mf36']
        self.mf56 = constants['mf56']
        self.mf68 = constants['mf68']
        self.mf92 = constants['mf92']

        self.mf38 = constants['mf38']
        self.mf35 = constants['mf35']
        self.mf43 = constants['mf43']
        self.mf45 = constants['mf45']
        self.mf09 = constants['mf09']
        self.mf29 = constants['mf29']
        self.mf34 = constants['mf34']
        self.mf58 = constants['mf58']
        self.mf02 = constants['mf02']

        self.NA = constants['NA']
        self.NR85 = constants['NR85']
        self.cps = constants['cps']

        self.lambda232 = constants['l232']
        self.lambda234 = constants['l234']
        self.lambda238 = constants['l238']
        self.lambda230 = constants['l230']

        self.tri236 = constants['tri236']
        self.tri233 = constants['tri233']
        self.tri229 = constants['tri229']

        self.spBlank230 = constants['sp_blank230']
        self.blank234 = constants['blank234']
        self.blank234S = constants['blank234S']
        self.blank238 = constants['blank238']
        self.blank238S = constants['blank238S']
        self.blank232 = constants['blank232']
        self.blank232S = constants['blank232S']

        self.chBlank230 = constants['ch_blank230']
        self.chBlank230S = constants['ch_blank230S']

        self.a230232_init = constants['a230232_init']
        self.a230232_init_err = constants['a230232_init_err']
        self.a230232_init_sst = constants['a230232_init_sst']
        self.a230232_init_err_sst = constants['a230232_init_err_sst']


        self.standardBezeich = constants['standardBezeich']
        self.standardEinwaage = constants['standardEinwaage']
        self.standardTriSp13 = constants['standardTriSp13']

    def set_specific_constants(self, specific_constants):
        self.specific_constants = specific_constants

    def set_metadata(self, metadata_path, ratios):
        '''
         build up full metadata file, either from .csv or .xlsx files
        '''
        if metadata_path.endswith('.csv'):
            fullMetadata = pd.read_csv(metadata_path, sep=';', na_filter=False)
            fullMetadata['Tiefe'] = fullMetadata.pop('Tiefe (cm)')
            self.tiefe_unit = 'cm'

        elif metadata_path.endswith('.xlsx'):
            fullMetadata = pd.read_excel(metadata_path, sheet_name='Ergebnisse', na_filter=False, engine='openpyxl')

            metadata_dict = {'Lab. #': [], 'Bezeich.': [], 'Art der Probe': [], 'Mess. Dat.': [], 'Tiefe': [],
                             'Einwaage (g)': [], 'TriSp13 (g)': []}

            if fullMetadata.iloc[:, 4].str.contains('cm').any():
                self.tiefe_unit = 'cm'
            elif fullMetadata.iloc[:, 4].str.contains('mm').any():
                self.tiefe_unit = 'mm'

            for idx, row in fullMetadata.iterrows():
                try:
                    labnr = fullMetadata.iloc[idx, 0]
                    metadata_dict['Lab. #'].append(labnr)
                    metadata_dict['Bezeich.'].append(fullMetadata.iloc[idx, 1])
                    metadata_dict['Art der Probe'].append(fullMetadata.iloc[idx, 2])
                    metadata_dict['Mess. Dat.'].append(fullMetadata.iloc[idx, 3])
                    metadata_dict['Tiefe'].append(fullMetadata.iloc[idx, 4])
                    metadata_dict['Einwaage (g)'].append(fullMetadata.iloc[idx, 5])
                    metadata_dict['TriSp13 (g)'].append(fullMetadata.iloc[idx, 6])
                except:
                    pass

            fullMetadata = pd.DataFrame(metadata_dict)

        # prevents wrong date format in results file
        try:
            fullMetadata['Mess. Dat.'] = fullMetadata['Mess. Dat.'].dt.strftime('%d.%m.%Y')
        except:
            pass

        # fixes standard name in "Art der Probe"
        for i in range(len(fullMetadata.index)):
            if fullMetadata['Art der Probe'][i] == 'St.':
                fullMetadata['Art der Probe'][i] = 'Standard'

        if self.standard in list(fullMetadata['Lab. #']):
            standardRow = fullMetadata[fullMetadata['Lab. #'] == self.standard]
        else:
            standardRow = pd.DataFrame(
                {'Lab. #': [self.standard], 'Bezeich.': [self.standardBezeich], 'Art der Probe': ['Standard'],
                 'Mess. Dat.': [''], 'Tiefe': [''],
                 'Einwaage (g)': [self.standardEinwaage], 'TriSp13 (g)': [self.standardTriSp13]})

        measurementLabNrs = DataFolderUtil.getLabNrsFromList(list(ratios.index))

        # get measurement dates (add to metadata array, because it gets added to excel later, on calc sheet)
        dates = Util.get_dates(self.data_root_folder)

        # duplicate last standard row if last measurement was not standard measurement
        indices = list(ratios.index)
        if measurementLabNrs[-1] != self.standard and self.standard is not None:
            measurementLabNrs.append(self.standard)
            indices.append(indices[-2])
            dates.append(dates[-2])
        '''
         build up measurement specific metadata dataframe
        '''
        metadata_dict = {
            'Lab. #': [], 'Bezeich.': [], 'Art der Probe': [], 'Mess. Dat.': dates, 'Tiefe': [],
            'Einwaage (g)': [], 'TriSp13 (g)': []
        }

        missing_labnrs = []

        for labnr in measurementLabNrs:
            if labnr == self.standard:
                metadata_dict['Lab. #'].append(labnr)
                metadata_dict['Bezeich.'].append(standardRow.iloc[0]['Bezeich.'])
                metadata_dict['Art der Probe'].append(standardRow.iloc[0]['Art der Probe'])
                metadata_dict['Tiefe'].append(standardRow.iloc[0]['Tiefe'])
                metadata_dict['Einwaage (g)'].append(standardRow.iloc[0]['Einwaage (g)'])
                metadata_dict['TriSp13 (g)'].append(standardRow.iloc[0]['TriSp13 (g)'])
            else:

                labnr_row = fullMetadata[fullMetadata['Lab. #'].astype(str) == labnr]

                if labnr_row.empty:
                    missing_labnrs.append(labnr)
                else:
                    metadata_dict['Lab. #'].append(labnr)
                    metadata_dict['Bezeich.'].append(labnr_row.iloc[0]['Bezeich.'])
                    metadata_dict['Art der Probe'].append(labnr_row.iloc[0]['Art der Probe'])
                    metadata_dict['Tiefe'].append(labnr_row.iloc[0]['Tiefe'])
                    metadata_dict['Einwaage (g)'].append(labnr_row.iloc[0]['Einwaage (g)'])
                    metadata_dict['TriSp13 (g)'].append(labnr_row.iloc[0]['TriSp13 (g)'])

        if missing_labnrs:
            raise ValueError('The metadata is missing the following Lab.Nrs.: {}'.format(', '.join(missing_labnrs)))

        # Convert laboratory numbers to int if possible
        # metadata_dict['Lab. #'] = Util.try_convert_to_int(metadata_dict['Lab. #'])

        # Create dataframe
        self.metadata = pd.DataFrame(metadata_dict, index=indices)

        # Set blanks

        blank234 = [self.blank234S if desc == 'Standard' else self.blank234 for desc in self.metadata['Art der Probe']]
        blank238 = [self.blank238S if desc == 'Standard' else self.blank238 for desc in self.metadata['Art der Probe']]
        blank232 = [self.blank232S if desc == 'Standard' else self.blank232 for desc in self.metadata['Art der Probe']]
        chBlank230 = [self.chBlank230S if desc == 'Standard' else self.chBlank230 for desc in
                      self.metadata['Art der Probe']]
        a230232_init = [self.a230232_init_sst if desc == 'Standard' else self.a230232_init for desc in self.metadata['Art der Probe']]
        a230232_init_err = [self.a230232_init_err_sst if desc == 'Standard' else self.a230232_init_err for desc in self.metadata['Art der Probe']]

        self.blanks = pd.DataFrame({'Blank 234 (fg)': blank234,
                                    'Blank 238 (ng)': blank238,
                                    'Blank 232 (ng)': blank232,
                                    'Ch. Blank 230 (fg)': chBlank230,
                                    'A230Th232Th Init.': a230232_init,
                                    'A230Th232Th Init. err': a230232_init_err}, index=indices)

    def set_metadata_df(self, metadata):
        '''
         set metadata df directly
        '''
        self.metadata = metadata

        self.tiefe_unit = self.metadata['Tiefe'].iloc[0]
        self.metadata = self.metadata[self.metadata['Lab. #'].notna()]
        self.metadata.index = list(range(len(self.metadata)))

        # duplicate last standard row if last measurement was not standard measurement
        if self.metadata.iloc[-1]['Lab. #'] != self.standard and self.standard is not None:
            self.metadata = self.metadata.append(self.metadata.iloc[-2], ignore_index=True)

        # Set blanks
        blank234 = [self.blank234S if desc == 'Standard' else self.blank234 for desc in self.metadata['Art der Probe']]
        blank238 = [self.blank238S if desc == 'Standard' else self.blank238 for desc in self.metadata['Art der Probe']]
        blank232 = [self.blank232S if desc == 'Standard' else self.blank232 for desc in self.metadata['Art der Probe']]
        chBlank230 = [self.chBlank230S if desc == 'Standard' else self.chBlank230 for desc in
                      self.metadata['Art der Probe']]
        a230232_init = [self.a230232_init_sst if desc == 'Standard' else self.a230232_init for desc in self.metadata['Art der Probe']]
        a230232_init_err = [self.a230232_init_err_sst if desc == 'Standard' else self.a230232_init_err for desc in self.metadata['Art der Probe']]

        self.blanks = pd.DataFrame({'Blank 234 (fg)': blank234,
                                    'Blank 238 (ng)': blank238,
                                    'Blank 232 (ng)': blank232,
                                    'Ch. Blank 230 (fg)': chBlank230,
                                    'A230Th232Th Init.': a230232_init,
                                    'A230Th232Th Init. err': a230232_init_err}, index=self.metadata.index)

    def analyze(self, ratios, filename='Results', write_results_file=True, options_dict=None, output_path=None):
        ratios = ratios.copy()

        # Add additional row if last standard was not measured
        if len(ratios.index) + 1 == len(self.metadata.index):
            ratios = ratios.append(ratios.iloc[-2], ignore_index=False)

        # Ratio 234/233
        r234233_err = ratios['Ratio 234/233'] * ratios['Error (%) 234/233'] / 100
        r235236_err = ratios['Ratio 235/236'] * ratios['Error (%) 235/236'] / 100

        # Ratio 238/236
        r238236 = ratios['Ratio 235/236'] * self.NR85
        r238236_err = r238236 * ratios['Error (%) 235/238'] / 100

        # 234U
        u234pgg = ((ratios['Ratio 234/233'] * self.tri233 * 10 ** -9 * self.metadata['TriSp13 (g)'] * (
                234.0409521 / 233.0396352)) -
                   (self.blanks['Blank 234 (fg)'] * 10 ** -15)) * 10 ** 12 / self.metadata['Einwaage (g)']
        u234pgg_err = u234pgg * ratios['Error (%) 234/233'] / 100
        u234dpmg = (u234pgg / 234.0409521) * self.NA * 10 ** -12 * self.lambda234 / (365.2425 * 24 * 60)
        u234dpmg_err = u234dpmg * ratios['Error (%) 234/233'] / 100

        # 238U
        u238mugg = ((r238236 * self.tri236 * 10 ** -9 * self.metadata['TriSp13 (g)'] * (238.0507882 / 236.045568)) -
                    (self.blanks['Blank 238 (ng)'] * 10 ** -9)) * 10 ** 6 / self.metadata['Einwaage (g)']
        u238mugg_err = u238mugg * ratios['Error (%) 235/236'] / 100
        u238dpmg = (u238mugg / 238.0507882) * self.NA * 10 ** -6 * self.lambda238 / (365.2425 * 24 * 60)
        u238dpmg_err = u238dpmg * ratios['Error (%) 235/236'] / 100

        # a234238
        a234238 = ratios['Ratio 234/238'] * self.lambda234 / self.lambda238
        a234238_err = a234238 * ratios['Error (%) 234/238'] / 100
        a234238_corr = [a234238[i] * 2 / (a234238[i - 1] + a234238[i + 1])
                        if (
                0 < i < len(a234238) - 1 and
                self.standard is not None and
                self.standard not in ratios['Lab. #'].iloc[i]
        )
                        else a234238[i]
                        for i
                        in range(len(a234238))]
        a234238_corr_err = a234238_corr * ratios['Error (%) 234/238'] / 100

        # 232Th
        th232ngg = ((self.tri229 * 10 ** -9 * self.metadata['TriSp13 (g)'] * (232.0380553 / 229.031762) / ratios[
            'Ratio 229/232']) -
                    (self.blanks['Blank 232 (ng)'] * 10 ** -9)) * 10 ** 9 / self.metadata['Einwaage (g)']

        th232ngg_err = th232ngg * ratios['Error (%) 229/232'] / 100
        th232dpmg = (th232ngg / 232.0380553) * self.NA * 10 ** -9 * self.lambda232 / (365.2425 * 24 * 60)
        th232dpmg_err = th232dpmg * ratios['Error (%) 229/232'] / 100

        # 230Th
        th230pgg = ((ratios['Ratio 230/229'] * self.tri229 * 10 ** -9 * self.metadata['TriSp13 (g)'] * (
                230.0331338 / 229.031762))
                    - (self.spBlank230 * self.metadata['TriSp13 (g)'] * 10 ** -15 +
                       self.blanks['Ch. Blank 230 (fg)'] * 10 ** -15)) * 10 ** 12 / self.metadata['Einwaage (g)']
        th230pgg_err = th230pgg * ratios['Error (%) 230/229'] / 100
        th230dpmg = (th230pgg / 230.0331338) * self.NA * 10 ** -12 * self.lambda230 / (365.2425 * 24 * 60)
        th230dpmg_err = th230dpmg * ratios['Error (%) 230/229'] / 100

        # a230232
        a230232 = th230dpmg / th232dpmg
        a230232_err = a230232 * (np.array((th230dpmg_err / th230dpmg) ** 2 + (th232ngg_err / th232ngg) ** 2)) ** 0.5

        # a230238
        a230238 = th230dpmg / u238dpmg
        a230238_err = a230238 * ((u238dpmg_err / u238dpmg) ** 2 + (th230pgg_err / th230pgg) ** 2) ** 0.5
        a230238_corr = [a230238[i] * 2 / (a230238[i - 1] + a230238[i + 1])
                        if (
                0 < i < len(a230238) - 1 and
                self.standard is not None and
                self.standard not in ratios['Lab. #'].iloc[i]
        )
                        else a230238[i]
                        for i
                        in range(len(a230238))]
        a230238_corr_err = a230238_corr * ((th230dpmg_err / th230dpmg) ** 2 + (u238dpmg_err / u238dpmg) ** 2) ** 0.5

        # a232238
        a232238 = th232dpmg / u238dpmg
        a232238_err = a232238 * ((th232dpmg_err / th232dpmg) ** 2 + (u238dpmg_err / u238dpmg) ** 2) ** 0.5

        # Ages
        a230232_init = np.array(self.blanks['A230Th232Th Init.'])
        a230232_init_err = np.array(self.blanks['A230Th232Th Init. err'])
        # uncorrected Ages
        age_uncorr = [thu_alter_kombi(a230238_corr[i], a234238_corr[i], self.lambda230, self.lambda234) for i in
                      range(len(a230238_corr))]

        # corrected Ages
        age_corr = [marincorr_age(a230238_corr[i], a234238_corr[i], a232238[i], a230232_init[i], self.lambda230,
                                  self.lambda234) for i in
                    range(len(a230238_corr))]

        # Age errors

        age_uncorr_errors = []
        age_uncorr_rel_errors = []
        age_uncorr_fractions = []
        age_corr_errors = []
        age_corr_rel_errors = []
        age_corr_fractions = []

        if self.calculate_age_errors:
            for i in range(len(age_uncorr)):
                if age_uncorr[i] == 'Out of range':
                    age_uncorr_errors.append('/')
                    age_uncorr_rel_errors.append('/')
                    age_uncorr_fractions.append('/')
                else:
                    error, out_of_range_fraction = montealter(a230238_corr[i],
                                                              a230238_corr_err[i],
                                                              a234238_corr[i],
                                                              a234238_corr_err[i],
                                                              self.lambda230,
                                                              self.lambda234)
                    age_uncorr_errors.append(error)
                    age_uncorr_rel_errors.append(error / age_uncorr[i] * 100)
                    age_uncorr_fractions.append(100 - out_of_range_fraction * 100)

                if age_corr[i] == 'Out of range':
                    age_corr_errors.append('/')
                    age_corr_rel_errors.append('/')
                    age_corr_fractions.append('/')
                else:
                    error, out_of_range_fraction = marincorr_age_error(a230238_corr[i],
                                                                       a230238_corr_err[i],
                                                                       a234238_corr[i],
                                                                       a234238_corr_err[i],
                                                                       a232238[i],
                                                                       a232238_err[i],
                                                                       a230232_init[i],
                                                                       a230232_init_err[i],
                                                                       self.lambda230,
                                                                       self.lambda234)
                    age_corr_errors.append(error)
                    age_corr_rel_errors.append(error / age_corr[i] * 100)
                    age_corr_fractions.append(100 - out_of_range_fraction * 100)
        else:
            age_uncorr_errors = ['/'] * len(age_uncorr)
            age_uncorr_rel_errors = ['/'] * len(age_uncorr)
            age_uncorr_fractions = ['/'] * len(age_uncorr)
            age_corr_errors = ['/'] * len(age_uncorr)
            age_corr_rel_errors = ['/'] * len(age_uncorr)
            age_corr_fractions = ['/'] * len(age_uncorr)

        d234U = (np.array(a234238_corr) - 1) * 1000
        d234U_err = np.array(a234238_corr_err) * 1000

        age_corr_taylor = [taylor_err(a230232_init[i],
                                      age_corr[i],
                                      d234U[i],
                                      a232238[i],
                                      a232238_err[i],
                                      a230232_init_err[i],
                                      a234238_corr_err[i],
                                      a230238_corr_err[i],
                                      self.lambda230,
                                      self.lambda234) for i in range(len(age_corr))]

        d234U_init = []
        d234U_init_err = []
        for i in range(len(age_corr)):
            if age_corr[i] == 'Out of range':
                d234U_init.append('/')
            else:
                d234U_init.append(((a234238_corr[i] - 1) * np.exp(self.lambda234 * age_corr[i] * 1000)) * 1000)

            if age_corr[i] == 'Out of range' or age_corr_errors[i] == '/':
                d234U_init_err.append('/')
            else:
                d234U_init_err.append((
                                              (np.exp(self.lambda234 * age_corr[i] * 1000) * a234238_corr_err[
                                                  i]) ** 2 + (
                                                      (a234238_corr[i] - 1) * self.lambda234 * np.exp(
                                                  self.lambda234 * age_corr[i] * 1000) *
                                                      age_corr_errors[i] * 1000) ** 2) ** 0.5 * 1000)

        cheng_corr = [age_corr[i] * 1000 - 58
                      if age_corr[i] != 'Out of range' else 'Out of range' for i in range(len(age_corr))]
        taylor_err_one_sig = [age_corr_taylor[i] / 2 * 1000
                              if age_corr_taylor[i] != '/' else '/' for i in range(len(cheng_corr))]
        two_sig_t = [age_corr_taylor[i] / age_corr[i] * 100
                     if taylor_err_one_sig != '/' and age_corr[i] != 'Out of range' else '/' for i in
                     range(len(age_corr))]

        # Create input sheet dataframe
        self.input = pd.concat([self.metadata, ratios.drop(columns=['Lab. #'], errors='ignore')], axis=1)
        self.input.drop(['dU234', 'Error dU234 (abs.)'], axis=1, inplace=True, errors='ignore')

        input_units = ['', '', '', '', self.tiefe_unit, '', '', '', '', '', 'gem.', '(%)', 'gem.', '(%)', 'gem.+korr.', '(%)',
                       'gem.', '(%)', 'gem.', '(%)', '', '(%)', '', '(%)', '', '(%)']
        input_units_frame = pd.DataFrame(dict(zip(self.input.columns, input_units)), index=[''])
        self.input = pd.concat([self.input.iloc[:0], input_units_frame, self.input[0:]])

        # Create calc sheet dataframe
        self.calc = pd.DataFrame({
            'Lab. #': list(self.metadata['Lab. #']), 'Bezeich.': list(self.metadata['Bezeich.']),
            '244/233U': list(ratios['Ratio 234/233']), 'Fehler1': list(r234233_err),
            '235/236U': list(ratios['Ratio 235/236']), 'Fehler2': list(r235236_err),
            '238/236U': r238236, 'Fehler3': r238236_err,
            'Blank 234': self.blanks['Blank 234 (fg)'],
            '234U1': u234pgg, 'Fehler4': u234pgg_err,
            '234U2': u234dpmg, 'Fehler5': u234dpmg_err,
            'Blank 238': self.blanks['Blank 238 (ng)'],
            '238U1': u238mugg, 'Fehler6': u238mugg_err,
            '238U2': u238dpmg, 'Fehler7': u238dpmg_err,
            '234U/238U': a234238, 'Fehler8': a234238_err,
            '234U/238Ukorr': a234238_corr, 'Fehler9': a234238_corr_err,
            'Blank 232': self.blanks['Blank 232 (ng)'],
            '232Th': th232ngg, 'Fehler10': th232ngg_err,
            'A232': th232dpmg, 'Fehler11': th232dpmg_err,
            'Ch. Bl. 230': self.blanks['Ch. Blank 230 (fg)'],
            '230Th1': th230pgg, 'Fehler12': th230pgg_err,
            '230Th2': th230dpmg, 'Fehler13': th230dpmg_err,
            'A230/232': a230232, 'Fehler14': a230232_err,
            'd234U': d234U, 'Fehler15': d234U_err,
            '230Th/238U': a230238, 'Fehler16': a230238_err,
            '230Th/238Ukorr': a230238_corr, 'Fehler17': a230238_corr_err,
            'Alter (unkorr.)': age_uncorr, 'Fehler18': age_uncorr_errors, 'Fehler': age_uncorr_rel_errors,
            '232Th/238U': a232238, 'Fehler20': a232238_err,
            '(230Th/232Th)': self.blanks['A230Th232Th Init.'], 'Fehler21': self.blanks['A230Th232Th Init. err'],
            'Cheng korr.': age_corr, 'Fehler22': age_corr_errors, 'Fehler23': age_corr_taylor,
            'Fehler24': age_corr_rel_errors,
            'Bezeichnung': list(self.metadata['Bezeich.']), 'Tiefe': self.metadata['Tiefe'],
            'd234U (initial)': d234U_init, 'Fehler25': d234U_init_err,
            'Cheng korr': cheng_corr, 'Fehler 1σ': taylor_err_one_sig, '2sig/t': two_sig_t,
            'Unkorr. Montefehler Erfolgsrate': age_uncorr_fractions, 'Korr. Montefehler Erfolgsrate': age_corr_fractions
        })

        calc_units = ['', '', 'gem.+korr.', '(abso.)', 'gem.+korr.', '(abso.)', 'gem.',
                      '(abso.)', '(fg)', '(pg/g)', '(abs.)', '(dpm/g)', '(abso.)',
                      '(ng)', '(μg/g)', '(abso.)', '(dpm/g)', '(abso.)', 'Akt. Ver.',
                      '(abso.)', 'Akt. Ver.', '(abso.)', '(ng)', '(ng/g)', '(abso.)',
                      '(dpm/g)', '(abso.)', '(fg)', '(pg/g)', '(abso.)',
                      '(dpmg/g)', '(abso.)', '', '(abso.)', '(o/oo)', '(abso.) o/oo',
                      'Akt. Ver.', '(abso.)', 'Akt.Ver.', '(abso.)', '(ka)', '(ka)', '(%)',
                      'Akt. Ver.', '(abso.)', 'Akt. Ver. initial', '(abso.)', '(ka)', '(ka)',
                      'Taylor 1. Ord.', '(%)', '', self.tiefe_unit, '(o/oo)', '(abso.) o/oo',
                      '(a BP)', '(a)', '(%)', '(%)', '(%)']

        calc_units_frame = pd.DataFrame(dict(zip(self.calc.columns, calc_units)), index=[''])

        self.calc = pd.concat([self.calc.iloc[:0], calc_units_frame, self.calc[0:]])

        # Create results sheet dataframe

        u238unitfactor = 1
        u238unit = '(μg/g)'
        if self.constantsType == 'stalag':
            u238unitfactor = 1000
            u238unit = '(ng/g)'

        self.results = pd.DataFrame({
            'Lab. #': list(self.metadata['Lab. #']), 'Bezeich.': list(self.metadata['Bezeich.']),
            '238U': list(u238unitfactor * u238mugg), 'Fehler1': list(u238unitfactor * u238mugg_err),
            '232Th': list(th232ngg), 'Fehler2': list(th232ngg_err),
            '230Th/238U': list(a230238_corr), 'Fehler3': list(a230238_corr_err),
            '230Th/232Th': list(a230232), 'Fehler4': list(a230232_err),
            'd234U korr': list(d234U), 'Fehler5': list(d234U_err),
            'Alter (unkorr.)': list(age_uncorr), 'Fehler6': list(age_uncorr_errors),
            'Alter (korr.)': list(age_corr), 'Fehler7': list(age_corr_errors),
            'd234U (initial)': list(d234U_init), 'Fehler8': list(d234U_init_err),
            'Tiefe': list(self.metadata['Tiefe'])
        },
            index=ratios.index)

        results_units = pd.DataFrame({'Lab. #': '', 'Bezeich.': '',
                                      '238U': u238unit, 'Fehler1': '(abso.)',
                                      '232Th': '(ng/g)', 'Fehler2': '(abso.)',
                                      '230Th/238U': '(Akt.Ver)', 'Fehler3': '(abso.)',
                                      '230Th/232Th': '(Akt.Ver.)', 'Fehler4': '(abso.)',
                                      'd234U korr': '(o/oo)', 'Fehler5': '(abso.) (o/oo)',
                                      'Alter (unkorr.)': '(ka)', 'Fehler6': '(ka)',
                                      'Alter (korr.)': '(ka)', 'Fehler7': '(ka)',
                                      'd234U (initial)': '(o/oo)', 'Fehler8': '(abso.) (o/oo)',
                                      'Tiefe': self.tiefe_unit}, index=[''])

        self.results = pd.concat([self.results.iloc[:0], results_units, self.results[0:]])

        # Prepare dataframe for constants sheet
        dfConstants = pd.DataFrame({**self.specific_constants, **self.constants}, index=[''])
        dfConstants = dfConstants.transpose()
        dfConstants.reset_index(level=0, inplace=True)

        dfOptions = pd.DataFrame(options_dict, index=[''])
        dfOptions = dfOptions.transpose()
        dfOptions.reset_index(level=0, inplace=True)

        results_dict = {'Input': self.input, 'Calc': self.calc, 'Results': self.results, 'Constants': dfConstants,
                        'Options': dfOptions}

        if write_results_file:
            self.writeToFile(results_dict, output_path=output_path)
        else:
            return results_dict

    def writeToFile(self, results_dict, fileTitle='Results', output_path=None):
        writer = ExcelWriter(self.data_root_folder + '\\{}.xlsx'.format(fileTitle), engine='xlsxwriter')
        ExcelFormatter.format(writer, results_dict)
        writer.save()

        if output_path is not None:
            writer = ExcelWriter(os.path.join(output_path, '{} {}.xlsx'.format(fileTitle, Util.sortableTimestamp())),
                                 engine='xlsxwriter')
            ExcelFormatter.format(writer, results_dict)
            writer.save()