# Convex Optimization of Autocorrelation with Constrained Support (COACS)
# Author: Noa Lerch
# Based on code by Carl Nettelblad at https://github.com/cnettel/jackdaw
# As well as the TFOCS library for MATLAB: http://cvxr.com/tfocs/
# Bachelor's degree project in Computer Science at Uppsala University
# 2023

import numpy as np
import coacsutils as cu
import sys

sys.path.append('ConicSolver')
import ConicSolver as cs


class Healer:
    def __init__(self, pattern, support, bkg, init_guess, alg, num_rounds, qbarrier,
                 nzpenalty, iters, tolerance, nowindow=None):
        """The main COACS function
        pattern : ??
            pattern to phase
        support : ??
            support mask (in autocorrelation space
        bkg : ??
            background signal, support for non-zero values here basically stale
        init_guess : ??
            start guess for the pattern
        alg : ??
            solving algorithm to use
        num_rounds : int
            number of outermost iterations
        qbarrier : int?
            qbarrier (2 * l) in each round
        nzpenalty : ??
            penalty constant outside of the support
        iters : int
            number of TFOCS (solver) iterations within the round
        tolerance : ??
            the tolerance used to determine end of iteration in TFOCS
        nowindow: ??
        """

        # TODO: if nargin < 11

        if nowindow is None:
            nowindow = []

        if len(nowindow) == 0:
            nowindow = False

        iter_factor = 1.1

        # handle scalars
        # 1x69 in matlab, is this correct?
        # resulting from num_rounds
        # TODO: check this, possible error in matlab
        # nzpenalty = np.ones(num_rounds) * nzpenalty  # redundant if nzpenalty is 1D
        qbarrier = np.ones(num_rounds) * qbarrier

        dims, side2, fullsize, pshape, cshape = cu.get_dims(pattern)

        original_pattern = pattern.copy()
        # TODO: check dimensions of pattern
        pattern = pattern.reshape(fullsize, 1)

        solver = cs.ConicSolver
        solver.alg = alg
        solver.restart = 5e5
        solver.count_ops = True
        solver.print_stop_criterion = True
        solver.print_every = 2500
        # no regress restart option
        solver.restart = -10000000  # ?

        solver.autoRestart = 'fun' # ? double check this

        mask = np.hstack((np.reshape(support, pshape), np.zeros(np.reshape(support, pshape).shape)))
        # TODO: check dimensions of mask
        mask = np.reshape(mask, (fullsize * 2, 1))

        # purely ie zero mask in imaginary space
        our_linp_flat = jackdaw_linop(original_pattern, 1)
        # no windowing used within linop for now
        our_linp = our_linp_flat

        global factor

        # empty guess?
        if not init_guess:
            init_guess = pattern.flatten()
            # replace neg values with 0
            init_guess[init_guess < 0] = 0

        x = np.reshape(init_guess, (1, fullsize))
        # need to copy to not overwrite later
        xprev = x.copy()
        y = x.copy()
        jval = 0

        filter = np.ones((fullsize, 1))
        rfilter = 1.0 / filter

        # i is outer round
        for i in range(num_rounds):
            # base_penalty = None
            if nowindow:
                factor = np.ones((65536, 1))
                base_penalty = 1 - mask
            else:
                factor, base_penalty = cu.create_windows(original_pattern, mask, qbarrier[i], filter)

            y = y * factor
            x = x * factor

            penalty = base_penalty * nzpenalty[i]

            # acceleration scheme baseed on assumption of linear steps
            # in response to decreasing qbarrier
            if i > 0 and qbarrier[i] != qbarrier[i - 1]:
                xprev = xprev * factor
                if jval > 0:
                    diffx = x + (x - xprev) * (qbarrier[i] / qbarrier[i - 1])
                    smoothop = cu.diffpoisson(factor, pattern.flatten(), diffx.flatten(), bkg.flatten(), diffx, filter, qbarrier[i])





# TODO: test this
def jackdaw_linop(pattern, filter):
    dims, side2, fullsize, pshape, cshape = cu.get_dims(pattern)

    if dims == 3:
        r = np.fftshift(np.pi / 2 + (np.arange(0.25, side2 - 0.75) * np.pi / side2))
        Xs, Ys, Zs = np.meshgrid(r, r, r)
        shifter = np.exp(1j * (Xs + Ys + Zs))

        r = np.linspace(0, -np.pi + np.pi / side2, side2)
        Xs, Ys, Zs = np.meshgrid(r, r, r)
        unshifter = np.exp(1j * (Xs + Ys + Zs))
    else:
        shifter = 1
        unshifter = 1

    linop = lambda x, mode: linop_helper(x, mode, dims, side2, fullsize, pshape, cshape, filter, unshifter, shifter)
    return linop


def linop_helper(x, mode, dims, side, fullsize, pshape, cshape, filter, unshifter, shifter):
    y = None
    if mode == 0:
        y = np.array([fullsize, 2 * fullsize])
    elif mode == 1:
        x = x.reshape(cshape)
        if dims == 3:
            x = np.fft.fftshift(x[0:side, 0:side, 0:side] + 1j * x[0:side, side:side * 2, 0:side])
        else:
            x = np.fft.fftshift(x[0:side, 0:side] + 1j * x[0:side, side:side * 2])

        x2 = x.copy() * np.conj(shifter)
        x = np.fft.fftn(x2) * np.conj(shifter)

        y = (side ** (-dims / 2)) * np.real(x.flatten()) * filter.flatten()
    elif mode == 2:
        x2 = np.zeros(pshape, dtype=complex)
        x2[:] = np.real(x) * filter
        x2 = x2 * shifter
        x2 = np.fft.ifftn(x2)
        x2 = x2 * shifter
        x2 = np.fft.ifftshift(x2)
        y = np.concatenate([np.real(side ** (dims / 2) * x2), np.imag(side ** (dims / 2) * x2)], axis=0)

    assert y is not None
    return y




