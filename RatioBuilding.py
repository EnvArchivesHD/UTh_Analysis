import os
import pandas as pd
import numpy as np
from pandas import ExcelWriter
import scipy.interpolate
import ExcelFormatter
import DataFolderUtil
import Util
from scipy.stats import median_abs_deviation, iqr


class RatioBuilder:

    def __init__(self):
        self.data_root_folder = None
        self.ratios = None
        self.mean_option = 'median'
        self.dev_option = 'std'

    def set_path(self, path):
        self.data_root_folder = path

    def set_constants(self, constants):
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

        self.lambda234 = constants['l234']
        self.lambda238 = constants['l238']
        self.lambda230 = constants['l230']
        self.lambda232 = constants['l232']

        self.th229SubU238 = constants['th229SubU238']
        self.th230SubU238 = constants['th230SubU238']

    def set_specific_constants(self, specific_constants):
        useBlank = specific_constants['Blank']
        if useBlank:
            self.blk = 1
        else:
            self.blk = 0
        self.yield_Th = specific_constants['Yield_Th']
        self.yield_U = specific_constants['Yield_U']
        self.gain = specific_constants['Gain']
        self.tailShift = specific_constants['Tail shift']

    def set_options(self, mean_option='median', dev_option='std'):
        self.mean_option = mean_option
        self.dev_option = dev_option

    def post_904IC(self, data, i, labNr, tail_mat_cup, ThH_plus, blk, datablkm, UH_plus, cps, yield_U, R34_33, tail_mat,
                   R35_33,
                   tail_mat_th, R30_29, yield_Th, mf48, mf36, mf56, mf68, mf92, mf38, mf35,
                   mf43, mf45, mf09, mf29, mf34, mf58, mf02):

        data33 = data[:, 0] - data[:, 4] * tail_mat_cup[3] - data[:, 7] * ThH_plus - blk * datablkm[i, 0]  # U233

        data34 = data[:, 1] - UH_plus * data33 * cps * yield_U - data33 * R34_33 * cps * yield_U - data[:, 4] * \
                 tail_mat[4] * cps * yield_U - blk * datablkm[i, 1]  # U234

        data35 = (data[:, 2] - (data[:, 1] * UH_plus) / (cps * yield_U)) - data33 * R35_33 - data[:, 4] * tail_mat_cup[
            5] - blk * datablkm[i, 2]  # U235

        data36 = data[:, 3] - UH_plus * data[:, 2] - data[:, 4] * tail_mat_cup[6] - blk * datablkm[i, 3]  # U236

        data38 = data[:, 4] - blk * datablkm[i, 4]  # U238

        data29 = data[:, 8] - data[:, 4] * tail_mat[0] * cps * yield_U - tail_mat_th[0] * cps * yield_Th * data[:,
                                                                                                           7] - blk * \
                 datablkm[i, 7] - self.th229SubU238 * data[:, 4]  # Th229

        data30 = data[:, 6] - ThH_plus * data29 - data29 * R30_29 - data[:, 4] * tail_mat[1] * cps * yield_U - \
                 tail_mat_th[1] * cps * yield_Th * data[:, 7] - blk * datablkm[i, 5] - self.th230SubU238 * data[:,
                                                                                                           4]  # Th230 U

        data32 = data[:, 7] - data[:, 4] * tail_mat_cup[2] - blk * datablkm[i, 6]  # Th232

        self.intensities_dict[labNr] = pd.DataFrame(
            {
                'Cycle': list(np.arange(1, len(data29) + 1)),
                '229Th': list(data29),
                '230Th': list(data30),
                '232Th': list(data32),
                '233U': list(data33),
                '234U': list(data34),
                '235U': list(data35),
                '236U': list(data36),
                '238U': list(data38)
            }
        )

        # calculating atomic ratios, mass fractionation correction, 2 sigma outlier test
        R58d = data35 / data38  # U235/U238 for mass fractionation correction

        R58u = data35 / data38  # U235/U238 for monitoring machine drift
        [R58u, errR58u, R58u_, errRel58u] = self.outliertest(
            R58u)  # output: outlier corrected R58, 2sigma SE, mean, 2sigma relative SE

        R58 = data35 / data38 * (1 / self.NR85 / R58d) ** mf58  # U235/U238
        [R58, errR58, R58_, errRel58] = self.outliertest(R58)

        R34 = data33 / (data34 / (cps * yield_U)) * (1 / self.NR85 / R58d) ** mf34  # U233/U234
        [R34, errR34, R34_, errRel34] = self.outliertest(R34)

        R56 = data35 / data36 * (1 / self.NR85 / R58d) ** mf56  # U235/U236
        [R56, errR56, R56_, errRel56] = self.outliertest(R56)

        R48 = (data34 / (cps * yield_U)) / data38 * (1 / self.NR85 / R58d) ** mf48  # U234/U238
        [R48, errR48, R48_, errRel48] = self.outliertest(R48)

        R09 = data30 / data29 * (1 / self.NR85 / R58d) ** mf09  # Th230/Th229
        [R09, errR09, R09_, errRel09] = self.outliertest(R09)

        R29 = data32 / (data29 / (cps * yield_Th)) * (1 / self.NR85 / R58d) ** mf29  # Th232/Th229
        [R29, errR29, R29_, errRel29] = self.outliertest(R29)

        R43 = (data34 / (cps * yield_U)) / data33 * (1 / self.NR85 / R58d) ** mf43  # U233/U234
        [R43, errR43, R43_, errRel43] = self.outliertest(R43)

        R92 = (data29 / (cps * yield_Th)) / data32 * (1 / self.NR85 / R58d) ** mf92  # Th232/Th229
        [R92, errR92, R92_, errRel92] = self.outliertest(R92)

        R36 = data33 / data36 * (1 / self.NR85 / R58d) ** mf36  # U233/U234
        [R36, errR36, R36_, errRel36] = self.outliertest(R36)

        R45 = (data34 / (cps * yield_U)) / data35 * (1 / self.NR85 / R58d) ** mf45  # U233/U234
        [R45, errR45, R45_, errRel45] = self.outliertest(R45)

        R02 = (data30 / (cps * yield_Th)) / data32 * (1 / self.NR85 / R58d) ** mf02  # Th230/Th229
        [R02, errR02, R02_, errRel02] = self.outliertest(R02)

        R38 = data33 / data38 * (1 / self.NR85 / R58d) ** mf38  # U233/U238
        [R38, errR38, R38_, errRel38] = self.outliertest(R38)

        R68 = data36 / data38 * (1 / self.NR85 / R58d) ** mf68  # U236/U238
        [R68, errR68, R68_, errRel68] = self.outliertest(R68)

        R35 = data33 / data35 * (1 / self.NR85 / R58d) ** mf35  # U233/U235
        [R35, errR35, R35_, errRel35] = self.outliertest(R35)

        return R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_, errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_, errRel35

    def post_90IC(self, data, i, labNr, tail_mat_cup, ThH_plus, blk, gain13, datablkm, UH_plus, cps, yield_U, R34_33,
                  tail_mat,
                  R35_33,
                  tail_mat_th, R30_29, yield_Th, mf48, mf36, mf56, mf68, mf92, mf38, mf35,
                  mf43, mf45, mf09, mf29, mf34, mf58, mf02):

        data33 = data[:, 0] - data[:, 4] * tail_mat_cup[3] - data[:, 7] * ThH_plus - blk * datablkm[i, 0]  # U233

        data34 = gain13 * data[:, 1] - UH_plus * data33 - data33 * R34_33 - data[:, 4] * tail_mat_cup[4] - blk * \
                 datablkm[i, 1] / (cps * yield_U)  # U234

        data35 = (data[:, 2] - data[:, 1] * UH_plus * gain13) - data33 * R35_33 - data[:, 4] * tail_mat_cup[5] - blk * \
                 datablkm[i, 2]  # U235

        data36 = data[:, 3] - UH_plus * data[:, 2] - data[:, 4] * tail_mat_cup[6] - blk * datablkm[i, 3]  # U236

        data38 = data[:, 4] - blk * datablkm[i, 4]  # U238

        data29 = data[:, 8] - data[:, 4] * tail_mat[0] * cps * yield_U - tail_mat_th[0] * cps * yield_Th * data[:,
                                                                                                           7] - blk * \
                 datablkm[i, 7] - self.th229SubU238 * data[:, 4]  # Th229

        data30 = data[:, 6] - ThH_plus * data29 - data29 * R30_29 - data[:, 4] * tail_mat[1] * cps * yield_U - \
                 tail_mat_th[1] * cps * yield_Th * data[:, 7] - blk * datablkm[i, 5] - self.th230SubU238 * data[:,
                                                                                                           4]  # Th230

        data32 = data[:, 7] - data[:, 4] * tail_mat_cup[2] - blk * datablkm[i, 6]  # Th232

        self.intensities_dict[labNr] = pd.DataFrame(
            {
                'Cycle': list(np.arange(1, len(data29) + 1)),
                '229Th': list(data29),
                '230Th': list(data30),
                '232Th': list(data32),
                '233U': list(data33),
                '234U': list(data34),
                '235U': list(data35),
                '236U': list(data36),
                '238U': list(data38)
            }
        )

        # calculating atomic ratios, mass fractionation correction, 2 sigma outlier test
        R58d = data35 / data38  # U235/U238 for mass fractionation correction

        R58u = data35 / data38  # U235/U238 for monitoring machine drift
        [R58u, errR58u, R58u_, errRel58u] = self.outliertest(
            R58u)  # output: outlier corrected R58, 2sigma SE, mean, 2sigma relative SE

        R58 = data35 / data38 * (1 / self.NR85 / R58d) ** mf58  # U235/U238
        [R58, errR58, R58_, errRel58] = self.outliertest(R58)

        R34 = data33 / data34 * (1 / self.NR85 / R58d) ** mf34  # U233/U234
        [R34, errR34, R34_, errRel34] = self.outliertest(R34)

        R56 = data35 / data36 * (1 / self.NR85 / R58d) ** mf56  # U235/U236 and mass fractionation
        [R56, errR56, R56_, errRel56] = self.outliertest(R56)

        R48 = data34 / data38 * (1 / self.NR85 / R58d) ** mf48  # U234/U238
        [R48, errR48, R48_, errRel48] = self.outliertest(R48)

        R09 = data30 / data29 * (1 / self.NR85 / R58d) ** mf09  # Th230/Th229
        [R09, errR09, R09_, errRel09] = self.outliertest(R09)

        R29 = data32 / (data29 / (cps * yield_Th)) * (1 / self.NR85 / R58d) ** mf29  # Th232/Th229
        [R29, errR29, R29_, errRel29] = self.outliertest(R29)

        R43 = data34 / data33 * (1 / self.NR85 / R58d) ** mf43  # U233/U234
        [R43, errR43, R43_, errRel43] = self.outliertest(R43)

        R92 = ((data29 / cps) * yield_Th / data32) * (1 / self.NR85 / R58d) ** mf92  # Th232/Th229
        [R92, errR92, R92_, errRel92] = self.outliertest(R92);

        R36 = data33 / data36 * (1 / self.NR85 / R58d) ** mf36  # U233/U234
        [R36, errR36, R36_, errRel36] = self.outliertest(R36)

        R45 = data34 / data35 * (1 / self.NR85 / R58d) ** mf45  # U233/U234
        [R45, errR45, R45_, errRel45] = self.outliertest(R45)

        R02 = (data30 / (cps * yield_Th)) / data32 * (1 / self.NR85 / R58d) ** mf02  # Th230/Th229
        [R02, errR02, R02_, errRel02] = self.outliertest(R02)

        R38 = data33 / data38 * (1 / self.NR85 / R58d) ** mf38  # U233/U238
        [R38, errR38, R38_, errRel38] = self.outliertest(R38)

        R68 = data36 / data38 * (1 / self.NR85 / R58d) ** mf68  # U236/U238
        [R68, errR68, R68_, errRel68] = self.outliertest(R68)

        R35 = data33 / data35 * (1 / self.NR85 / R58d) ** mf35  # U233/U235
        [R35, errR35, R35_, errRel35] = self.outliertest(R35)

        return R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_, errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_, errRel35

    def post_0IC(self, data, i, labNr, tail_mat_cup, ThH_plus, blk, gain13, datablkm, UH_plus, cps, yield_U, R34_33,
                 tail_mat,
                 R35_33,
                 tail_mat_th, tail_mat_th_cup, R30_29, yield_Th, mf48, mf36, mf56, mf68, mf92, mf38,
                 mf35,
                 mf43, mf45, mf09, mf29, mf34, mf58, mf02):

        data33 = data[:, 0] - data[:, 4] * tail_mat_cup[3] - data[:, 7] * ThH_plus - blk * datablkm[i, 0]  # U233

        data34 = gain13 * data[:, 1] - UH_plus * data33 - data33 * R34_33 - data[:, 4] * tail_mat_cup[4] - blk * \
                 datablkm[i, 1]  # U234

        data35 = (data[:, 2] - data[:, 1] * UH_plus * gain13) - data33 * R35_33 - data[:, 4] * tail_mat_cup[5] - blk * \
                 datablkm[i, 2]  # U235

        data36 = data[:, 3] - UH_plus * data[:, 2] - data[:, 4] * tail_mat_cup[6] - blk * datablkm[i, 3]  # U236

        data38 = data[:, 4] - blk * datablkm[i, 4]  # U238

        data29 = data[:, 5] - data[:, 4] * tail_mat_cup[0] - tail_mat_th_cup[0] * data[:, 7] - blk * datablkm[
            i, 7] - data[:, 4] * self.th229SubU238 / cps  # Th229

        data30 = data[:, 6] - ThH_plus * data29 * cps * yield_Th - data29 * R30_29 * cps * yield_Th - data[:, 4] * \
                 tail_mat[1] * cps * yield_U - tail_mat_th[1] * cps * yield_Th * data[:, 7] - blk * datablkm[
                     i, 5] - data[:, 4] * self.th230SubU238  # Th230

        data32 = data[:, 7] - data[:, 4] * tail_mat_cup[2] - blk * datablkm[6, i]  # Th232

        self.intensities_dict[labNr] = pd.DataFrame(
            {
                'Cycle': list(np.arange(1, len(data29) + 1)),
                '229Th': list(data29),
                '230Th': list(data30),
                '232Th': list(data32),
                '233U': list(data33),
                '234U': list(data34),
                '235U': list(data35),
                '236U': list(data36),
                '238U': list(data38)
            }
        )

        # calculating atomic ratios, mass fractionation correction, 2 sigma outlier test
        R58d = data35 / data38  # U235/U238 for mass fractionation correction

        R58u = data35 / data38  # U235/U238 for monitoring machine drift
        [R58u, errR58u, R58u_, errRel58u] = self.outliertest(
            R58u)  # output: outlier corrected R58, 2sigma SE, mean, 2sigma relative SE

        R58 = data35 / data38 * (1 / self.NR85 / R58d) ** mf58  # U235/U238
        [R58, errR58, R58_, errRel58] = self.outliertest(R58)

        R34 = data33 / data34 * (1 / self.NR85 / R58d) ** mf34  # U233/U234
        [R34, errR34, R34_, errRel34] = self.outliertest(R34)

        R56 = data35 / data36 * (1 / self.NR85 / R58d) ** mf56  # U235/U236 and mass fractionation
        [R56, errR56, R56_, errRel56] = self.outliertest(R56)

        R48 = data34 / data38 * (1 / self.NR85 / R58d) ** mf48  # U234/U238
        [R48, errR48, R48_, errRel48] = self.outliertest(R58u)

        R09 = (data30 / (cps * yield_Th)) / data29 * (1 / self.NR85 / R58d) ** mf09  # Th230/Th229
        [R09, errR09, R09_, errRel09] = self.outliertest(R09)

        R29 = data32 / data29 * (1 / self.NR85 / R58d) ** mf29  # Th232/Th229
        [R29, errR29, R29_, errRel29] = self.outliertest(R29)

        R43 = data34 / data33 * (1 / self.NR85 / R58d) ** mf43  # U233/U234
        [R43, errR43, R43_, errRel43] = self.outliertest(R43)

        R92 = data29 / data32 * (1 / self.NR85 / R58d) ** mf92  # Th232/Th229
        [R92, errR92, R92_, errRel92] = self.outliertest(R92)

        R36 = data33 / data36 * (1 / self.NR85 / R58d) ** mf36  # U233/U234
        [R36, errR36, R36_, errRel36] = self.outliertest(R36)

        R45 = data34 / data35 * (1 / self.NR85 / R58d) ** mf45  # U233/U234
        [R45, errR45, R45_, errRel45] = self.outliertest(R45)

        R02 = (data30 / (cps * yield_Th)) / data32 * (1 / self.NR85 / R58d) ** mf02  # Th230/Th229
        [R02, errR02, R02_, errRel02] = self.outliertest(R02)

        R38 = data33 / data38 * (1 / self.NR85 / R58d) ** mf38  # U233/U238
        [R38, errR38, R38_, errRel38] = self.outliertest(R38)

        R68 = data36 / data38 * (1 / self.NR85 / R58d) ** mf68  # U236/U238
        [R68, errR68, R68_, errRel68] = self.outliertest(R68)

        R35 = data33 / data35 * (1 / self.NR85 / R58d) ** mf35  # U233/U235
        [R35, errR35, R35_, errRel35] = self.outliertest(R35)

        return R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_, errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_, errRel35

    def post_allcup(self, data, i, labNr, tail_mat_cup, ThH_plus, blk, gain13, datablkm, UH_plus, cps, yield_U, R34_33,
                    tail_mat, R35_33,
                    tail_mat_th, tail_mat_th_cup, R30_29, yield_Th, mf48, mf36, mf56, mf68, mf92,
                    mf38, mf35,
                    mf43, mf45, mf09, mf29, mf34, mf58, mf02):

        data33 = data[:, 0] - data[:, 4] * tail_mat_cup[3] - data[:, 7] * ThH_plus - blk * datablkm[i, 0]  # U233

        data34 = gain13 * data[:, 1] - UH_plus * data33 - data33 * R34_33 - data[:, 4] * tail_mat_cup[4] - blk * \
                 datablkm[i, 1] / cps  # U234

        data35 = (data[:, 2] - data[:, 1] * UH_plus * gain13) - data33 * R35_33 - data[:, 4] * tail_mat_cup[5] - blk * \
                 datablkm[i, 2]  # U235

        data36 = data[:, 3] - UH_plus * data[:, 2] - data[:, 4] * tail_mat_cup[6] - blk * datablkm[i, 3]  # U236

        data38 = data[:, 4] - blk * datablkm[i, 4]  # U238

        data29 = data[:, 5] - data[:, 4] * tail_mat_cup[0] - tail_mat_th_cup[0] * data[:, 7] - blk * datablkm[
            i, 7] / cps - data[:, 4] * self.th229SubU238 / cps  # Th229

        data30 = gain13 * data[:, 6] - ThH_plus * data29 - data29 * R30_29 - data[:, 4] * tail_mat_cup[1] - \
                 tail_mat_th_cup[1] * data[:, 7] - blk * datablkm[i, 5] / cps - data[:,
                                                                                4] * self.th230SubU238 / cps  # Th230

        data32 = data[:, 7] - data[:, 4] * tail_mat_cup[2] - blk * datablkm[i, 6]  # Th232

        self.intensities_dict[labNr] = pd.DataFrame(
            {
                'Cycle': list(np.arange(1, len(data29) + 1)),
                '229Th': list(data29),
                '230Th': list(data30),
                '232Th': list(data32),
                '233U': list(data33),
                '234U': list(data34),
                '235U': list(data35),
                '236U': list(data36),
                '238U': list(data38)
            }
        )

        # calculating atomic ratios, mass fractionation correction, 2 sigma outlier test
        R58d = data35 / data38  # U235/U238 for mass fractionation correction

        R58u = data35 / data38  # U235/U238 for monitoring machine drift
        [R58u, errR58u, R58u_, errRel58u] = self.outliertest(
            R58u)  # output: outlier corrected R58, 2sigma SE, mean, 2sigma relative SE

        R58 = data35 / data38 * (1 / self.NR85 / R58d) ** mf58  # U235/U238
        [R58, errR58, R58_, errRel58] = self.outliertest(R58)

        R34 = data33 / data34 * (1 / self.NR85 / R58d) ** mf34  # U233/U234
        [R34, errR34, R34_, errRel34] = self.outliertest(R34)

        R56 = data35 / data36 * (1 / self.NR85 / R58d) ** mf56  # U235/U236 and mass fractionation
        [R56, errR56, R56_, errRel56] = self.outliertest(R56)

        R48 = data34 / data38 * (1 / self.NR85 / R58d) ** mf48  # U234/U238
        [R48, errR48, R48_, errRel48] = self.outliertest(R48)

        R09 = data30 / data29 * (1 / self.NR85 / R58d) ** mf09  # Th230/Th229
        [R09, errR30, R09_, errRel09] = self.outliertest(R09)

        R29 = data32 / data29 * (1 / self.NR85 / R58d) ** mf29  # Th232/Th229
        [R29, errR32, R29_, errRel29] = self.outliertest(R29)

        R43 = data34 / data33 * (1 / self.NR85 / R58d) ** mf43  # U233/U234
        [R43, errR43, R43_, errRel43] = self.outliertest(R43)

        R92 = data29 / data32 * (1 / self.NR85 / R58d) ** mf92  # Th232/Th229
        [R92, errR92, R92_, errRel92] = self.outliertest(R92)

        R36 = data33 / data36 * (1 / self.NR85 / R58d) ** mf36  # U233/U234
        [R36, errR36, R36_, errRel36] = self.outliertest(R36)

        R45 = data34 / data35 * (1 / self.NR85 / R58d) ** mf45  # U233/U234
        [R45, errR45, R45_, errRel45] = self.outliertest(R45)

        R02 = data30 / data32 * (1 / self.NR85 / R58d) ** mf02  # Th230/Th229
        [R02, errR02, R02_, errRel02] = self.outliertest(R02)

        R38 = data33 / data38 * (1 / self.NR85 / R58d) ** mf38  # U233/U238
        [R38, errR38, R38_, errRel38] = self.outliertest(R38)

        R68 = data36 / data38 * (1 / self.NR85 / R58d) ** mf68  # U236/U238
        [R68, errR68, R68_, errRel68] = self.outliertest(R68)

        R35 = data33 / data35 * (1 / self.NR85 / R58d) ** mf35  # U233/U235
        [R35, errR35, R35_, errRel35] = self.outliertest(R35)

        return R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_, errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_, errRel35

    def yhas_uranium(self):
        # xnew = np.linspace(228.5, 237.5, num=200)

        old_path = os.getcwd()
        os.chdir(self.data_root_folder)
        listyu = os.listdir('yhas_u')
        namesyu = np.array(listyu)

        if self.tailShift:
            x_axis_tail_u = np.array([227.5, 233.5, 236.5, 236.7, 237.05, 237.5])  # half-masses tailing SEM/RPQ
        else:
            x_axis_tail_u = np.array([228.5, 233.5, 236.5, 236.7, 237.05, 237.5])  # half-masses tailing SEM/RPQ
        os.chdir('yhas_u')

        for i in range(len(namesyu)):  # read yhas data
            aa = pd.read_table(namesyu[i], sep='\t')  # read in files from neptune software
            raw = pd.DataFrame(aa)

            sub_raw = raw['Unnamed: 1']
            peakstct = 'C\(C\)'
            searchIC2 = sub_raw.str.contains(peakstct)

            peakstrt = 'Mean'
            searchMean = sub_raw.str.contains(peakstrt)

            for k in range(len(searchMean)):
                if searchMean[k] == True:
                    rowtu = k
            dummyu = raw.loc[
                rowtu, ['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']]
            dummyu = [float(x) for x in dummyu]
            dummyu = np.array(dummyu)

            u238tail = raw.loc[rowtu, ['Unnamed: 9']]
            u238tail = float(u238tail)
            u238tail = np.array(u238tail)
            self.u238tail = np.mean(u238tail[u238tail != 0])
            uh1 = raw.loc[rowtu, ['Unnamed: 8']]
            uh1 = float(uh1)
            uh1 = np.array(uh1)
            uh2 = raw.loc[rowtu, ['Unnamed: 9']]
            uh2 = float(uh2)
            uh2 = np.array(uh2)
            uh = uh1 / (uh2 * self.cps)
            self.UH_plus = np.mean(uh[uh != 0])

            check = 0
            for m in range(len(dummyu)):
                if dummyu[m] == 0:
                    check = check + 1
                else:
                    check = check
            if check == len(dummyu):
                dummyu = []

        self.x_axis_tail_u = x_axis_tail_u
        self.aatsu = dummyu

        self.f_u238 = scipy.interpolate.PchipInterpolator(self.x_axis_tail_u, self.aatsu)

        os.chdir(old_path)

        self.uranium_tailing()

    def yhas_thorium(self):
        old_path = os.getcwd()
        os.chdir(self.data_root_folder)
        listyth = os.listdir('yhas_th')
        namesyth = np.array(listyth)

        x_axis_tail_th = np.array([227.5, 228.5, 229.5, 230.5, 231.5])  # half-masses tailing SEM/RPQ
        os.chdir('yhas_th')

        for i in range(len(namesyth)):  # read yhas data
            aa = pd.read_table(namesyth[i], sep='\t')  # read in files from neptune software
            raw = pd.DataFrame(aa)

            sub_raw = raw['Unnamed: 1']
            peakstrt = 'Mean'
            searchMean = sub_raw.str.contains(peakstrt)

            for k in range(len(searchMean)):
                if searchMean[k] == True:
                    rowt = k
            dummyt = raw.loc[rowt, ['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6']]
            dummyt = [float(x) for x in dummyt]
            dummyt = np.array(dummyt)

            th232tail = raw.loc[rowt, ['Unnamed: 7']]
            th232tail = float(th232tail)
            th232tail = np.array(th232tail)
            self.th232tail = np.mean(th232tail[th232tail != 0])
            thh1 = raw.loc[rowt, ['Unnamed: 8']]
            thh1 = float(thh1)
            thh1 = np.array(thh1)
            thh2 = raw.loc[rowt, ['Unnamed: 7']]
            thh2 = float(thh2)
            thh2 = np.array(thh2)
            thh = thh1 / (thh2 * self.cps)

            ThH_plus = np.mean(thh[thh != 0])

            check = 0
            for m in range(len(dummyt)):
                if dummyt[m] == 0:
                    check = check + 1
                else:
                    check = check
            if check == len(dummyt):
                dummyt = []

        self.x_axis_tail_th = x_axis_tail_th
        self.aats = dummyt

        self.g_th232 = scipy.interpolate.PchipInterpolator(self.x_axis_tail_th, self.aats)

        self.ThH_plus = ThH_plus

        os.chdir(old_path)

        self.thorium_tailing()

    def uranium_tailing(self):
        rpq_factor_u = [164, 94, 46, 37, 18, 7, 5, 4]  # RPQon/RPQoff

        f_u238 = self.f_u238
        tail_mat = [f_u238(229), f_u238(230), f_u238(232), f_u238(233), f_u238(234), f_u238(235), f_u238(236),
                    f_u238(237)] / (self.yield_U * self.cps * self.u238tail)

        if tail_mat[0] < 1e-10:  # empirically determined threshold for too low signals
            tail_mat[0] = 1e-10
        if tail_mat[1] < 4e-10:  # empirically determined threshold for too low signals
            tail_mat[1] = 4e-10

        for j in range(len(tail_mat)):  # Sets all negative elements of {tail_mat_cup} to zero
            if tail_mat[j] < 0:
                tail_mat[j] = 0

        tail_mat_cup = tail_mat * rpq_factor_u  # tailing U-238 on cup converted from tailing on SEM/RPQ using factors

        self.tail_mat = tail_mat
        self.tail_mat_cup = tail_mat_cup

        self.uTailData = pd.DataFrame(
            {
                '229': [self.tail_mat[0], self.tail_mat_cup[0]],
                '230': [self.tail_mat[1], self.tail_mat_cup[1]],
                '232': [self.tail_mat[2], self.tail_mat_cup[2]],
                '233': [self.tail_mat[3], self.tail_mat_cup[3]],
                '234': [self.tail_mat[4], self.tail_mat_cup[4]],
                '235': [self.tail_mat[5], self.tail_mat_cup[5]],
                '236': [self.tail_mat[6], self.tail_mat_cup[6]],
                '237': [self.tail_mat[7], self.tail_mat_cup[7]],
            }, index=['Tailing U SEM', 'Tailing U Cup'])

    def thorium_tailing(self):
        rpq_factor_th = [52, 10]  # RPQon/RPQoff

        g_th232 = self.g_th232
        tail_mat_th = [g_th232(229), g_th232(230)] / (
                self.yield_Th * self.cps * self.th232tail)  # tailing Th-232 on SEM/RPQ

        if tail_mat_th[0] < 2e-9:  # empirically determined threshold for too low signals
            tail_mat_th[0] = 2e-9
        if tail_mat_th[1] < 6e-8:  # empirically determined threshold for too low signals
            tail_mat_th[1] = 6e-8

        tail_mat_th_cup = tail_mat_th * rpq_factor_th  # tailing Th-232 on cup

        self.tail_mat_th = tail_mat_th
        self.tail_mat_th_cup = tail_mat_th_cup

        self.thTailData = pd.DataFrame(
            {
                '229': [self.tail_mat_th[0], self.tail_mat_th_cup[0]],
                '230': [self.tail_mat_th[1], self.tail_mat_th_cup[1]]
            }, index=['Tailing Th SEM', 'Tailing Th Cup'])

        # RPQ_Norm_Th = tail_mat_th * self.cps
        # IC5_Norm_Th = tail_mat_th_cup * self.cps

    def calc_blank_correction(self):
        old_path = os.getcwd()

        folder_blank = self.data_root_folder + '\\blank'
        list_blank = os.listdir(folder_blank)
        names_blank = np.array(list_blank)
        names_blank = np.sort(names_blank)

        peakstra = '1:233U'
        peakstrb = 'Cup'
        peakstrc = '2:230Th'
        peakstrhelp = 'Cycle'

        datablkm = np.empty([len(names_blank), 8])
        if self.blk == 1.0:
            for k in range(len(names_blank)):
                os.chdir(folder_blank)
                bb = pd.read_table(names_blank[k], sep='\t')  # read in files from neptune software
                raw = pd.DataFrame(bb)
                sub_bb = raw['Unnamed: 1']
                searchCup = sub_bb.str.contains(peakstrb)
                colpb = 1
                for i in range(len(searchCup)):
                    if searchCup[i] == True:
                        rowpb = i
                sub_help = raw['Neptune Analysis Data Report']
                searchCycle = sub_help.str.contains(peakstrhelp)
                for i in range(len(searchCycle)):
                    if searchCycle[i] == True:
                        rowphelp = i
                rawnew = raw.iloc[rowphelp]
                search233U = rawnew.str.contains(peakstra)
                for i in range(len(search233U)):
                    if search233U[i] == True:
                        cola = i
                search230Th = rawnew.str.contains(peakstrc)
                for i in range(len(search230Th)):
                    if search230Th[i] == True:
                        colc = i

                os.chdir(self.data_root_folder)

                datablk = raw.iloc[(rowphelp + 1):(rowpb), (colpb + 1):(colpb + 6)]
                datablk = datablk.values
                datablk = datablk.astype(np.float)

                datablk2 = raw.iloc[(rowphelp + 1):(rowpb), (colc):(colc + 3)]
                datablk2 = datablk2.values
                datablk2 = datablk2.astype(np.float)

                datablk = np.append(datablk, datablk2, axis=1)

                smaller = np.mean(datablk, axis=0) + 0.5 * np.std(datablk, axis=0, ddof=1)
                larger = np.mean(datablk, axis=0) - 2 * np.std(datablk, axis=0, ddof=1)

                index1 = (rowpb) - (rowphelp + 1)
                index2 = ((colc + 3) - (colc)) + ((colpb + 6) - (colpb + 1))

                for m in range(index1):
                    for n in range(index2):
                        if ((datablk[m, n] > smaller[n]) or (datablk[m, n] < larger[n])):
                            datablk[m, n] = float('nan')
                        else:
                            datablk[m, n] = datablk[m, n]

                [nn, mm] = np.shape(datablk)
                for n in range(nn):
                    for m in range(mm):
                        if datablk[n, m] < 0:
                            datablk[n, m] = 0

                datablk_mean = np.nanmean(datablk, axis=0)

                datablkm[k, :] = datablk_mean

            blank = pd.DataFrame(
                {'Lab. #': self.labNrs, 'U-233': datablkm[:, 0], 'U-234': datablkm[:, 1], 'U-235': datablkm[:, 2],
                 'U-236': datablkm[:, 3],
                 'U-238': datablkm[:, 4], 'Th-230': datablkm[:, 5], 'Th-232': datablkm[:, 6], 'Th-229': datablkm[:, 7]},
                index=names_blank)
            writer = ExcelWriter(self.data_root_folder + '\\PrBlank.xlsx', engine='xlsxwriter')
            ExcelFormatter.format(writer, {'Sheet1': blank})
            writer.save()

        else:
            datablkm[:, :] = 0
            blank = pd.DataFrame(
                {'Lab. #': self.labNrs, 'U-233': datablkm[:, 0], 'U-234': datablkm[:, 1], 'U-235': datablkm[:, 2],
                 'U-236': datablkm[:, 3],
                 'U-238': datablkm[:, 4], 'Th-230': datablkm[:, 5], 'Th-232': datablkm[:, 6], 'Th-229': datablkm[:, 7]},
                index=names_blank)
            writer = ExcelWriter(self.data_root_folder + '\\PrBlank.xlsx', engine='xlsxwriter')
            ExcelFormatter.format(writer, {'Sheet1': blank})
            writer.save()

        self.datablkm = datablkm

        os.chdir(old_path)

    def data_correction(self):

        old_path = os.getcwd()

        folder_data = os.path.join(self.data_root_folder, 'data')
        list_data = os.listdir(folder_data)
        names_data = np.sort(np.array(list_data))

        # get the laboratory numbers from the data filenames
        self.labNrs = DataFolderUtil.getLabNrsFromList(names_data)
        standard = DataFolderUtil.findStandardNumber(self.data_root_folder)
        standardCount = 1
        # Modify lab nr strings to prevent overwriting in intensities sheet
        for i, labNr in enumerate(self.labNrs):
            if labNr == standard:
                self.labNrs[i] = self.labNrs[i] + '_{}'.format(standardCount)
                standardCount += 1

        self.yhas_uranium()
        self.yhas_thorium()
        self.calc_blank_correction()

        peakstrhelp = 'Cycle'

        self.intensities_dict = {}

        matrix_ratios = np.empty([len(names_data), 18])
        matrix_ratios_add = np.empty([len(names_data), 24])
        for i in range(len(names_data)):
            os.chdir(folder_data)
            cc = pd.read_table(names_data[i], sep='\t')  # read in files from Neptune software
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
            searchCycle = sub_help.str.contains(peakstrhelp)
            for k in range(len(searchCycle)):
                if searchCycle[k] == True:
                    rowphelp = k
            rawnew2 = raw.iloc[rowphelp]
            rawnew2 = rawnew2.values
            for j in range(len(rawnew2)):
                if rawnew2[j] == '1:233U':
                    col233 = j

            os.chdir(self.data_root_folder)

            data = raw.iloc[(rowphelp + 1):(rowCup), (col233):(col233 + 9)]

            data = data.values
            data = data.astype(np.float)

            if len(c3) == 3:
                [R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_,
                 errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_,
                 errRel35] = self.post_904IC(
                    data, i, self.labNrs[i], self.tail_mat_cup, self.ThH_plus, self.blk, self.datablkm, self.UH_plus,
                    self.cps,
                    self.yield_U, self.R34_33, self.tail_mat, self.R35_33,
                    self.tail_mat_th, self.R30_29, self.yield_Th, self.mf48, self.mf36,
                    self.mf56, self.mf68, self.mf92, self.mf38, self.mf35,
                    self.mf43, self.mf45, self.mf09, self.mf29, self.mf34, self.mf58,
                    self.mf02)  # measurement method: 234, 230, and 229 on SEM/RPQ
            elif len(c3) == 2:
                [R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_,
                 errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_,
                 errRel35] = self.post_90IC(
                    data, i, self.labNrs[i], self.tail_mat_cup, self.ThH_plus, self.blk, self.gain, self.datablkm,
                    self.UH_plus,
                    self.cps, self.yield_U, self.R34_33, self.tail_mat, self.R35_33,
                    self.tail_mat_th, self.R30_29, self.yield_Th, self.mf48, self.mf36,
                    self.mf56, self.mf68, self.mf92, self.mf38, self.mf35,
                    self.mf43, self.mf45, self.mf09, self.mf29, self.mf34, self.mf58,
                    self.mf02)  # measurement method: 230 and 229 on SEM/RPQ
            elif len(c3) == 1:
                [R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_,
                 errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_,
                 errRel35] = self.post_0IC(
                    data, i, self.labNrs[i], self.tail_mat_cup, self.ThH_plus, self.blk, self.gain, self.datablkm,
                    self.UH_plus,
                    self.cps, self.yield_U, self.R34_33, self.tail_mat, self.R35_33,
                    self.tail_mat_th, self.tail_mat_th_cup, self.R30_29, self.yield_Th,
                    self.mf48, self.mf36, self.mf56, self.mf68, self.mf92, self.mf38, self.mf35,
                    self.mf43, self.mf45, self.mf09, self.mf29, self.mf34, self.mf58,
                    self.mf02)  # measurement method: 230 on SEM/RPQ
            else:
                [R36_, errRel36, R58u_, errRel58u, R56_, errRel56, R43_, errRel43, R45_, errRel45, R48_, errRel48, R09_,
                 errRel09, R92_, errRel92, R02_, errRel02, R38_, errRel38, R68_, errRel68, R35_,
                 errRel35] = self.post_allcup(data, i, self.labNrs[i], self.tail_mat_cup, self.ThH_plus, self.blk,
                                              self.gain,
                                              self.datablkm, self.UH_plus, self.cps, self.yield_U, self.R34_33,
                                              self.tail_mat, self.R35_33, self.tail_mat_th, self.tail_mat_th_cup,
                                              self.R30_29, self.yield_Th, self.mf48,
                                              self.mf36, self.mf56, self.mf68, self.mf92, self.mf38, self.mf35,
                                              self.mf43, self.mf45, self.mf09, self.mf29, self.mf34, self.mf58,
                                              self.mf02)  # measurement method: all isotopes on cup

            matrix_ratios[i, :] = [R36_, errRel36 * 100, R58u_, errRel58u * 100, R56_, errRel56 * 100, R43_,
                                   errRel43 * 100, R45_, errRel45 * 100, R48_, errRel48 * 100, R09_, errRel09 * 100,
                                   R92_, errRel92 * 100, R02_, errRel02 * 100]
            matrix_ratios_add[i, :] = [R36_, errRel36 * 100, R58u_, errRel58u * 100, R56_, errRel56 * 100, R43_,
                                       errRel43 * 100, R45_, errRel45 * 100, R48_, errRel48 * 100, R09_, errRel09 * 100,
                                       R92_, errRel92 * 100, R02_, errRel02 * 100, R38_, errRel38 * 100, R68_,
                                       errRel68 * 100, R35_, errRel35 * 100]

        # reset labNrs
        self.labNrs = DataFolderUtil.getLabNrsFromList(names_data)

        # Save ratios to file

        self.ratios = pd.DataFrame({'Lab. #': self.labNrs, 'dU234': (matrix_ratios[:, 10] * self.lambda234 / self.lambda238 - 1) * 1000,
                                    'Error dU234 (abs.)': (matrix_ratios[:,
                                                           10] * self.lambda234 / self.lambda238) * matrix_ratios[:,
                                                                                                    11] / 100,
                                    'Ratio 233/236': matrix_ratios[:, 0], 'Error (%) 233/236': matrix_ratios[:, 1],
                                    'Ratio 235/238': matrix_ratios[:, 2], 'Error (%) 235/238': matrix_ratios[:, 3],
                                    'Ratio 235/236': matrix_ratios[:, 4], 'Error (%) 235/236': matrix_ratios[:, 5],
                                    'Ratio 234/233': matrix_ratios[:, 6], 'Error (%) 234/233': matrix_ratios[:, 7],
                                    'Ratio 234/235': matrix_ratios[:, 8], 'Error (%) 234/235': matrix_ratios[:, 9],
                                    'Ratio 234/238': matrix_ratios[:, 10], 'Error (%) 234/238': matrix_ratios[:, 11],
                                    'Ratio 230/229': matrix_ratios[:, 12], 'Error (%) 230/229': matrix_ratios[:, 13],
                                    'Ratio 229/232': matrix_ratios[:, 14], 'Error (%) 229/232': matrix_ratios[:, 15],
                                    'Ratio 230/232': matrix_ratios[:, 16], 'Error (%) 230/232': matrix_ratios[:, 17]},
                                   index=names_data)

        datacorr = self.ratios.copy()

        writer = ExcelWriter(self.data_root_folder + '\\Ratios.xlsx', engine='xlsxwriter')
        ExcelFormatter.format(writer, {'Ratios': datacorr})
        writer.save()

        # os.remove(data_root_folder + '\\Ratios_python_add.xlsx')
        datacorr_add = pd.DataFrame(
            {
                'Lab. #': self.labNrs,
                'Ratio 233/236': matrix_ratios_add[:, 0], 'Error (%) 233/236': matrix_ratios_add[:, 1],
                'Ratio 235/238': matrix_ratios_add[:, 2], 'Error (%) 235/238': matrix_ratios_add[:, 3],
                'Ratio 235/236': matrix_ratios_add[:, 4], 'Error (%) 235/236': matrix_ratios_add[:, 5],
                'Ratio 234/233': matrix_ratios_add[:, 6], 'Error (%) 234/233': matrix_ratios_add[:, 7],
                'Ratio 234/235': matrix_ratios_add[:, 8], 'Error (%) 234/235': matrix_ratios_add[:, 9],
                'Ratio 234/238': matrix_ratios_add[:, 10], 'Error (%) 234/238': matrix_ratios_add[:, 11],
                'Ratio 230/229': matrix_ratios_add[:, 12], 'Error (%) 230/229': matrix_ratios_add[:, 13],
                'Ratio 229/232': matrix_ratios_add[:, 14], 'Error (%) 229/232': matrix_ratios_add[:, 15],
                'Ratio 230/232': matrix_ratios_add[:, 16], 'Error (%) 230/232': matrix_ratios_add[:, 17],
                'Ratio 233/238': matrix_ratios_add[:, 18], 'Error (%) 233/238': matrix_ratios_add[:, 19],
                'Ratio 236/238': matrix_ratios_add[:, 20], 'Error (%) 236/238': matrix_ratios_add[:, 21],
                'Ratio 233/235': matrix_ratios_add[:, 22], 'Error (%) 233/235': matrix_ratios_add[:, 23],
            }, index=names_data
        )
        writer = ExcelWriter(self.data_root_folder + '\\Ratios_add.xlsx', engine='xlsxwriter')
        ExcelFormatter.format(writer, {'Ratios': datacorr_add})
        writer.save()

        # Save tailing to file

        writer = ExcelWriter(self.data_root_folder + '\\Tailing.xlsx', engine='xlsxwriter')

        # Get Tailing in CPS / V_Uran or CPS / V_Thorium
        dfUTail = self.uTailData.loc[['Tailing U SEM'],:] * self.cps * self.yield_U
        dfThTail = self.thTailData.loc[['Tailing Th SEM'],:] * self.cps * self.yield_Th

        dfUTail = pd.concat([pd.DataFrame([['[CPS/V_U]'] * len(dfUTail.columns)], columns=dfUTail.columns), dfUTail])
        dfThTail = pd.concat([pd.DataFrame([['[CPS/V_Th]'] * len(dfThTail.columns)], columns=dfThTail.columns), dfThTail])

        ExcelFormatter.format(writer, {'U-Tailing': dfUTail,
                                       'Th-Tailing': dfThTail})
        writer.save()

        # Save intensitites to file
        units = {
            'Cycle': '',
            '229Th': '[V]' if len(c3) not in [2, 3] else '[CPS]',
            '230Th': '[V]' if len(c3) not in [1, 2, 3] else '[CPS]',
            '232Th': '[V]',
            '233U': '[V]',
            '234U': '[V]' if len(c3) not in [3] else '[CPS]',
            '235U': '[V]',
            '236U': '[V]',
            '238U': '[V]'
        }

        for labNr in self.intensities_dict:
            df = self.intensities_dict[labNr]

            medians = ['Median']
            errs = ['Error (%)']
            for col in df.columns[1:]:
                _, _, mean, err = self.outliertest(df.loc[:, col])
                medians.append(mean)
                errs.append(err * 100)

            # add units
            df = pd.concat([df, pd.DataFrame([[''] * len(df.columns)], columns=df.columns)])

            # add empty row
            df = pd.concat([pd.DataFrame(units, index=['']), df])

            # add median and errors
            df = pd.concat([df, pd.DataFrame([medians, errs], columns=df.columns)])

            self.intensities_dict[labNr] = df

        writer = ExcelWriter(self.data_root_folder + '\\Intensities.xlsx', engine='xlsxwriter')
        ExcelFormatter.format(writer, self.intensities_dict)
        writer.save()

        os.chdir(old_path)

    def outliertest(self, X):
        mean = None
        std = None

        if self.mean_option == 'mean':
            mean = np.mean(X)
        elif self.mean_option == 'median':
            mean = np.median(X)

        if self.dev_option == 'std':
            std = np.std(X, ddof=1)
        elif self.dev_option == 'mad':
            std = median_abs_deviation(X)
        elif self.dev_option == 'iqr':
            std = iqr(X)

        inRangeIndices = np.where(np.logical_and(X >= mean - 2 * std, X <= mean + 2 * std))[0]
        X = X[inRangeIndices]

        errX = 2 * np.std(X, ddof=1) / np.sqrt(len(X))  # 2 sigma SE

        meanX = None
        if self.mean_option == 'mean':
            meanX = np.mean(X)
        elif self.mean_option == 'median':
            meanX = np.median(X)
        errRelX = errX / meanX  # 2 sigma relative error

        return X, errX, meanX, errRelX
