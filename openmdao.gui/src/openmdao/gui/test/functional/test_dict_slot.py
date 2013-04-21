"""
Tests of overall workspace functions.
"""

import pkg_resources
import time
import tempfile

from nose.tools import eq_ as eq
from nose.tools import with_setup

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from util import main, setup_server, teardown_server, generate, \
                 startup, closeout

from pageobjects.component import NameInstanceDialog
from pageobjects.util import ArgsPrompt, NotifierPage

from pageobjects.slot import SlotFigure


@with_setup(setup_server, teardown_server)
def test_generator():
    for _test, browser in generate(__name__):
        yield _test, browser



def _test_dict_slot(browser):
    project_dict, workspace_page = startup(browser)

    #### load in some files needed for the tests ####
    # write out a file to be loaded in with some vartrees
    vartree_temp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    print >> vartree_temp, """
from openmdao.main.api import VariableTree, Component
from openmdao.main.datatypes.api import Float, Slot
class InVtree(VariableTree): 
    a = Float(iotype='in')
    b = Float(iotype='in')


class OutVtree(VariableTree): 
    x = Float(iotype='out', desc='horizontal distance', units='ft')
    y = Float(iotype='out', desc='vertical distance', units='ft')    


class InTreeOnly(Component): 

    ins = Slot(InVtree, iotype='in')

    x = Float(iotype='out')
    y = Float(iotype='out') 

    def __init__(self): 
        super(InTreeOnly, self).__init__()
        self.ins = InVtree()

    def execute(self): 
        self.x = 2*self.ins.a
        self.y = 2*self.ins.a+self.ins.b


class InandOutTree(Component): 

    ins = Slot(InVtree, iotype='in')

    outs = Slot(OutVtree, iotype='out')

    def __init__(self): 
        super(InandOutTree, self).__init__()
        self.ins = InVtree()
        self.outs = OutVtree()

    def execute(self): 

        self.outs.x = 2*self.ins.a
        self.outs.y = 2*self.ins.a+self.ins.b
"""
    vartree_temp.close()
    workspace_page.add_file(vartree_temp.name)

    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')
    workspace_page.add_file(file1_path)
    file2_path = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                 'transmission.py')
    workspace_page.add_file(file2_path)

    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.components.metamodel.MetaModel', 'mm')
    mm_figure = workspace_page.get_dataflow_figure('mm', 'top')
    mm_editor = mm_figure.editor_page()
    mm_editor.show_slots()
    mm_editor.move(-150, 0)

    model_slot = SlotFigure(workspace_page, 'top.mm.model')

    # Should not be any surrogates slots without a model in the slot
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq( 0, len( surrogates),
        "There should not be any surrogates in the surrogates dict but %d surrogate(s) are being displayed" % len( surrogates ) )

    # Fill the model slot
    model_slot.fill_from_library('Paraboloid')

    # Should be one surrogates slot in the dict
    time.sleep(1.0)  # give it a bit to update the figure
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq( 1, len( surrogates),
        "There should be one surrogate in the surrogate slot but %d surrogate is being displayed" % len( surrogates ) )

    # remove the model
    model_elem = browser.find_element(By.ID, 'SlotFigure-top-mm-model')
    menu_item_remove = model_elem.find_element_by_css_selector('ul li')
    chain = ActionChains(browser)
    chain.move_to_element_with_offset(model_elem, 25, 25)
    chain.context_click(model_elem).perform()
    menu_item_remove.click()

    # There should not be any surrogates slots
    time.sleep(1.0)  # give it a bit to update the figure
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq( 0, len( surrogates),
        "There should not be any surrogates in the surrogates dict but %d surrogate(s) are being displayed" % len( surrogates ) )

    model_slot.fill_from_library('Transmission')

    # There should two surrogates slots
    time.sleep(1.0)  # give it a bit to update the figure
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq( 2, len( surrogates),
        "There should be two surrogates in the surrogates dict but %d surrogate(s) are being displayed" % len( surrogates ) )

    # They should all be empty: RPM and torque_ratio
    for surrogate in surrogates :
        eq(False, ("filled" in surrogate.get_attribute('class')), "Surrogate should not be filled")

    # Fill the torque_ratio surrogate slot with FloatKrigingSurrogate
    # The ID of that slot div is SlotFigure-top-mm-surrogates-torque_ratio
    surrogates_torque_ratio_slot = SlotFigure(workspace_page, 'top.mm.surrogates.torque_ratio')
    surrogates_torque_ratio_slot.fill_from_library('KrigingSurrogate')

    # One should be filled now
    time.sleep(1.5)  # give it a bit to update the figure
    num_surrogates_filled = 0
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    for surrogate in surrogates :
        if "filled" in surrogate.get_attribute('class') :
            num_surrogates_filled += 1
    eq(1, num_surrogates_filled,
       "Exactly one surrogate slot should be filled but %d are filled" % num_surrogates_filled)

    # Fill the RPM surrogate slot with FloatKrigingSurrogate
    # The ID of that slot div is SlotFigure-top-mm-surrogates-RPM
    surrogates_torque_ratio_slot = SlotFigure(workspace_page, 'top.mm.surrogates.RPM')
    surrogates_torque_ratio_slot.fill_from_library('FloatKrigingSurrogate')

    # Two should be filled now
    time.sleep(1.5)  # give it a bit to update the figure
    num_surrogates_filled = 0
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    for surrogate in surrogates :
        if "filled" in surrogate.get_attribute('class') :
            num_surrogates_filled += 1
    eq(2, num_surrogates_filled,
       "Exactly two surrogate slot should be filled but %d are filled" % num_surrogates_filled)

    # Need to test with vartrees
    #model_slot.fill_from_library('SimpleComp')

    time.sleep(5.5)  # give it a bit to update the figure


#     # Open code editor.
#     workspace_window = browser.current_window_handle
#     editor_page = workspace_page.open_editor()

#     # Create a file (code editor automatically indents).
#     editor_page.new_file('component_with_vartree.py', """
# from openmdao.main.api import Component, Assembly, VariableTree, set_as_top, Case
# from openmdao.main.interfaces import implements, ICaseRecorder

# from openmdao.main.uncertain_distributions import NormalDistribution, UncertainDistribution

# from openmdao.lib.datatypes.api import Float, Slot, Array


# class InVtree(VariableTree): 
# a = Float(iotype="in")
# b = Float(iotype="in")


# class OutVtree(VariableTree): 
# x = Float(iotype="out", desc="horizontal distance", units="ft")
# y = Float(iotype="out", desc="vertical distance", units="ft")    

# class InandOutTree(Component): 

# ins = Slot(InVtree, iotype="in")

# outs = Slot(OutVtree, iotype="out")
# """)
#     # Back to workspace.
#     browser.close()
#     browser.switch_to_window(workspace_window)



    # test vartree with metamodel ##############################
    model_slot.fill_from_library('InandOutTree')


    # There should two surrogates slots
    time.sleep(1.0)  # give it a bit to update the figure
    surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq( 2, len( surrogates),
        "There should be two surrogates in the surrogates dict but %d surrogate(s) are being displayed" % len( surrogates ) )

    # They should all be empty: RPM and torque_ratio
    for surrogate in surrogates :
        eq(False, ("filled" in surrogate.get_attribute('class')), "Surrogate should not be filled")
    

    # Clean up.
    closeout(project_dict, workspace_page)






if __name__ == '__main__':
    main()
