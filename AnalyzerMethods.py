from random import random
from numba import njit
import numpy as np

# This method is needed to make the age calculation method "thu_alter_kombi_numba" return a single type (float)
# This is required to compile with numba
def thu_alter_kombi(a230238, a234238, lambda230, lambda234):
    alter = thu_alter_kombi_numba(a230238, a234238, lambda230, lambda234)
    if alter == -1:
        return 'Out of range'
    else:
        return alter

@njit
def thu_alter_kombi_numba(a230238, a234238, lambda230, lambda234):
    xacc = 0.0001
    x1 = 0
    x2 = 1000000
    # i = 0

    fl = ((1 - np.exp(-lambda230 * x1)) + (a234238 - 1) * (
            lambda230 / (lambda230 - lambda234)) * (
                  1 - np.exp(-(lambda230 - lambda234) * x1))) - a230238
    fh = ((1 - np.exp(-lambda230 * x2)) + (a234238 - 1) * (
            lambda230 / (lambda230 - lambda234)) * (
                  1 - np.exp(-(lambda230 - lambda234) * x2))) - a230238

    if fl * fh >= 0:
        return -1
    else:

        if fl < 0:
            xl = x1
            xh = x2
        else:
            xh = x1
            xl = x2

        t = 0.5 * (x1 + x2)
        dxold = abs(x2 - x1)
        dx = dxold

        WERT = ((1 - np.exp(-lambda230 * t)) + (a234238 - 1) * (
                lambda230 / (lambda230 - lambda234)) * (
                        1 - np.exp(-(lambda230 - lambda234) * t))) - a230238
        ABL = lambda230 * np.exp(-lambda230 * t) - (a234238 - 1) * (
                lambda230 / (lambda230 - lambda234)) * (
                      -lambda230 + lambda234) * np.exp((-lambda230 + lambda234) * t)

        for i in range(100):

            if ((t - xh) * ABL - WERT) * ((t - xl) * ABL - WERT) >= 0:
                dxold = dx
                dx = 0.5 * (xh - xl)
                t = xl + dx

                if abs(dx) < xacc:
                    return np.round(t / 1000, 4)
            elif abs(2 * WERT) > abs(dxold * ABL):
                dxold = dx
                dx = 0.5 * (xh - xl)
                t = xl + dx

                if abs(dx) < xacc:
                    return np.round(t / 1000, 4)
            else:
                dxold = dx
                dx = WERT / ABL
                temp = t
                t = t - dx

                if temp == t:
                    return np.round(t / 1000, 4)

            if abs(dx) < xacc:
                return np.round(t / 1000, 4)

            WERT = ((1 - np.exp(-lambda230 * t)) + (a234238 - 1) * (
                    lambda230 / (lambda230 - lambda234)) * (
                            1 - np.exp(-(lambda230 - lambda234) * t))) - a230238
            ABL = lambda230 * np.exp(-lambda230 * t) - (a234238 - 1) * (
                    lambda230 / (lambda230 - lambda234)) * (
                          -lambda230 + lambda234) * np.exp((-lambda230 + lambda234) * t)

            if WERT < 0:
                xl = t
            else:
                xh = t
    return -1

# This method is needed to make the age calculation method "marincorr_age_numba" return a single type (float)
# This is required to compile with numba
def marincorr_age(a230238, a234238, a232238, a230232_init, lambda230, lambda234):
    alter = marincorr_age_numba(a230238, a234238, a232238, a230232_init, lambda230, lambda234)
    if alter == -1:
        return 'Out of range'
    else:
        return alter

# AV = a230238_coor
# AU = a234238_corr
@njit
def marincorr_age_numba(a230238, a234238, a232238, a230232_init, lambda230, lambda234):
    xacc = 0.0001
    x1 = 0
    x2 = 1000000

    fl = 1 + (a232238 * a230232_init - 1) * np.exp(-lambda230 * x1) + (a234238 - 1) * (
            lambda230 / (lambda230 - lambda234)) * (
                 1 - np.exp(-(lambda230 - lambda234) * x1)) - a230238
    fh = 1 + (a232238 * a230232_init - 1) * np.exp(-lambda230 * x2) + (a234238 - 1) * (
            lambda230 / (lambda230 - lambda234)) * (
                 1 - np.exp(-(lambda230 - lambda234) * x2)) - a230238

    if fl * fh >= 0:
        return -1
    else:
        if fl < 0:
            xl = x1
            xh = x2
        else:
            xh = x1
            xl = x2

        t = 0.5 * (x1 + x2)
        dxold = abs(x2 - x1)
        dx = dxold

        WERT = 1 + (a232238 * a230232_init - 1) * np.exp(-lambda230 * t) + (a234238 - 1) * (
                lambda230 / (lambda230 - lambda234)) * (
                       1 - np.exp(-(lambda230 - lambda234) * t)) - a230238
        ABL = -lambda230 * (a234238 - 1) * np.exp((-lambda230 + lambda234) * t) - lambda230 * (
                a232238 * a230232_init - 1) * np.exp(-lambda230 * t)

        for i in range(100):

            if ((t - xh) * ABL - WERT) * ((t - xl) * ABL - WERT) >= 0:
                dxold = dx
                dx = 0.5 * (xh - xl)
                t = xl + dx
            elif abs(2 * WERT) > abs(dxold * ABL):
                dxold = dx
                dx = 0.5 * (xh - xl)
                t = xl + dx
            else:
                dxold = dx
                dx = WERT / ABL
                t = t - dx

            if abs(dx) < xacc:
                return np.round(t / 1000, 4)

            WERT = 1 + (a232238 * a230232_init - 1) * np.exp(-lambda230 * t) + (a234238 - 1) * (
                    lambda230 / (lambda230 - lambda234)) * (
                           1 - np.exp(-(lambda230 - lambda234) * t)) - a230238
            ABL = -lambda230 * (a234238 - 1) * np.exp(
                (-lambda230 + lambda234) * t) - lambda230 * (a232238 * a230232_init - 1) * np.exp(
                -lambda230 * t)

            if WERT < 0:
                xl = t
            else:
                xh = t

    return -1

def montealter(a230238, a230238_err, a234238, a234238_err, lambda230, lambda234):
    error, fraction = montealter_numba(a230238, a230238_err, a234238, a234238_err, lambda230, lambda234)
    if error == -1:
        return '/', fraction
    else:
        return error, fraction

@njit
def montealter_numba(a230238, a230238_err, a234238, a234238_err, lambda230, lambda234):
    # number of iterations
    iter = 5000

    felda = np.empty(iter)
    feldb = np.empty(iter)
    res = np.empty(iter)

    summe = 0
    out_of_range_fraction = 0
    for i in range(iter):
        felda[i] = np.random.normal() * a230238_err + a230238
        feldb[i] = np.random.normal() * a234238_err + a234238

        result = thu_alter_kombi_numba(felda[i], feldb[i], lambda230, lambda234)
        if result == -1:
            out_of_range_fraction += 1
            res[i] = 0
        else:
            res[i] = result
            summe = summe + res[i]

    if iter == out_of_range_fraction:
        return -1, 1.0

    out_of_range_fraction /= iter

    mean = summe / iter

    summe = 0
    for i in range(iter):
        summe = summe + ((res[i] - mean) * (res[i] - mean))

    fehl = np.sqrt(summe / (iter - 1))

    return np.round(fehl, 4), out_of_range_fraction

def marincorr_age_error(a230238, a230238_err, a234238, a234238_err, a232238, a232238_err, a230232_init,
                        a230232_init_err, lambda230, lambda234):
    error, fraction = marincorr_age_error_numba(a230238, a230238_err, a234238, a234238_err, a232238, a232238_err, a230232_init,
                                                a230232_init_err, lambda230, lambda234)
    if error == -1:
        return '/', fraction
    else:
        return error, fraction

# AV = a230238
# AU = a234238
# AT232 = a232238
# ATinitial = a230232_init
@njit
def marincorr_age_error_numba(a230238, a230238_err, a234238, a234238_err, a232238, a232238_err, a230232_init,
                              a230232_init_err, lambda230, lambda234):
    iter = 5000
    summe = 0

    felda = np.empty(iter)
    feldb = np.empty(iter)
    feldc = np.empty(iter)
    feldd = np.empty(iter)
    res = np.empty(iter)

    out_of_range_fraction = 0
    for i in range(iter):
        felda[i] = np.random.normal() * a230238_err + a230238
        feldb[i] = np.random.normal() * a234238_err + a234238
        feldc[i] = np.random.normal() * a232238_err + a232238
        feldd[i] = np.random.normal() * a230232_init_err + a230232_init
        result = marincorr_age_numba(felda[i], feldb[i], feldc[i], feldd[i], lambda230, lambda234)

        if result == -1:
            out_of_range_fraction += 1
            res[i] = 0
        else:
            res[i] = result
            summe = summe + res[i]

    if iter == out_of_range_fraction:
        return -1, 1.0

    actual_iter = iter - out_of_range_fraction
    out_of_range_fraction /= iter

    mean = summe / actual_iter

    summe = 0

    for i in range(iter):
        summe = summe + ((res[i] - mean) * (res[i] - mean))

    fehl = np.sqrt(summe / (actual_iter - 1))

    return np.round(fehl, 4), out_of_range_fraction

# AU = a230232_init
# AW = age_corr
# AJ = d234U
# AS = a232238
# AT = a232238_err
# AV = a230232_init_err
# T = a234238_corr_err
# AO = a230238_corr_err)
def taylor_err(au, aw, aj, as_, at, av, t, ao, lambda230, lambda234):

    if aw == 'Out of range':
        return '/'
    else:
        return np.sqrt(((au * np.exp(-lambda230 * aw * 1000)) / (lambda230 * (
                np.exp(-lambda230 * aw * 1000) + (aj / 1000) * np.exp(
                -(lambda230 - lambda234) * aw * 1000)
                - as_ * au * np.exp(-lambda230 * aw * 1000)))) ** 2 * at ** 2 + (
                (as_ * np.exp(-lambda230 * aw * 1000)) / (
                lambda230 * (np.exp(-lambda230 * aw * 1000) +
                (aj / 1000) * np.exp(-(lambda230 - lambda234) * aw * 1000) - as_ * au * np.exp(
                -lambda230 * aw * 1000)))) ** 2 * av ** 2 + (
                (lambda230 / (lambda230 - lambda234)) * (np.exp(-(lambda230 - lambda234) * aw * 1000) - 1) / (
                lambda230 * (np.exp(-lambda230 * aw * 1000) + (aj / 1000) * np.exp(
                -(lambda230 - lambda234) * aw * 1000)
                - as_ * au * np.exp(-lambda230 * aw * 1000)))) ** 2 * t ** 2 + (1 / (
                lambda230 * (np.exp(-lambda230 * aw * 1000) + (aj / 1000) * np.exp(
                -(lambda230 - lambda234) * aw * 1000)
                - as_ * au * np.exp(-lambda230 * aw * 1000)))) ** 2 * ao ** 2) / 1000
