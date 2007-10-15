#!/usr/bin/env python

## This script was derived from
## 'examples/phase/anisotropy/input.py'

if __name__ == "__main__":
    from fipy import *
    from fipy.tools.parser import parse

    numberOfElements = parse('--numberOfElements', action = 'store',
                          type = 'int', default = 40)
    N = int(sqrt(numberOfElements))

    from benchmarker import Benchmarker
    bench = Benchmarker()

    bench.start()

    Length = N * 2.5 / 100.
    nx = N
    ny = N
    dx = Length / nx
    dy = Length / ny
    radius = Length / 4.
    seedCenter = (Length / 2., Length / 2.)
    initialTemperature = -0.4
    mesh = Grid2D(dx=dx, dy=dy, nx=nx, ny=ny)

    bench.stop('mesh')

    bench.start()

    timeStepDuration = 5e-5
    tau = 3e-4
    alpha = 0.015
    c = 0.02
    N = 4.
    kappa1 = 0.9
    kappa2 = 20.    
    tempDiffusionCoeff = 2.25
    theta = 0.
    phase = CellVariable(name='phase field', mesh=mesh, hasOld=1)
    x, y = mesh.getCellCenters()
    phase.setValue(1., where=(x - seedCenter[0])**2 + (y - seedCenter[1])**2 < radius**2)
    temperature = CellVariable(
        name='temperature',
        mesh=mesh,
        value=initialTemperature,
        hasOld=1
        )

    bench.stop('variables')

    bench.start()

    mVar = phase - 0.5 - kappa1 / pi * \
        arctan(kappa2 * temperature)

    phaseY = phase.getFaceGrad().dot((0, 1))
    phaseX = phase.getFaceGrad().dot((1, 0))
    psi = theta + arctan2(phaseY, phaseX)
    Phi = tan(N * psi / 2)
    PhiSq = Phi**2
    beta = (1. - PhiSq) / (1. + PhiSq)
    betaPsi = -N * 2 * Phi / (1 + PhiSq)
    A = alpha**2 * c * (1.+ c * beta) * betaPsi
    D = alpha**2 * (1.+ c * beta)**2
    dxi = phase.getFaceGrad()._take((1, 0), axis = 1) * (-1, 1)
    anisotropySource = (A * dxi).getDivergence()
    phaseEq = TransientTerm(tau) == ExplicitDiffusionTerm(D) + \
        ImplicitSourceTerm(mVar * ((mVar < 0) - phase)) + \
        ((mVar > 0.) * mVar * phase + anisotropySource)

    temperatureEq = TransientTerm() == \
                    ImplicitDiffusionTerm(tempDiffusionCoeff) + \
                    (phase - phase.getOld()) / timeStepDuration

    bench.stop('terms')

    phase.updateOld()
    temperature.updateOld()
    phaseEq.solve(phase, dt=timeStepDuration)
    temperatureEq.solve(temperature, dt=timeStepDuration)

    steps = 10

    bench.start()

    for i in range(steps):
        phase.updateOld()
        temperature.updateOld()
        phaseEq.solve(phase, dt=timeStepDuration)
        temperatureEq.solve(temperature, dt=timeStepDuration)

    bench.stop('solve')

    print bench.report(numberOfElements=numberOfElements, steps=steps)
