
import sys
import time

import numpy as np 

from openmdao.main.api import Assembly, Component, Driver, set_as_top
from openmdao.main.datatypes.api import Float, Array
from openmdao.main.hasobjective import HasObjectives
from openmdao.main.hasconstraints import HasConstraints
from openmdao.main.hasparameters import HasParameters
from openmdao.util.decorators import add_delegate
from openmdao.util.testutil import assert_rel_error
import openmdao.main.pseudocomp as pcompmod  # to keep pseudocomp names consistent in tests

@add_delegate(HasObjectives, HasParameters, HasConstraints)
class NTimes(Driver):
    def __init__(self, n=1):
        super(NTimes, self).__init__()
        self.n = n 
        self._count = 0

    def run(self, force=False, ffd_order=0, case_id=''):
        self._count = 0
        super(NTimes, self).run(force=force, ffd_order=ffd_order,
                                case_id=case_id)
        
    def run_iteration(self):
        self._count += 1
        print "%s: iteration = %d" % (self.get_pathname(), self._count)
        super(NTimes, self).run_iteration()

    def continue_iteration(self):
        return self._count < self.n


class ABCDArrayComp(Component):
    a = Array(np.ones(12, float), iotype='in')
    b = Array(np.ones(12, float), iotype='in')
    c = Array(np.ones(12, float), iotype='out')
    d = Array(np.ones(12, float), iotype='out')
    delay = Float(0.01, iotype='in')
    
    def execute(self):
        time.sleep(self.delay)
        self.c = self.a + self.b
        self.d = self.a - self.b
        
def _get_model1():
    top = set_as_top(Assembly())
    top.add('driver', NTimes(3))
    for i in range(1,12):
        name = 'C%d' % i
        top.add(name, ABCDArrayComp())
        top.driver.workflow.add(name)
        getattr(top, name).mpi.requested_cpus = 1

    conns = [
        ('C1.c','C6.a'),
        ('C2.c','C5.a'),
        ('C3.c','C11.a'),
        ('C3.d','C8.a'),
        ('C5.c','C6.b'),
        ('C5.d','C8.b'),
        ('C8.c','C11.b'),
        ('C8.d','C10.a'),
    ]

    for u,v in conns:
        top.connect(u, v)

    top.driver.add_parameter('C3.a[1]', high=100.0, low=0.0)
    top.driver.add_constraint('C8.d[0]>C11.d[0]') 
    
    return top

if __name__ == '__main__':
    from mpi4py import MPI
    from openmdao.main.mpiwrap import MPI_run

    top = _get_model1()

    MPI_run(top)

        
