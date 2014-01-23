"""
A component with a large number of inputs is finite differenced.
"""

import numpy as np

from openmdao.lib.optproblems.scalable import Discipline
from openmdao.main.api import Assembly, Component, set_as_top

N = 200
np.random.seed(12345)

class Model(Assembly):

    def configure(self):

        self.add('comp', Discipline(prob_size=N))
        self.comp.C_y = np.random.random((N, N))

if __name__ == "__main__":

    from time import time

    top = set_as_top(Model())
    top.run()

    inputs = ['comp.y_in']
    outputs = ['comp.y_out']
    inputs = ['comp.y_in[%d, 0]'%n for n in range(N)]
    outputs = ['comp.y_out[%d, 0]'%n for n in range(N)]


    import sys
    if len(sys.argv) > 1 and '-prof' in sys.argv:
        import cProfile
        import pstats
        sys.argv.remove('-prof') #unittest doesn't like -prof
        cProfile.run('J = top.driver.workflow.calc_gradient(inputs=inputs, outputs=outputs, mode = "forward")', 'profout')
        p = pstats.Stats('profout')
        p.strip_dirs()
        p.sort_stats('cumulative', 'time')
        p.print_stats()
        print '\n\n---------------------\n\n'
        p.print_callers()
        print '\n\n---------------------\n\n'
        p.print_callees()
    else:
        t0 = time()
        J = top.driver.workflow.calc_gradient(inputs=inputs,
                                              outputs=outputs,
                                              mode = 'forward')
        print 'Time elapsed', time() - t0


    # python -m cProfile -s time fd_scalable.py >z