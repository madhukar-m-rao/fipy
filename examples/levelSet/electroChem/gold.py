#!/usr/bin/env python

## 
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "gold.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #    mail: NIST
 #     www: http://ctcms.nist.gov
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  PFM is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 # ###################################################################
 ##

r"""
This input file

.. raw:: latex

    \label{gold} is a demonstration of the use of \FiPy{} for
    modeling gold superfill. The material properties and experimental
    parameters used are roughly those that have been previously
    published~\cite{NIST:damascene:2005}.

To run this example from the base fipy directory type::
    
    $ examples/levelSet/electroChem/gold.py

at the command line. The results of the simulation will be displayed
and the word `finished` in the terminal at the end of the
simulation. The simulation will only run for 10 time steps. In order
to alter the number of timesteps, the python function that
encapsulates the system of equations must first be imported (at the
python command line),

.. raw:: latex

   \IndexFunction{runGold}

..

    >>> from examples.levelSet.electroChem.gold import runGold

and then the function can be run with a different number of time steps
with the `numberOfSteps` argument as follows,

    >>> runGold(numberOfSteps=10, displayViewers=False)
    1
    
Change the `displayViewers` argument to `True` if you wish to see the
results displayed on the screen. This example has a more realistic
default boundary layer depth and thus requires `gmsh` to construct a
more complex mesh.

.. raw:: latex

    \IndexSoftware{gmsh}

    There are a few differences between the gold superfill model presented
    in this example and Example~\ref{inputSimpleTrench}. Most default
    values have changed to account for a different metal ion (gold)
    and catalyst (lead). In this system the catalyst is not present in
    the electrolyte but instead has a non-zero initial coverage. Thus
    quantities associated with bulk catalyst and catalyst accumulation
    are not defined. The current density is given by, $$ i =
    \frac{c_m}{c_m^{\infty}} \left( b_0 + b_1 \theta \right). $$ The
    more common representation of the current density includes an
    exponential part. Here it is buried in $b_0$ and $b_1$. The
    governing equation for catalyst evolution includes a term for
    catalyst consumption on the interface and is given by $$
    \dot{\theta} = J v \theta - k_c v \theta $$ where $k_c$ is the
    consumption coefficient

(`consumptionRateConstant`). The trench geometry is also given a
slight taper, given by `taperAngle`.

If the MayaVi plotting software is

.. raw:: latex

    installed (see Chapter~\ref{chap:Installation}) then a plot should
    appear that is updated every 10 time steps and will eventually

resemble the image below.

.. image:: examples/levelSet/electroChem/inputGold.pdf
   :scale: 60
   :align: center
   :alt: resulting image

"""
__docformat__ = 'restructuredtext'

from fipy import *

def runGold(faradaysConstant=9.6e4,
            consumptionRateConstant=2.6e+6,
            molarVolume=10.21e-6,
            charge=1.0,
            metalDiffusion=1.7e-9,
            metalConcentration=20.0,
            catalystCoverage=0.15,
            currentDensity0=3e-2 * 16,
            currentDensity1=6.5e-1 * 16,
            cellSize=0.1e-7,
            trenchDepth=0.2e-6,
            aspectRatio=1.47,
            trenchSpacing=0.5e-6,
            boundaryLayerDepth=90.0e-6,
            numberOfSteps=10,
            taperAngle=6.0,
            displayViewers=True):
    
    cflNumber = 0.2
    numberOfCellsInNarrowBand = 20
    cellsBelowTrench = 10
    
    mesh = TrenchMesh(cellSize = cellSize,
                      trenchSpacing = trenchSpacing,
                      trenchDepth = trenchDepth,
                      boundaryLayerDepth = boundaryLayerDepth,
                      aspectRatio = aspectRatio,
                      angle = pi * taperAngle / 180.,
                      bowWidth = 0.,
                      overBumpRadius = 0.,
                      overBumpWidth = 0.)

    narrowBandWidth = numberOfCellsInNarrowBand * cellSize

    distanceVar = DistanceVariable(
       name = 'distance variable',
       mesh = mesh,
       value = -1,
       narrowBandWidth = narrowBandWidth)

    distanceVar.setValue(1, where=mesh.getElectrolyteMask())
    distanceVar.calcDistanceFunction(narrowBandWidth = 1e10)

    catalystVar = SurfactantVariable(
        name = "catalyst variable",
        value = catalystCoverage,
        distanceVar = distanceVar)

    metalVar = CellVariable(
        name = 'metal variable',
        mesh = mesh,
        value = metalConcentration)

    exchangeCurrentDensity = currentDensity0 + currentDensity1 * catalystVar.getInterfaceVar()
    
    currentDensity = metalVar / metalConcentration * exchangeCurrentDensity

    depositionRateVariable = currentDensity * molarVolume / charge / faradaysConstant

    extensionVelocityVariable = CellVariable(
        name = 'extension velocity',
        mesh = mesh,
        value = depositionRateVariable)   

    catalystSurfactantEquation = AdsorbingSurfactantEquation(
        catalystVar,
        distanceVar = distanceVar,
        bulkVar = 0,
        rateConstant = 0,
        consumptionCoeff = consumptionRateConstant * extensionVelocityVariable)

    advectionEquation = buildHigherOrderAdvectionEquation(
        advectionCoeff = extensionVelocityVariable)

    metalEquation = buildMetalIonDiffusionEquation(
        ionVar = metalVar,
        distanceVar = distanceVar,
        depositionRate = depositionRateVariable,
        diffusionCoeff = metalDiffusion,
        metalIonMolarVolume = molarVolume)

    metalEquationBCs = FixedValue(mesh.getTopFaces(), metalConcentration)

    if displayViewers:

        try:
            
            viewer = MayaviSurfactantViewer(distanceVar, catalystVar.getInterfaceVar(), zoomFactor = 1e6, limits = { 'datamax' : 1.0, 'datamin' : 0.0 }, smooth = 1, title = 'catalyst coverage', animate=True)
            
        except:
            
            class PlotVariable(CellVariable):
                def __init__(self, var = None, name = ''):
                    CellVariable.__init__(self, mesh = mesh.getFineMesh(), name = name)
                    self.var = self._requires(var)

                def _calcValue(self):
                    return array(self.var[:self.mesh.getNumberOfCells()])

            viewer = MultiViewer(viewers=(
                Viewer(PlotVariable(var = distanceVar), limits = {'datamax' : 1e-9, 'datamin' : -1e-9}),
                Viewer(PlotVariable(var = catalystVar.getInterfaceVar()))))
    else:
        viewer = None

    levelSetUpdateFrequency = int(0.7 * narrowBandWidth / cellSize / cflNumber / 2)
    step = 0
    
    while step < numberOfSteps:

        if step % 10 == 0 and viewer is not None:
            viewer.plot()

        if step % levelSetUpdateFrequency == 0:
            
            distanceVar.calcDistanceFunction(deleteIslands = True)
            
        extensionVelocityVariable.setValue(array(depositionRateVariable))
        argmx = argmax(extensionVelocityVariable)
        dt = cflNumber * cellSize / extensionVelocityVariable[argmx]
        distanceVar.extendVariable(extensionVelocityVariable, deleteIslands = True)
        
        distanceVar.updateOld()
        catalystVar.updateOld()
        metalVar.updateOld()

        advectionEquation.solve(distanceVar, dt = dt)
        catalystSurfactantEquation.solve(catalystVar, dt = dt)

        metalEquation.solve(metalVar, boundaryConditions = metalEquationBCs, dt = dt, solver=LinearPCGSolver())
                    
        step += 1

    try:
        import os
        data = dump.read(os.path.splitext(__file__)[0] + '.gz')
        n = mesh.getFineMesh().getNumberOfCells()
        print allclose(catalystVar[:n], data[:n], atol=1.0)
    except:
        return 0
    
if __name__ == '__main__':
    runGold(numberOfSteps = 300, cellSize = 0.05e-7)
    raw_input("finished")
    