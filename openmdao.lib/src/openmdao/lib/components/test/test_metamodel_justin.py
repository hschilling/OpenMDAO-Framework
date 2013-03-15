import unittest 

from openmdao.main.api import Component, Assembly, VariableTree, set_as_top

#from openmdao.lib.components.api import MetaModel
#from openmdao.lib.components.metamodel_works_for_inputs import MetaModel
#from openmdao.lib.components.metamodel_getting_outputs_working import MetaModel
#from openmdao.lib.components.metamodel_getting_outputs_working_with_dict import MetaModel
from openmdao.lib.components.metamodel_check_at_runtime import MetaModel
from openmdao.lib.datatypes.api import Float, Slot, Array
from openmdao.lib.surrogatemodels.api import FloatKrigingSurrogate, KrigingSurrogate

#from openmdao.main.datatypes.uncertaindist import UncertainDistVar
from openmdao.main.uncertain_distributions import UncertainDistribution



class InVtree(VariableTree): 
    a = Float(iotype="in")
    b = Float(iotype="in")


class OutVtree(VariableTree): 
    x = Float(iotype="out", desc="horizontal distance", units="ft")
    y = Float(iotype="out", desc="vertical distance", units="ft")    


class InTreeOnly(Component): 

    ins = Slot(InVtree, iotype="in")

    x = Float(iotype="out")
    y = Float(iotype="out") 

    def __init__(self): 
        super(InTreeOnly, self).__init__()
        self.ins = InVtree()

    def execute(self): 
        self.x = 2*self.ins.a
        self.y = 2*self.ins.a+self.ins.b


class InandOutTree(Component): 

    ins = Slot(InVtree, iotype="in")

    outs = Slot(OutVtree, iotype="out")

    def __init__(self): 
        super(InandOutTree, self).__init__()
        self.ins = InVtree()
        self.outs = OutVtree()

    def execute(self): 

        self.outs.x = 2*self.ins.a
        self.outs.y = 2*self.ins.a+self.ins.b


class InArrayOnly(Component):        

    ins = Array([0, 0], dtype=Float, size=(2,), iotype="in")

    x = Float(iotype="out")
    y = Float(iotype="out") 

    def execute(self): 
        self.x = 2*self.ins[0]
        self.y = 2*self.ins[0]+self.ins[1]


class InandOutArray(Component):        

    ins = Array([0, 0], dtype=Float, size=(2,), iotype="in")
    outs = Array([0, 0], dtype=Float, size=(2,), iotype="out")

    def execute(self): 
        self.outs[0] = 2*self.ins[0]
        self.outs[1] = 2*self.ins[0]+self.ins[1]        


class MMTest(Assembly):    

    def configure(self):
        import echo

        print "create MetaModel"

        mm = MetaModel()
        #echo.echo_class( mm )
        self.add('mm', mm )
        print "set default surrogate"
        self.mm.default_surrogate = FloatKrigingSurrogate()

        self.driver.workflow.add('mm')  
     


class TestMetaModelWithVtree(unittest.TestCase):

    def setUp(self): 
        self.k_x = FloatKrigingSurrogate()
        self.k_y = FloatKrigingSurrogate()

        self.k_x.train([(1, 2), (2, 3)], [2, 4])
        self.k_y.train([(1, 2), (2, 3)], [4, 7])

        self.a = set_as_top(MMTest())

    def tearDown(self): 
        self.a = None

    def _run_sweep(self, asmb, a_name, b_name, x_name, y_name):
        in_arrays = (type(a_name)==tuple)

        def set_ab(a, b):
            if in_arrays:
                asmb.mm.set(a_name[0], a, (a_name[1],))
                asmb.mm.set(b_name[0], b, (b_name[1],))
            else: 
                asmb.mm.set(a_name, a)
                asmb.mm.set(b_name, b)  

        asmb.mm.train_next = True
        print "first training set"
        set_ab(1, 2)
        asmb.run()  
        x = asmb.mm.get(x_name)
        y = asmb.mm.get(y_name)
        self.assertEqual(x, 2)
        if ( isinstance(y,UncertainDistribution) ):
            self.assertEqual(y.getvalue(), 4)
        else:
            self.assertEqual(y, 4)

        asmb.mm.train_next = True
        print "second training set"
        set_ab(2, 3)
        asmb.run()
        x = asmb.mm.get(x_name)
        y = asmb.mm.get(y_name)
        self.assertEqual(x, 4)
        if ( isinstance(y,UncertainDistribution) ):
            self.assertEqual(y.getvalue(), 7)     
        else:
            self.assertEqual(y, 7)     

        #predictions
        set_ab(1, 2)
        asmb.run()

        print "+++++++++++++++ predictions ++++++++++++"

        x = asmb.mm.get(x_name)
        y = asmb.mm.get(y_name)
        self.assertEqual(x, self.k_x.predict((1, 2)))
        if ( isinstance(y,UncertainDistribution) ):
            self.assertEqual(y.getvalue(), self.k_y.predict((1, 2)))
        else:
            self.assertEqual(y, self.k_y.predict((1, 2)))

        set_ab(1.5, 2.5)
        asmb.run()

        x = asmb.mm.get(x_name)
        y = asmb.mm.get(y_name)
        self.assertEqual(x, self.k_x.predict((1.5, 2.5)))
        if ( isinstance(y,UncertainDistribution) ):
            self.assertEqual(y.getvalue(), self.k_y.predict((1.5, 2.5)))
        else:
            self.assertEqual(y, self.k_y.predict((1.5, 2.5)))

        set_ab(2, 3)
        asmb.run()

        x = asmb.mm.get(x_name)
        y = asmb.mm.get(y_name)
        self.assertEqual(x, self.k_x.predict((2, 3)))
        if ( isinstance(y,UncertainDistribution) ):
            self.assertEqual(y.getvalue(), self.k_y.predict((2, 3)))  
        else:
            self.assertEqual(y, self.k_y.predict((2, 3)))  

    def test_in_tree_only(self):
        self.a.mm.model = InTreeOnly()

        self._run_sweep(self.a, 'ins.a', 'ins.b', 'x', 'y')

    def test_in_and_out_tree(self):
        #a = MMTest()

        print "set model"
        self.a.mm.model = InandOutTree()

        self._run_sweep(self.a, 'ins.a', 'ins.b', 'outs.x', 'outs.y')


    def test_in_tree_only_multiple_surrogates(self):
        self.a.mm.model = InTreeOnly()

        #import pdb; pdb.set_trace()
        #### TODO remove 
        #self.a.mm.surrogates ={}

        print "##############setting surrogate for x"
        self.a.mm.surrogates['x']= FloatKrigingSurrogate()
        self.a.mm.surrogates['y'] = KrigingSurrogate()
        # self.a.mm.sur_x = FloatKrigingSurrogate()
        # self.a.mm.sur_y = KrigingSurrogate()
        self._run_sweep(self.a, 'ins.a', 'ins.b', 'x', 'y')

    def test_in_and_out_tree_multiple_surrogates(self):
        #a = MMTest()
        self.a.mm.model = InandOutTree()

        #import pdb; pdb.set_trace()
        self.a.mm.sur_outs_x = FloatKrigingSurrogate()
        self.a.mm.sur_outs_y = FloatKrigingSurrogate()

        self._run_sweep(self.a, 'ins.a', 'ins.b', 'outs.x', 'outs.y')

    def test_includes_with_vartrees(self):
        self.a.mm.default_surrogate = KrigingSurrogate()
        self.a.mm.includes = ['ins.a', 'outs.y']
        self.a.mm.model = InandOutTree()
        self.assertEqual(self.a.mm.surrogate_input_names(), ['ins.a'])
        self.assertEqual(self.a.mm.surrogate_output_names(), ['outs.y'])
        
        # now try changing the includes
        self.a.mm.includes = ['ins.b', 'outs.x']
        self.assertEqual(self.a.mm.surrogate_input_names(), ['ins.b'])
        self.assertEqual(self.a.mm.surrogate_output_names(), ['outs.x'])

    def test_excludes_with_vartrees(self):
        self.a.mm.default_surrogate = KrigingSurrogate()
        self.a.mm.excludes = ['ins.b', 'outs.y']
        self.a.mm.model = InandOutTree()
        self.assertEqual(self.a.mm.surrogate_input_names(), ['ins.a'])
        self.assertEqual(self.a.mm.surrogate_output_names(), ['outs.x'])
        
        # now try changing the excludes
        self.a.mm.excludes = ['ins.a', 'outs.x']
        self.assertEqual(self.a.mm.surrogate_input_names(), ['ins.b'])
        self.assertEqual(self.a.mm.surrogate_output_names(), ['outs.y'])

    def test_include_exclude_with_vartrees(self):
        self.a.mm.model = InandOutTree()
        self.a.mm.default_surrogate = KrigingSurrogate()
        self.a.mm.includes = ['ins.a','outs.y']
        self.a.mm.excludes = ['ins.b','outs.x']

        #self.a.mm.run()
        #self._run_sweep(self.a, 'ins.a', 'ins.b', 'outs.x', 'outs.y')


        try:
            self.a.mm.run()
            #self._run_sweep(self.a, 'ins.a', 'ins.b', 'outs.x', 'outs.y')
        except Exception as err:
            self.assertEqual(str(err), 
                             'mm: includes and excludes are mutually exclusive')
        else:
            self.fail('Expected Exception')

    # def test_in_array_only(self): 
        
    #     self.a.mm.model = InArrayOnly()

    #     self._run_sweep(self.a, ('ins', 0), ('ins', 1), 'x', 'y')

    # def test_in_and_out_array(self): 
    #     a = MMTest()
    #     a.mm.model = InandOutArray()

    #     self._run_sweep(a, ('ins', 0), ('ins', 1), 'outs[0]', 'outs[1]')    






if __name__ == "__main__":

    unittest.main()

