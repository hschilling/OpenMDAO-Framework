"""
Tests of code editor functions.
"""

import time
import pkg_resources

import re, glob, datetime, os

from unittest import TestCase

from nose import SkipTest
from nose.tools import eq_ as eq
from nose.tools import with_setup
from nose.tools import assert_not_equal as neq

from util import main, setup_server, teardown_server, generate, \
                 startup, closeout, broken_chrome
from util import main, setup_server, teardown_server, generate, \
                 begin, random_project, edit_project, import_project, \
                 get_browser_download_location_path, broken_chrome, begin, random_project


from pageobjects.util import NotifierPage

from selenium.webdriver.common.action_chains import ActionChains
from pageobjects.component import ComponentPage
from pageobjects.component import NameInstanceDialog
from openmdao.gui.test.functional.pageobjects.slot import find_slot_figure
from openmdao.gui.test.functional.pageobjects.geometry import GeometryPage
from pageobjects.workspace import WorkspacePage
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

from pageobjects.basepageobject import TMO
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, \
                                       WebDriverException

from openmdao.main.releaseinfo import __version__

@with_setup(setup_server, teardown_server)
def test_generator():
    for _test, browser in generate(__name__):
        yield _test, browser


def _test_crlf(browser):
    # Test ability to handle a file with Windows-style CR/LF line terminations
    project_dict, workspace_page = startup(browser)

    # add a Windows notepad generated python file
    filename = 'notepad.py'
    filepath = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/notepad.py')
    workspace_page.add_file(filepath)

    # open file in code editor
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.edit_file(filename)
    eq(str(editor_page.get_tab_label()), '/' + filename)

    # add a comment and save
    comment = '# a comment'
    editor_page.append_text_to_file(comment)
    editor_page.save_document()

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # re-open file and verify comment was successfully added
    workspace_window = browser.current_window_handle
    if broken_chrome():
        raise SkipTest('Test broken for chrome/selenium combination')
    editor_page = workspace_page.edit_file(filename)
    assert editor_page.get_code().endswith(comment)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_editfile(browser):
    # Check ability to open code editor by double clicking on file in workspace.
    project_dict, workspace_page = startup(browser)

    # create a couple of files
    file1 = 'test1.py'
    workspace_page.new_file(file1)
    file2 = 'test2.py'
    workspace_page.new_file(file2)

    # verify file is opened in code editor by double clicking
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.edit_file(file1)
    eq(str(editor_page.get_tab_label()), '/' + file1)

    # verify different file is opened in code editor by double clicking
    browser.switch_to_window(workspace_window)
    editor_page = workspace_page.edit_file(file2)
    eq(str(editor_page.get_tab_label()), '/' + file2)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # verify code editor can be re-opened by double clicking on file
    workspace_window = browser.current_window_handle
    if broken_chrome():
        raise SkipTest('Test broken for chrome/selenium combination')
    editor_page = workspace_page.edit_file(file1)
    eq(str(editor_page.get_tab_label()), '/' + file1)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_multitab(browser):
    project_dict, workspace_page = startup(browser)

    # Open code editor.
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()

    # Create the file (code editor automatically indents).
    test_code1 = """
def f(x):
return math.sqrt(x)"""

    test_code2 = """
def g(x):
return x**2"""

    editor_page.new_file('test1.py', test_code1)
    editor_page.new_file('test2.py', test_code2)

    editor_page.edit_file('test1.py')
    editor_page.add_text_to_file('\n #an extra comment line')
    input_code1 = editor_page.get_code()
    editor_page.save_document()

    editor_page.edit_file('test2.py')
    editor_page.add_text_to_file('\n #an extra comment line')
    input_code2 = editor_page.get_code()

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Go back to code editor, open file, verify source code
    if broken_chrome():
        raise SkipTest('Test broken for chrome/selenium combination')
    editor_page = workspace_page.edit_file('test1.py')  # this file was saved
    time.sleep(1)
    loaded_code = editor_page.get_code()
    eq(input_code1, loaded_code)

    editor_page.edit_file('test2.py')  # this file was not saved
    time.sleep(1)
    loaded_code = editor_page.get_code()
    neq(input_code2, loaded_code)

    # Clean up.
    browser.close()
    browser.switch_to_window(workspace_window)
    closeout(project_dict, workspace_page)


def _test_newfile(browser):
    # Creates a file in the GUI.
    project_dict, workspace_page = startup(browser)

    # Open code editor.
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()

    # test the 'ok' and 'cancel' buttons on the new file dialog
    dlg = editor_page.new_file_dialog()
    dlg.set_text('ok_file1')
    dlg.click_ok()
    NotifierPage.wait(editor_page)

    dlg = editor_page.new_file_dialog()
    dlg.set_text('cancel_file')
    dlg.click_cancel()

    dlg = editor_page.new_file_dialog()
    dlg.set_text('ok_file2')
    dlg.click_ok()
    NotifierPage.wait(editor_page)

    file_names = editor_page.get_files()
    expected_file_names = ['ok_file1', 'ok_file2']
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Create the file (code editor automatically indents).
    editor_page.new_file('plane.py', """
from openmdao.main.api import Component
from openmdao.main.datatypes.api import Float

# lines will be auto-indented by ace editor
class Plane(Component):

x1 = Float(0.0, iotype='in')
x2 = Float(0.0, iotype='in')
x3 = Float(0.0, iotype='in')

f_x = Float(0.0, iotype='out')
""")

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Drag over Plane.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow('plane.Plane', 'plane')

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_maxmin(browser):
    # Toggles maxmimize/minimize button on assemblies.
    project_dict, workspace_page = startup(browser)

    # verify that the globals figure is invisible
    globals_figure = workspace_page.get_dataflow_figure('')
    assert globals_figure.border.find('none') >= 0
    eq(globals_figure.background_color, 'rgba(0, 0, 0, 0)')

    # Add maxmin.py to project
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/maxmin.py')
    workspace_page.add_file(file_path)

    # Add MaxMin to 'top'.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'top'])
    maxmin = workspace_page.add_library_item_to_dataflow('maxmin.MaxMin',
                                                         'maxmin', prefix='top')
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'maxmin', 'top'])

    workspace_page.hide_left()

    # Maximize maxmin.
    background = maxmin('top_right').value_of_css_property('background')
    assert background.find('circle-plus.png') >= 0

    maxmin('top_right').click()
    time.sleep(0.5)
    background = maxmin('top_right').value_of_css_property('background')
    assert background.find('circle-minus.png') >= 0
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'driver', 'maxmin', 'sub', 'top'])

    sub = workspace_page.get_dataflow_figure('sub')
    sub('top_right').click()
    time.sleep(0.5)
    background = sub('top_right').value_of_css_property('background')
    assert background.find('circle-minus.png') >= 0
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'driver', 'driver', 'extcode', 'maxmin', 'sub', 'top'])

    # issue a command and make sure maxmin is still maximized
    workspace_page.do_command('dir()')
    background = maxmin('top_right').value_of_css_property('background')
    assert background.find('circle-minus.png') >= 0
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'driver', 'driver', 'extcode', 'maxmin', 'sub', 'top'])

    # Minimize sub
    sub('top_right').click()
    background = sub('top_right').value_of_css_property('background')
    assert background.find('circle-plus.png') >= 0
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'driver', 'maxmin', 'sub', 'top'])

    # remove maxmin and make sure its children are removed as well
    maxmin.remove()
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['driver', 'top'])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_connect(browser):
    project_dict, workspace_page = startup(browser)

    # Import connect.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/connect.py')
    workspace_page.add_file(file_path)
    workspace_page.add_library_item_to_dataflow('connect.Topp', 'top')

    # Connect components.
    workspace_page.show_dataflow('top')
    comp1 = workspace_page.get_dataflow_figure('comp1', 'top')
    comp2 = workspace_page.get_dataflow_figure('comp2', 'top')
    conn_page = workspace_page.connect(comp1, comp2)
    time.sleep(0.5)
    conn_page.move(-100, -100)
    eq(conn_page.dialog_title, 'Connections: top')
    eq(conn_page.source_component, 'comp1')
    eq(conn_page.target_component, 'comp2')
    for prefix in ('b', 'e', 'f', 'i', 's', 'w'):
        conn_page.connect_vars('comp1.' + prefix + '_out',
                               'comp2.' + prefix + '_in')
        time.sleep(0.5)  # Wait for display update.

    conn_page.set_source_expression('comp1.f_out+comp1.i_out')
    conn_page.target_variable = 'comp2.x_in'
    conn_page.connect()

    time.sleep(0.5)  # Wait for display update.

    eq(conn_page.count_variable_figures(), 21)
    eq(conn_page.count_variable_connections(), 9)  # 3 connections for the expr

    conn_page.close()

    # Set inputs (re-fetch required after updating).
    comp1 = workspace_page.get_dataflow_figure('comp1', 'top')
    props = comp1.properties_page()
    props.move(0, -120)  # Move up for short displays.
    time.sleep(0.5)      # Wait for header update.
    eq(props.header, 'Connectable: top.comp1')
    props.move(-100, -100)
    inputs = props.inputs
    eq(inputs[4].value, ['s_in', ''])
    inputs[4][1] = 'xyzzy'
    inputs = props.inputs
    eq(inputs[2].value, ['f_in', '0'])
    inputs[2][1] = '2.781828'
    inputs = props.inputs
    eq(inputs[3].value, ['i_in', '0'])
    inputs[3][1] = '42'

    inputs = props.inputs
    eq(inputs[0].value, ['b_in', 'False'])
    inputs.rows[0].cells[1].click()
    browser.find_element_by_xpath('//*[@id="bool-editor-b_in"]/option[1]').click()
    #inputs.rows[0].cells[0].click()
    #inputs[0][1] = 'True'

    inputs = props.inputs
    eq(inputs[1].value, ['e_in', '1'])
    inputs.rows[1].cells[1].click()
    browser.find_element_by_xpath('//*[@id="editor-enum-e_in"]/option[3]').click()
    #inputs.rows[2].cells[0].click()
    #inputs[2][1] = '3'

    props.close()

    # Run the simulation.
    top = workspace_page.get_dataflow_figure('top')
    top.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    # Verify outputs.
    comp2 = workspace_page.get_dataflow_figure('comp2', 'top')
    editor = comp2.editor_page()
    editor.move(-100, 0)
    eq(editor.dialog_title, 'Connectable: top.comp2')

    inputs = editor.get_inputs()
    for i, row in enumerate(inputs.value):
        if row[1] == 'w_in':
            eq(row[2], '5000')

    outputs = editor.get_outputs()
    expected = [
        ['', 'b_out', 'True', '', ''],
        ['', 'e_out', '3', '', ''],
        ['', 'f_out', '2.781828', '', ''],
        ['', 'i_out', '42', '', ''],
        ['', 's_out', 'xyzzy', '', ''],
        ['', 'w_out', '5', 'kg', ''],
        ['', 'x_out', '44.781828', '', ''],
        ['', 'derivative_exec_count', '0', '',
         "Number of times this Component's derivative function has been executed."],
        ['', 'exec_count', '1', '',
         'Number of times this Component has been executed.'],
        ['', 'itername', '1-comp2', '', 'Iteration coordinates.'],
    ]
    for i, row in enumerate(outputs.value):
        eq(row, expected[i])

    editor.close()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_connections(browser):
    # Check connection frame functionality.
    project_dict, workspace_page = startup(browser)

    filename = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                               'vehicle_singlesim.py')
    workspace_page.add_file(filename)

    asm_name = 'sim'
    workspace_page.add_library_item_to_dataflow('vehicle_singlesim.VehicleSim',
                                                asm_name)
    # show dataflow for vehicle
    workspace_page.expand_object('sim')
    workspace_page.show_dataflow('sim.vehicle')
    workspace_page.hide_left()
    vehicle = workspace_page.get_dataflow_figure('vehicle', 'sim')

    # no connections between assembly vars
    conn_page = vehicle.connections_page()
    conn_page.move(-50, -100)
    eq(conn_page.dialog_title, 'Connections: vehicle')
    eq(conn_page.source_component, '-- Assembly --')
    eq(conn_page.target_component, '-- Assembly --')
    eq(conn_page.count_variable_connections(), 36)

    # two connections between engine and chassis
    conn_page.set_source_component('engine')
    conn_page.set_target_component('chassis')
    eq(conn_page.count_variable_figures(), 21)
    eq(conn_page.count_variable_connections(), 2)
    conn_page.show_connected_variables()
    time.sleep(0.5)
    eq(conn_page.count_variable_figures(), 4)
    eq(conn_page.count_variable_connections(), 2)
    eq(sorted(conn_page.get_variable_names()),
       ['engine_torque', 'engine_weight', 'mass_engine', 'torque'])

    # one connection between transmission and engine (RPM)
    conn_page.set_source_component('transmission')
    conn_page.set_target_component('engine')
    eq(conn_page.count_variable_figures(), 2)
    eq(conn_page.count_variable_connections(), 1)
    eq(sorted(conn_page.get_variable_names()),
       ['RPM', 'RPM'])

    # disconnect transmission
    conn_page.close()  # Sometimes obscures dataflow.
    tranny = workspace_page.get_dataflow_figure('transmission', 'sim.vehicle')
    tranny.disconnect()
    vehicle = workspace_page.get_dataflow_figure('vehicle', 'sim')
    conn_page = vehicle.connections_page()
    conn_page.move(-50, -100)
    conn_page.show_connected_variables()

    # now there are no connections between transmission and engine
    conn_page.set_source_component('transmission')
    conn_page.set_target_component('engine')
    time.sleep(0.5)
    eq(conn_page.count_variable_figures(), 0)
    eq(conn_page.count_variable_connections(), 0)

    # reconnect transmission RPM to engine RPM
    conn_page.connect_vars('transmission.RPM', 'engine.RPM')
    time.sleep(1)
    eq(conn_page.count_variable_figures(), 2)
    eq(conn_page.count_variable_connections(), 1)
    eq(sorted(conn_page.get_variable_names()),
       ['RPM', 'RPM'])

    # no connections between transmission and chassis
    conn_page.set_target_component('chassis')
    time.sleep(0.5)
    eq(conn_page.count_variable_figures(), 0)
    eq(conn_page.count_variable_connections(), 0)

    # reconnect transmission torque to chassis torque by dragging
    # conn_page.connect_vars('transmission.torque_ratio', 'chassis.torque_ratio')
    conn_page.show_all_variables()
    time.sleep(0.5)
    torque_vars = conn_page.find_variable_name('torque_ratio')
    eq(len(torque_vars), 2)
    chain = ActionChains(browser)
    chain.click_and_hold(torque_vars[0])
    chain.move_to_element(torque_vars[1])
    chain.release(on_element=None).perform()
    time.sleep(1.0)
    eq(conn_page.count_variable_connections(), 1)
    conn_page.show_connected_variables()
    time.sleep(0.5)
    eq(conn_page.count_variable_figures(), 2)
    eq(sorted(conn_page.get_variable_names()),
       ['torque_ratio', 'torque_ratio'])

    # no connections between vehicle assembly and transmission
    conn_page.set_source_component('')
    conn_page.set_target_component('transmission')
    time.sleep(0.5)
    eq(conn_page.count_variable_figures(), 0)
    eq(conn_page.count_variable_connections(), 0)

    # connect assembly variable to component variable
    conn_page.connect_vars('current_gear', 'transmission.current_gear')
    eq(conn_page.count_variable_figures(), 2)
    eq(conn_page.count_variable_connections(), 1)
    eq(sorted(conn_page.get_variable_names()),
       ['current_gear', 'current_gear'])

    # one connection from chassis component to vehicle assembly
    conn_page.set_source_component('chassis')
    conn_page.set_target_component('')
    eq(conn_page.count_variable_figures(), 2)
    eq(conn_page.count_variable_connections(), 1)
    eq(sorted(conn_page.get_variable_names()),
       ['acceleration', 'acceleration'])

    conn_page.close()

    # disconnect chassis
    chassis = workspace_page.get_dataflow_figure('chassis', 'sim.vehicle')
    chassis.disconnect()
    vehicle = workspace_page.get_dataflow_figure('vehicle', 'sim')

    conn_page = vehicle.connections_page()
    conn_page.move(-50, -100)

    eq(conn_page.count_variable_connections(), 18)

    # test invalid variable
    conn_page.connect_vars('chassis.accel', 'acceleration')
    message = NotifierPage.wait(workspace_page)
    eq(message, "Invalid source variable")

    # connect component variable to assembly variable
    conn_page.set_source_component('chassis')
    conn_page.connect_vars('chassis.acceleration', 'acceleration')
    eq(conn_page.count_variable_connections(), 1)
    conn_page.show_connected_variables()
    eq(sorted(conn_page.get_variable_names()),
       ['acceleration', 'acceleration'])

    conn_page.close()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_connect_nested(browser):
    project_dict, workspace_page = startup(browser)

    # Import bem.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/bem.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('bem.BEM', 'top')

    # get connection frame
    workspace_page.show_dataflow('top')
    top = workspace_page.get_dataflow_figure('top')
    conn_page = top.connections_page()

    # select BE0 and perf components
    conn_page.move(-100, -100)
    eq(conn_page.dialog_title, 'Connections: top')
    conn_page.set_source_component('BE0')
    conn_page.set_target_component('perf')
    eq(conn_page.source_component, 'BE0')
    eq(conn_page.target_component, 'perf')
    time.sleep(1)
    connection_count = conn_page.count_variable_connections()

    # check that array is not expanded
    delta_Cts = conn_page.find_variable_name('delta_Ct[0]')
    eq(len(delta_Cts), 0)

    # expand the destination array and connect the source to array variable
    delta_Cts = conn_page.find_variable_name('delta_Ct')
    eq(len(delta_Cts), 2)
    x0 = delta_Cts[0].location['x']
    x1 = delta_Cts[1].location['x']
    if x0 > x1:
        perf_delta_Ct = delta_Cts[0]
    else:
        perf_delta_Ct = delta_Cts[1]
    chain = ActionChains(browser)
    chain.double_click(perf_delta_Ct).perform()
    delta_Cts = conn_page.find_variable_name('delta_Ct[0]')
    eq(len(delta_Cts), 1)
    conn_page.connect_vars('BE0.delta_Ct', 'perf.delta_Ct[0]')
    time.sleep(1)
    eq(conn_page.count_variable_connections(), connection_count + 1)

    # switch source component, destination array should still be expanded
    conn_page.set_source_component('BE1')
    eq(conn_page.source_component, 'BE1')
    time.sleep(1)
    connection_count = conn_page.count_variable_connections()
    delta_Cts = conn_page.find_variable_name('delta_Ct[1]')
    eq(len(delta_Cts), 1)
    conn_page.connect_vars('BE1.delta_Ct', 'perf.delta_Ct[1]')
    time.sleep(1)
    eq(conn_page.count_variable_connections(), connection_count + 1)

    # check connecting var tree to var tree
    conn_page.set_source_component('-- Assembly --')
    eq(conn_page.source_component, '-- Assembly --')
    time.sleep(1)
    connection_count = conn_page.count_variable_connections()
    conn_page.connect_vars('free_stream', 'perf.free_stream')
    time.sleep(1)
    eq(conn_page.count_variable_connections(), connection_count + 1)

    # collapse delta_Ct array and confirm that it worked
    chain = ActionChains(browser)
    delta_Cts = conn_page.find_variable_name('delta_Ct')
    eq(len(delta_Cts), 1)
    chain.double_click(delta_Cts[0]).perform()
    delta_Cts = conn_page.find_variable_name('delta_Ct[0]')
    eq(len(delta_Cts), 0)

    # check connecting var tree variable to variable
    conn_page.set_target_component('BE0')
    eq(conn_page.target_component, 'BE0')
    time.sleep(1)
    connection_count = conn_page.count_variable_connections()
    free_streams = conn_page.find_variable_name('free_stream')
    eq(len(free_streams), 1)
    chain = ActionChains(browser)
    chain.double_click(free_streams[0]).perform()
    free_stream_V = conn_page.find_variable_name('V')
    eq(len(free_stream_V), 1)
    rho = conn_page.find_variable_name('rho')
    eq(len(rho), 2)
    conn_page.connect_vars('free_stream.rho', 'BE0.rho')
    time.sleep(1)
    eq(conn_page.count_variable_connections(), connection_count + 1)

    # Clean up.
    conn_page.close()
    closeout(project_dict, workspace_page)


def _test_driverflows(browser):
    # Excercises display of driver flows (parameters, constraints, objectives).
    project_dict, workspace_page = startup(browser)

    filename = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/rosen_suzuki.py')
    workspace_page.add_file(filename)

    workspace_page.add_library_item_to_dataflow('rosen_suzuki.Simulation', 'top')

    # Show dataflow for Simulation.
    workspace_page.show_dataflow('top')
    workspace_page.hide_left()

    # Select different displays.
    top = workspace_page.get_dataflow_figure('top')
    top.display_dataflows(False)
    time.sleep(0.5)

    # While only driver flows are displayed, check on context menu.
    preproc = workspace_page.get_dataflow_figure('preproc', 'top')
    editor = preproc.input_edit_driver('top.driver')
    editor.move(-100, 0)
    eq(editor.dialog_title, 'CONMINdriver: top.driver')
    outputs = editor.get_parameters()
    expected = [
        ['',
         "('preproc.x_in[0]', 'preproc.x_in[1]', 'preproc.x_in[2]', 'preproc.x_in[3]')",
         '-10', '99', '1', '0', '',
         "('preproc.x_in[0]', 'preproc.x_in[1]', 'preproc.x_in[2]', 'preproc.x_in[3]')"],
    ]
    for i, row in enumerate(outputs.value):
        eq(row, expected[i])
    editor.close()

    #FIXME: can't seem to do context-click on output port.

    top.display_driverflows(False)
    time.sleep(0.5)
    top.display_dataflows(True)
    time.sleep(0.5)
    top.display_driverflows(True)
    time.sleep(0.5)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_replace(browser):
    # Replaces various connected components.
    project_dict, workspace_page = startup(browser)

    filename = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/rosen_suzuki.py')
    workspace_page.add_file(filename)

    workspace_page.add_library_item_to_dataflow('rosen_suzuki.Simulation', 'top')

    # Show dataflow for Simulation.
    workspace_page.show_dataflow('top')
    workspace_page.hide_left()

    # Verify preproc is a PreProc.
    preproc = workspace_page.get_dataflow_figure('preproc', 'top')
    editor = preproc.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'x_in', '[1.0, 1.0, 1.0, 1.0]', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Replace preproc with a ScalingPreProc.
    workspace_page.replace('preproc', 'rosen_suzuki.ScalingPreProc')
    preproc = workspace_page.get_dataflow_figure('preproc', 'top')
    editor = preproc.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'scaler', '1', '', ''],
        ['', 'x_in', '[1.0, 1.0, 1.0, 1.0]', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Verify postproc is a PostProc.
    postproc = workspace_page.get_dataflow_figure('postproc', 'top')
    editor = postproc.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'result_in', '0', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Replace postproc with a ScalingPostProc.
    workspace_page.replace('postproc', 'rosen_suzuki.ScalingPostProc')
    postproc = workspace_page.get_dataflow_figure('postproc', 'top')
    editor = postproc.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'result_in', '0', '', ''],
        ['', 'scaler', '1', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Verify driver is a CONMINdriver.
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    eq(inputs.value[0],
       ['', 'conmin_diff', 'False', '',
        'Set to True to let CONMINcalculate the gradient.'])
    editor.close()

    # Replace driver with an SLSQPdriver.
    workspace_page.replace_driver('top', 'SLSQPdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    eq(inputs.value[0],
       ['', 'accuracy', '0.000001', '', 'Convergence accuracy'])
    editor.close()

    # Verify comp is a OptRosenSuzukiComponent.
    comp = workspace_page.get_dataflow_figure('comp', 'top')
    editor = comp.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'x', '[]', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Replace comp with an Assembly.
    workspace_page.replace('comp', 'openmdao.main.assembly.Assembly')
    expected = "but are missing in the replacement object"
    time.sleep(0.5)
    # messages go to log now, so don't show up in history
    #assert workspace_page.history.find(expected) >= 0

    comp = workspace_page.get_dataflow_figure('comp', 'top')
    editor = comp.editor_page()
    editor.move(-400, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'excludes', '[]', '',
         'Patterns for variables to exclude from the recorders'
         ' (only valid at top level).'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'includes', "['*']", '',
         'Patterns for variables to include in the recorders'
         ' (only valid at top level).'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing'],
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])
    editor.close()

    # Verify new figure.
    comp = workspace_page.get_dataflow_figure('comp', 'top')
    background = comp('top_right').value_of_css_property('background')
    assert background.find('circle-plus.png') >= 0

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_ordering(browser):
    # Verify that adding parameter to driver moves it ahead of target.
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    # Add ExternalCode and SLSQP.
    workspace_page.show_dataflow('top')
    ext = workspace_page.add_library_item_to_dataflow(
              'openmdao.lib.components.external_code.ExternalCode', 'ext',
              prefix='top')
    opt = workspace_page.add_library_item_to_dataflow(
              'openmdao.lib.drivers.slsqpdriver.SLSQPdriver', 'opt',
              prefix='top')

    # Add parameter to SLSQP.
    editor = opt.editor_page(base_type='Driver')
    editor('parameters_tab').click()
    editor.move(-100, -100)
    dialog = editor.new_parameter()
    dialog.target = 'ext.timeout'
    dialog.low = '0'
    dialog.high = '1'
    dialog.name = 'tmo'
    dialog('ok').click()

    # Check that SLSQP is above and to the left of ExternalCode
    ext = workspace_page.get_dataflow_figure('ext', 'top')
    opt = workspace_page.get_dataflow_figure('opt', 'top')
    assert ext.coords[0] > opt.coords[0]
    assert ext.coords[1] > opt.coords[1]

    # Clean up.
    editor.close()
    closeout(project_dict, workspace_page)


def _test_parameter_autocomplete(browser):
    project_dict, workspace_page = startup(browser)
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/model_vartree.py')
    workspace_page.add_file(file_path)
    workspace_page.add_library_item_to_dataflow('model_vartree.Topp',
                                                "vartree", prefix=None)
    workspace_page.replace_driver('vartree', 'SLSQPdriver')

    driver = workspace_page.get_dataflow_figure('driver', 'vartree')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-100, 0)

    editor('parameters_tab').click()
    dialog = editor.new_parameter()

    expected_targets = set([
        'p1.cont_in.v1',
        'p1.cont_in.v2',
        'p1.cont_in.vt2.x',
        'p1.cont_in.vt2.y',
        'p1.cont_in.vt2.vt3.a',
        'p1.cont_in.vt2.vt3.b',
        'p1.directory',
        'p1.force_fd',
        'p1.missing_deriv_policy',
    ])

    autocomplete_targets = [element.text for element in dialog.get_autocomplete_targets('p1')]

    #For p1 (simplecomp) there should only be
    #8 valid autocomplete targets.

    eq(len(autocomplete_targets), 9)

    for target in autocomplete_targets:
        eq(target in expected_targets, True)

    #The autocomplete menu blocks the cancel button.
    #Enter a value in low is to remove the focus from the target cell
    #to get rid of the autocomplete menu.
    dialog.low = '0'

    dialog('cancel').click()

    editor.close()
    closeout(project_dict, workspace_page)


def _test_io_filter_without_vartree(browser):

    project_dict, workspace_page = startup(browser)
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'CONMINdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page()
    editor.move(-100, 0)

    editor.show_inputs()

    #Test filtering inputs

    #filter on name='ctlmin'
    editor.filter_inputs("ctlmin")
    eq([u'', u'ctlmin', u'0.001', u'',
        u'Minimum absolute value of ctl used in optimization.'],
       editor.get_inputs().value[0])
    editor.clear_inputs_filter()

    #filter on description='conjugate'
    editor.filter_inputs("conjugate")
    eq([u'', u'icndir', u'0', u'', u'Conjugate gradient restart. parameter.'],
       editor.get_inputs().value[0])
    editor.clear_inputs_filter()

    #filter on description='Conjugate'
    editor.filter_inputs("Conjugate")
    eq([u'', u'icndir', u'0', u'', u'Conjugate gradient restart. parameter.'],
       editor.get_inputs().value[0])
    editor.clear_inputs_filter()

    #filter on term='print'
    #filter should match items in name and description column
    expected = [
        [u'', u'iprint', u'0', u'', u'Print information during CONMIN solution.'
         ' Higher values are more verbose. 0 suppresses all output.'],
    ]

    editor.filter_inputs("print")
    inputs = editor.get_inputs()
    eq(expected, inputs.value)

    # Verify that editing a value doesn't clear the filter.
    inputs[0].cells[2].select(1)
    expected[0][2] = u'1'
    inputs = editor.get_inputs()
    eq(expected, inputs.value)

    editor.clear_inputs_filter()

    editor.show_outputs()

    #Test filtering outputs

    #filter on name='derivative_exec_count'
    editor.filter_outputs("derivative_exec_count")
    eq([u'', u'derivative_exec_count', u'0', u'',
        u"Number of times this Component's derivative function has been executed."],
       editor.get_outputs().value[0])
    editor.clear_outputs_filter()

    #filter on description='coordinates'
    editor.filter_outputs("coordinates")
    eq([u'', u'itername', u'', u'', u"Iteration coordinates."],
       editor.get_outputs().value[0])
    editor.clear_outputs_filter()

    #filter on term='time'.
    editor.filter_outputs("time")
    expected = [
        [u'', u'derivative_exec_count', u'0', u'',
         u"Number of times this Component's derivative function has been executed."],
        [u'', u'exec_count', u'0', u'',
         u"Number of times this Component has been executed."]
    ]

    eq(expected, editor.get_outputs().value)

    #filter on term='Time'.
    editor.filter_outputs("Time")
    expected = [
        [u'', u'derivative_exec_count', u'0', u'',
         u"Number of times this Component's derivative function has been executed."],
        [u'', u'exec_count', u'0', u'',
         u"Number of times this Component has been executed."]
    ]

    eq(expected, editor.get_outputs().value)
    editor.close()

    closeout(project_dict, workspace_page)


def _test_io_filter_with_vartree(browser):
    project_dict, workspace_page = startup(browser)

    #Test filtering variable trees
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/model_vartree.py')
    workspace_page.add_file(file_path)
    workspace_page.add_library_item_to_dataflow('model_vartree.Topp',
                                                "vartree", prefix=None)
    workspace_page.show_dataflow("vartree")

    comp = workspace_page.get_dataflow_figure('p1', "vartree")
    editor = comp.editor_page()
    editor.move(-100, 0)

    editor.show_inputs()

    #filter when tree is expanded, filter on name="b"
    editor.filter_inputs("b")
    expected = [
        [u'', u' cont_in', u'', u'', u''],
        [u'', u' vt2', u'', u'', u''],
        [u'', u' vt3', u'', u'', u''],
        [u'', u'b', u'12', u'inch', u''],
        [u'', u'directory', u'', u'', u'If non-blank, the directory to execute in.'],
        [u'', u'missing_deriv_policy', u'error', u'',
         u'Determines behavior when some analytical derivatives are provided but some are missing']
    ]

    eq(expected, editor.get_inputs().value)
    time.sleep(3)

    #filter when tree is collapsed, filter on units="ft"
    editor.filter_inputs("ft")
    expected = [
        [u'', u' cont_in', u'', u'', u''],
        [u'', u' vt2', u'', u'', u''],
        [u'', u' vt3', u'', u'', u''],
        [u'', u'a', u'1', u'ft', u''],
    ]
    eq(expected, editor.get_inputs().value)

    editor.show_outputs()

    #filter when tree is expanded, filter on name="b"
    editor.filter_outputs("b")
    expected = [
        [u'', u' cont_out', u'', u'', u''],
        [u'', u' vt2', u'', u'', u''],
        [u'', u' vt3', u'', u'', u''],
        [u'', u'b', u'12', u'inch', u''],
        [u'', u'derivative_exec_count', u'0', u'',
         u"Number of times this Component's derivative function has been executed."],
        [u'', u'exec_count', u'0', u'',
         u"Number of times this Component has been executed."]
    ]

    eq(expected, editor.get_outputs().value)
    time.sleep(3)

    #filter when tree is collapsed, filter on units="ft"
    editor.filter_outputs("ft")
    expected = [
        [u'', u' cont_out', u'', u'', u''],
        [u'', u' vt2', u'', u'', u''],
        [u'', u' vt3', u'', u'', u''],
        [u'', u'a', u'1', u'ft', u''],
    ]
    eq(expected, editor.get_outputs().value)

    editor.close()
    closeout(project_dict, workspace_page)


def _test_column_sorting(browser):
    Version = ComponentPage.Version
    SortOrder = ComponentPage.SortOrder

    def test_sorting(expected, grid, sort_order):
        names = None
        variables = None

        if grid == "inputs":
            editor.show_inputs()
            editor.sort_inputs_column("Name", sort_order)

            variables = editor.get_inputs()

        else:
            editor.show_outputs()
            editor.sort_outputs_column("Name", sort_order)
            variables = editor.get_outputs()

        names = [variable.name.value for variable in variables]

        for index, name in enumerate(names):
            eq(name, expected[index])

    project_dict, workspace_page = startup(browser)
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'SLSQPdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(version=Version.NEW)
    editor.move(-100, 0)

    test_sorting(
        ["accuracy", "iout", "iprint", "maxiter",
         "output_filename", "directory", "force_fd",
         " gradient_options"], "inputs",
        SortOrder.ASCENDING
    )

    test_sorting(
        [" gradient_options", "force_fd",
         "directory", "output_filename", "maxiter", "iprint", "iout",
         "accuracy"], "inputs",
        SortOrder.DESCENDING
    )

    editor.get_input(" gradient_options").name.click()

    test_sorting(
        ["accuracy", "iout", "iprint", "maxiter",
         "output_filename", "directory", "force_fd",
         " gradient_options", "derivative_direction", "directional_fd", "fd_blocks", "fd_form", "fd_step", "fd_step_type",
         "force_fd", "gmres_maxiter", "gmres_tolerance"], "inputs",
        SortOrder.ASCENDING
    )

    test_sorting(
         [" gradient_options", "gmres_tolerance", "gmres_maxiter",
         "force_fd", "fd_step_type", "fd_step", "fd_form", "fd_blocks", "directional_fd", "derivative_direction",
         "force_fd", "directory",
         "output_filename", "maxiter", "iprint", "iout", "accuracy"], "inputs",
        SortOrder.DESCENDING
    )

    test_sorting(
        ["error_code", "derivative_exec_count", "exec_count", "itername"],
        "outputs",
        SortOrder.ASCENDING
    )

    test_sorting(
        ["itername", "exec_count", "derivative_exec_count", "error_code"],
        "outputs",
        SortOrder.DESCENDING
    )

    editor.close()

    top = workspace_page.get_dataflow_figure('top')
    top.remove()

    workspace_page.reload_project()
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/model_vartree.py')
    workspace_page.add_file(file_path)
    workspace_page.add_library_item_to_dataflow('model_vartree.Topp',
                                                "apples", offset=(120, 90))
    #workspace_page.show_dataflow("vartree")

    comp = workspace_page.get_dataflow_figure('p1', "apples")
    editor = comp.editor_page(version=Version.NEW)

    editor.get_input(" cont_in").name.click()
    editor.get_input(" vt2").name.click()
    editor.get_input(" vt3").name.click()

    #Testing sort for inputs
    editor.get_input("missing_deriv_policy")
    test_sorting(
        [" cont_in", "v1", "v2", " vt2", " vt3", "a", "b", "x", "y",
         "directory", "force_fd", "missing_deriv_policy"],
        "inputs",
        SortOrder.ASCENDING
    )

    test_sorting(
        ["missing_deriv_policy", "force_fd", "directory",
         " cont_in", " vt2", "y", "x", " vt3", "b", "a", "v2", "v1"],
        "inputs",
        SortOrder.DESCENDING
    )

    #Testing sort for outputs
    editor.get_output(" cont_out").name.click()
    editor.get_output(" vt2").name.click()
    editor.get_output(" vt3").name.click()

    test_sorting(
        [" cont_out", "v1", "v2", " vt2", " vt3", "a", "b", "x", "y",
         "derivative_exec_count", "exec_count", "itername"],
        "outputs",
        SortOrder.ASCENDING
    )

    test_sorting(
        ["itername", "exec_count", "derivative_exec_count", " cont_out",
         " vt2", "y", "x", " vt3", "b", "a", "v2", "v1"],
        "outputs",
        SortOrder.DESCENDING
    )

    editor.close()
    closeout(project_dict, workspace_page)


def _test_taborder(browser):
    project_dict, workspace_page = startup(browser)
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')

    # Replace driver with an SLSQPdriver.
    workspace_page.replace_driver('top', 'SLSQPdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-100, 0)

    # verify that expected tabs appear in expected order
    eq(editor.get_tab_labels(),
       ['Inputs', 'Outputs', 'Parameters', 'Objectives', 'Constraints',
        'Triggers', 'Workflow'])

    editor.close()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_column_picking(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'SLSQPdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page()
    editor.move(-100, 0)

    expected_column_names = ["", "Name", "Value", "Units", "Description"]
    editor.show_inputs()

    input_column_names = [header.value for header in editor.inputs.headers]
    eq(input_column_names, expected_column_names)

    editor.show_outputs()

    output_column_names = [header.value for header in editor.outputs.headers]
    eq(output_column_names, expected_column_names)

    editor.close()
    top = workspace_page.get_dataflow_figure('driver', 'top')
    editor = top.editor_page()

    #Testing for Inputs tab

    #Test that the default columns are loaded first
    expected_column_names = ["", "Name", "Value", "Units", "Description"]

    editor.show_inputs()
    input_column_names = [header.value for header in editor.inputs.headers]

    eq(input_column_names, expected_column_names)

    #Test that low, high and type are added
    editor.toggle_column_visibility("Low")
    editor.toggle_column_visibility("High")
    editor.toggle_column_visibility("Type")

    expected_column_names[2:2] = ["Type"]
    expected_column_names[4:4] = ["High"]
    expected_column_names[5:5] = ["Low"]

    input_column_names = [header.value for header in editor.inputs.headers]

    eq(input_column_names, expected_column_names)

    #Test that the name and description columns are removed
    editor.toggle_column_visibility("Name")
    editor.toggle_column_visibility("Description")

    del expected_column_names[1]
    del expected_column_names[-1]

    input_column_names = [header.value for header in editor.inputs.headers]

    eq(input_column_names, expected_column_names)

    #Testing for Outputs tab

    #Test that the default columns are loaded first.
    editor.show_outputs()
    expected_column_names = ["", "Name", "Value", "Units", "Description"]

    output_column_names = [header.value for header in editor.outputs.headers]
    eq(output_column_names, expected_column_names)

    #Test that the units and name columns are removed
    #column_picker = editor.outputs.headers[0].get_column_picker()

    editor.toggle_column_visibility("Units")
    editor.toggle_column_visibility("Name")

    output_column_names = [header.value for header in editor.outputs.headers]

    del expected_column_names[1]
    del expected_column_names[2]

    eq(output_column_names, expected_column_names)

    #Test that the low column is shown
    editor.toggle_column_visibility("Low")

    expected_column_names[2:2] = ["Low"]
    output_column_names = [header.value for header in editor.outputs.headers]
    eq(output_column_names, expected_column_names)

    editor.close()

    editor = top.editor_page()

    #Reload the editor and check that the column settings
    #for the Inputs and Outputs tabs were recalled
    editor.show_inputs()
    expected_column_names = ["", "Type", "Value", "High", "Low", "Units"]
    input_column_names = [header.value for header in editor.inputs.headers]
    eq(input_column_names, expected_column_names)

    editor.show_outputs()
    expected_column_names = ["", "Value", "Low", "Description"]
    output_column_names = [header.value for header in editor.outputs.headers]
    eq(output_column_names, expected_column_names)

    editor.close()

    closeout(project_dict, workspace_page)


def _test_remove_tla(browser):
    # verify that adding, removing, and adding a top level assembly works.
    project_dict, workspace_page = startup(browser)
    eq(len(workspace_page.get_dataflow_figures()), 1)

    # create a top assembly and check number of figures
    workspace_page.add_library_item_to_dataflow(
        'openmdao.main.assembly.Assembly', 'top1')
    eq(len(workspace_page.get_dataflow_figures()), 3)

    # add component to top assembly and check for additional figure
    workspace_page.add_library_item_to_dataflow(
                    'openmdao.lib.components.external_code.ExternalCode', 'ext',
                    target_name='top1')
    eq(len(workspace_page.get_dataflow_figures()), 4)

    # remove top and check that it and it's child figures are gone
    top = workspace_page.get_dataflow_figure('top1')
    top.remove()
    eq(len(workspace_page.get_dataflow_figures()), 1)

    # add a new top, verify on screen.
    workspace_page.add_library_item_to_dataflow(
        'openmdao.main.assembly.Assembly', 'top2')
    eq(len(workspace_page.get_dataflow_figures()), 3)

    # clean up
    closeout(project_dict, workspace_page)

def _test_drop_on_driver(browser):
    project_dict, workspace_page = startup(browser)

    # replace the 'top' assembly driver with a CONMINdriver
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'CONMINdriver')

    # Check to see that the content area for the driver is now CONMINdriver
    driver_element = workspace_page.get_dataflow_figure('driver')
    eq(driver_element('content_area').find_element_by_xpath('center/i').text,
        'CONMINdriver', "Dropping CONMINdriver onto existing driver did not replace it")

    closeout(project_dict, workspace_page)


def _test_workspace_dragdrop(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    top = workspace_page.get_dataflow_figure('top')

    assembly = workspace_page.find_library_button('Assembly')

    names = []
    for div in top.get_drop_targets():
        chain = workspace_page.drag_element_to(assembly, div, False)
        workspace_page.check_highlighting(top('content_area').element, True,
                           "Top's content_area")
        workspace_page.release(chain)

        #deal with the modal dialog
        name = NameInstanceDialog(workspace_page).create_and_dismiss()
        names.append(name)

    workspace_page.ensure_names_in_workspace(names,
        "Dragging 'assembly' to 'top' in one of the drop areas did not "
        "produce a new element on page")

    # now test to see if all the new elements are children of 'top'

    # generate what the pathnames SHOULD be
    guess_pathnames = ["top." + name for name in names]

    # get the actual pathnames
    figs = workspace_page.get_dataflow_figures()
    pathnames = [fig.get_pathname() for fig in figs]

    # see if they match up! (keeping in mind that there are more elements
    # we have pathnames for than we put there)
    for path in guess_pathnames:
        eq(path in pathnames, True, "An element did not drop into 'top' when "
           "dragged onto one of its drop areas.\nIt was created somewhere else")

    closeout(project_dict, workspace_page)


def _test_drop_on_existing_assembly(browser):
    project_dict, workspace_page = startup(browser)

    assembly = workspace_page.find_library_button('Assembly')

    outer_name = workspace_page.put_element_on_grid('Assembly')
    outer_figure = workspace_page.get_dataflow_figure(outer_name)
    outer_path = outer_figure.pathname

    eq(outer_path, outer_name, "Assembly did not produce an instance on the grid")

    div = outer_figure.get_drop_targets()[0]
    chain = workspace_page.drag_element_to(assembly, div, False)
    workspace_page.check_highlighting(outer_figure('content_area').element, True,
                                      "Assembly's content_area")
    workspace_page.release(chain)

    middle_name = NameInstanceDialog(workspace_page).create_and_dismiss()
    middle_figure = workspace_page.get_dataflow_figure(middle_name)
    middle_path = middle_figure.pathname

    eq(middle_path, outer_path + '.' + middle_name,
        "Assembly did not produce an instance inside outer Assembly")

    div = middle_figure.get_drop_targets()[0]
    chain = workspace_page.drag_element_to(assembly, div, True)
    workspace_page.check_highlighting(middle_figure('content_area').element, True,
                       "Assembly's content_area")
    workspace_page.release(chain)

    inner_name = NameInstanceDialog(workspace_page).create_and_dismiss()
    #expand the middle div so that the inner one shows up in the workspace.
    middle_figure('top_right').element.click()
    inner_figure = workspace_page.get_dataflow_figure(inner_name)
    inner_path = inner_figure.pathname

    eq(inner_path, middle_path + '.' + inner_name,
        "Assembly did not produce an instance inside of the middle Assembly")

    workspace_page.ensure_names_in_workspace([outer_name, middle_name, inner_name],
        "Dragging Assembly onto Assembly did not create a new instance on page")

    closeout(project_dict, workspace_page)


def _test_drop_on_component_editor(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    top = workspace_page.get_dataflow_figure('top', '')

    workspace_page.set_library_filter('Assembly')   # put Assembly at top of lib
    assembly = workspace_page.find_library_button('Assembly')

    editor = top.editor_page(double_click=False, base_type='Assembly')
    editor.show_dataflow()

    # move the editor window down and to the left, away from the library
    editor.move(-200, 200)

    # in order to get the elements in the editor dataflow, we must
    # distinguish them from the elements in the main dataflow
    editor_top = workspace_page.get_dataflow_fig_in_globals('top')

    # sort through these to find the correct 'top'
    names = []
    for div in editor_top.get_drop_targets()[:-1]:
        time.sleep(1)
        chain = workspace_page.drag_element_to(assembly, div, False)
        time.sleep(1)
        workspace_page.check_highlighting(editor_top('content_area').element,
            True, "Top in component editor's content_area")
        workspace_page.release(chain)

        #deal with the modal dialog
        name = NameInstanceDialog(workspace_page).create_and_dismiss()
        names.append(name)

    workspace_page.ensure_names_in_workspace(names,
        "Dragging 'assembly' to 'top' (in component editor) in one of the "
        "drop areas did not produce a new element on page")

    #now test to see if all the new elements are children of 'top'

    #generate what the pathnames SHOULD be
    guess_pathnames = ["top." + name for name in names]

    #get the actual pathnames
    figs = workspace_page.get_dataflow_figures()
    pathnames = [fig.get_pathname() for fig in figs]

    # see if they match up! (keeping in mind that there are more elements
    # we have pathnames for than we put there)
    for path in guess_pathnames:
        eq(path in pathnames, True,
           "An element did not drop into 'top' (in component editor) when "
           "dragged onto one of its drop areas.\nIt was created somewhere else")

    closeout(project_dict, workspace_page)


def _test_drop_on_component_editor_grid(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    top = workspace_page.get_dataflow_figure('top', '')

    workspace_page.set_library_filter('Assembly')   # put Assembly at top of lib
    assembly = workspace_page.find_library_button('Assembly')

    editor = top.editor_page(double_click=False, base_type='Assembly')
    editor.show_dataflow()

    editor_top = workspace_page.get_dataflow_fig_in_globals('top')

    # sort through these to find the correct 'top'

    chain = ActionChains(browser)
    chain.click_and_hold(assembly)
    chain.move_to_element(editor_top('header').find_element_by_xpath("..")).perform()
    chain.move_by_offset(200, 1).perform()
    chain.release(None).perform()

    # don't bother checking to see if it appeared,
    # the UI box will appear and screw the test if it did

    closeout(project_dict, workspace_page)


def _test_component_to_complex_workflow(browser):
    project_dict, workspace_page = startup(browser)

    # Add paraboloid and vehicle_threesim files
    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')
    file2_path = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                 'vehicle_threesim.py')
    workspace_page.add_file(file1_path)
    workspace_page.add_file(file2_path)

    # create an instance of VehicleSim2
    sim_name = workspace_page.put_element_on_grid("VehicleSim2")

    # Drag paraboloid element into sim dataflow figure
    sim = workspace_page.get_dataflow_figure(sim_name)
    paraboloid = workspace_page.find_library_button('Paraboloid')
    chain = workspace_page.drag_element_to(paraboloid, sim('content_area').element, False)
    workspace_page.release(chain)
    paraboloid_name = NameInstanceDialog(workspace_page).create_and_dismiss()
    paraboloid_pathname = sim_name + "." + paraboloid_name

    # Switch to Workflow pane and show the sim workflow
    workspace_page('workflow_tab').click()
    workspace_page.show_workflow(sim_name)

    # See how many workflow component figures there are before we add to it
    eq(len(workspace_page.get_workflow_component_figures()), 16)

    ############################################################################
    # Drop paraboloid component onto the top level workflow for sim
    ############################################################################
    workspace_page('dataflow_tab').click()
    workspace_page.expand_object(sim_name)
    workspace_page.add_object_to_workflow(paraboloid_pathname, sim_name)

    # Confirm that there is one more workflow component figure
    workspace_page('workflow_tab').click()
    eq(len(workspace_page.get_workflow_component_figures()), 17)

    # Confirm that the paraboloid has been added to the sim workflow by trying
    # to access it.
    workspace_page.find_object_button(sim_name + "." + paraboloid_name)

    ############################################################################
    # Drop paraboloid component onto the sim_acc workflow under sim
    ############################################################################
    workspace_page('dataflow_tab').click()
    simsim_name = sim_name + '.sim_acc'
    workspace_page.add_object_to_workflow(paraboloid_pathname, simsim_name)

    # Confirm that there is one more workflow component figure
    workspace_page('workflow_tab').click()
    eq(len(workspace_page.get_workflow_component_figures()), 18)

    # Confirm that the paraboloid has been added to the sim workflow by trying
    # to access it.
    workspace_page.find_object_button(sim_name + "." + paraboloid_name)

    ############################################################################
    # Drop paraboloid component onto the vehicle workflow under sim_acc
    # This should NOT work since the paraboloid is not in the vehicle assembly
    ############################################################################

    # These error messages are tested in SequentialFlow, though we may want
    # to have one test that makes sure that the error dialog makes it through.

    #workspace_page('dataflow_tab').click()
    #workspace_page.expand_object(simsim_name)
    #simsimsim_name = simsim_name + '.vehicle'
    #workspace_page.add_object_to_workflow(paraboloid_pathname, simsimsim_name)
    #message = NotifierPage.wait(workspace_page)
    #eq(message, "x")

    # Confirm that there is NOT a new workflow component figure
    #workspace_page('workflow_tab').click()
    #eq(len(workspace_page.get_workflow_component_figures()), 18)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_drop_onto_layered_div(browser):
    # FIXME: problem with test successfully DnDing from dataflow to workflow figure
    return

    project_dict, workspace_page = startup(browser)

    # Add paraboloid and vehicle_threesim files
    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                'paraboloid.py')
    file2_path = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                            'vehicle_threesim.py')
    workspace_page.add_file(file1_path)
    workspace_page.add_file(file2_path)

    # add VehicleSim2 to the globals
    sim_name = workspace_page.put_element_on_grid('VehicleSim2')

    # add Paraboloid to VehicleSim dataflow assembly
    sim = workspace_page.get_dataflow_figure(sim_name)
    paraboloid = workspace_page.find_library_button('Paraboloid')
    chain = workspace_page.drag_element_to(paraboloid,
                            sim('content_area').element, False)
    workspace_page.release(chain)
    paraboloid_name = NameInstanceDialog(workspace_page).create_and_dismiss()
    paraboloid_pathname = sim_name + "." + paraboloid_name

    # Open up the component editor for the sim_EPA_city inside the vehicle sim
    sim_EPA_city_driver = workspace_page.get_dataflow_figure('sim_EPA_city',
                                                             sim_name)
    driver_editor = sim_EPA_city_driver.editor_page(base_type='Driver')
    driver_editor.move(800, 800)
    driver_editor.show_workflow()

    # Confirm expected number of workflow component figures before adding one
    eq(len(driver_editor.get_workflow_component_figures()), 5)
    eq(len(workspace_page.get_workflow_component_figures()), 22)

    # Drag paraboloid component into sim_EPA_city workflow
    workspace_page('dataflow_tab').click()
    workspace_page.add_object_to_workflow_figure(
        paraboloid_pathname, 'sim_EPA_city', target_page=driver_editor)

    # Confirm there is one more workflow component figure in the editor
    eq(len(driver_editor.get_workflow_component_figures()), 6)

    # Clean up.
    driver_editor.close()
    closeout(project_dict, workspace_page)

def _test_addfiles(browser):
    # Adds multiple files to the project.
    project_dict, workspace_page = startup(browser)

    # Get path to  paraboloid file.
    paraboloidPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                                     'paraboloid.py')

    # Get path to optimization_unconstrained file.
    optPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                              'optimization_unconstrained.py')

    # Add the files
    # would like to test adding multiple files but Selenium doesn't support it
    #workspace_page.add_files(paraboloidPath, optPath)
    workspace_page.add_file(paraboloidPath)
    workspace_page.add_file(optPath)

    # Check to make sure the files were added.
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    expected_file_names = ['optimization_unconstrained.py', 'paraboloid.py']
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_hidden_files(browser):
    project_dict, workspace_page = startup(browser)

    # there are no visible files in a new project
    file_names = workspace_page.get_files()
    eq(len(file_names), 0)

    # show hidden files using file tree pane context menu
    workspace_page.toggle_files()

    # confirm that formerly hidden files are now visible
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    assert '_settings.cfg' in file_names

    # hide files again using file tree pane context menu
    workspace_page.toggle_files()

    # there should be no visible files
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    eq(len(file_names), 0)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_rename_file(browser):
    # Rename a file in the project.
    project_dict, workspace_page = startup(browser)

    # Add paraboloid.py
    paraboloidPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                                     'paraboloid.py')
    workspace_page.add_file(paraboloidPath)
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    eq(file_names, ['paraboloid.py'])

    workspace_page.rename_file('paraboloid.py', 'xyzzy.py')
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    eq(file_names, ['xyzzy.py'])

    # Clean up.
    #closeout(projects_page, project_info_page, project_dict, workspace_page)
    closeout(project_dict, workspace_page)


def _test_remove_files(browser):
    # Adds multiple files to the project.
    project_dict, workspace_page = startup(browser)

    # Add some files
    paraboloidPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                                     'paraboloid.py')
    optPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                              'optimization_unconstrained.py')
    workspace_page.add_file(paraboloidPath)
    workspace_page.add_file(optPath)

    expected_file_names = ['optimization_unconstrained.py', 'paraboloid.py']

    # Check to make sure the files were added.
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # test delete file using context menu, but cancel the confirmation
    workspace_page.delete_file('paraboloid.py', False)

    # Check to make sure the file was NOT deleted
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # test delete file using context menu
    workspace_page.delete_file('paraboloid.py')

    expected_file_names = ['optimization_unconstrained.py', ]

    # Check to make sure the file was deleted
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # add more files
    file_path_one = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                    'files/basic_model.py')
    file_path_two = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                    'vehicle_singlesim.py')
    workspace_page.add_file(file_path_one)
    workspace_page.add_file(file_path_two)

    expected_file_names = ['optimization_unconstrained.py', 'basic_model.py', 'vehicle_singlesim.py']

    # Test deleting multiple files using the delete files pick
    #   on the Files menu, but cancel the confirmation
    workspace_page.delete_files(['vehicle_singlesim.py', 'optimization_unconstrained.py'], False)

    # toggle hidden files on and off to reset selected/highlighted files
    workspace_page.toggle_files()
    workspace_page.toggle_files()

    # Check to make sure the files were NOT deleted
    time.sleep(1.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Test deleting multiple files using the delete files pick
    #   on the Files menu
    workspace_page.delete_files(['vehicle_singlesim.py', 'optimization_unconstrained.py'])

    expected_file_names = ['basic_model.py']

    # Check to make sure the files were deleted
    time.sleep(1.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Test deleting a file in a folder
    workspace_page.new_folder('test_folder')
    time.sleep(1.0)
    workspace_page.add_file_to_folder('test_folder', paraboloidPath)
    time.sleep(2.0)
    workspace_page.expand_folder('test_folder')
    time.sleep(1.0)
    workspace_page.delete_files(['test_folder/paraboloid.py', ])

    expected_file_names = ['basic_model.py']

    # Check to make sure the file was deleted
    time.sleep(1.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_remove_folder(browser):
    # Adds multiple files to the project.
    project_dict, workspace_page = startup(browser)

    # Test deleting a folder, but cancel the confirmation
    workspace_page.new_folder('test_folder')
    time.sleep(1.0)

    paraboloidPath = pkg_resources.resource_filename('openmdao.examples.simple',
                                                     'paraboloid.py')
    workspace_page.add_file_to_folder('test_folder', paraboloidPath)
    time.sleep(2.0)
    workspace_page.expand_folder('test_folder')
    time.sleep(1.0)

    workspace_page.delete_files(['test_folder'], False)

    expected_file_names = ['paraboloid.py']

    # Check to make sure the folder was NOT deleted
    time.sleep(1.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # toggle hidden files on and off to reset selected/highlighted files
    workspace_page.toggle_files()
    workspace_page.toggle_files()

    # Test deleting a folder
    time.sleep(1.0)
    workspace_page.delete_files(['test_folder'])

    expected_file_names = []

    # Check to make sure the folder was deleted
    time.sleep(1.5)
    file_names = workspace_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_view_file(browser):
    project_dict, workspace_page = startup(browser)
    workspace_window = browser.current_window_handle

    # add an image file
    file_name = 'Engine_Example_Process_Diagram.png'
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/' + file_name)
    workspace_page.add_file(file_path)

    time.sleep(2)

    # view the image file in browser
    new_page = workspace_page.view_file(file_name)

    time.sleep(2)

    # the new page should have an img tag with the selected file name
    images = new_page.browser.find_elements_by_css_selector('img')
    eq(len(images), 1)
    eq(images[0].get_attribute('src').strip().endswith(file_name), True)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # add a pdf file
    file_name = 'sample.pdf'
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/' + file_name)
    workspace_page.add_file(file_path)

    time.sleep(2)

    # view the pdf file in browser
    new_page = workspace_page.view_file(file_name)

    time.sleep(2)

    # the new page should have an embed tag with the selected file name
    embeds = new_page.browser.find_elements_by_css_selector('embed')
    eq(len(embeds), 1)
    eq(embeds[0].get_attribute('src').strip().endswith(file_name), True)
    eq(embeds[0].get_attribute('type'), 'application/pdf')

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_view_image(browser):
    project_dict, workspace_page = startup(browser)
    workspace_window = browser.current_window_handle

    # add an image file
    file1_name = 'Engine_Example_Process_Diagram.png'
    file1_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                 'files/' + file1_name)
    workspace_page.add_file(file1_path)
    time.sleep(1)

    # view the image file
    images_page = workspace_page.view_image(file1_name)
    time.sleep(2)

    # check that the image is displayed
    image = images_page.get_image()
    eq(image.endswith(file1_name), True)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # add an image file to a folder
    workspace_page.new_folder('folder')
    time.sleep(1)
    file2_name = 'bmp_24.bmp'
    file2_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                 'files/' + file2_name)
    workspace_page.add_file_to_folder('folder', file2_path)
    time.sleep(1)

    # view the image file
    workspace_page.expand_folder('folder')
    time.sleep(1)
    images_page = workspace_page.view_image('folder/'+file2_name)
    time.sleep(2)

    # check that the image is displayed
    image = images_page.get_image()
    eq(image.endswith(file2_name), True)

    # check that both images appear in the thumbnails
    thumbnails = images_page.get_thumbnails()
    thumbnails.sort()
    eq(len(thumbnails), 2)
    eq(thumbnails[0].endswith(file1_name), True)
    eq(thumbnails[1].endswith(file2_name), True)

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)

def _test_view_geometry(browser):
    project_dict, workspace_page = startup(browser)
    workspace_window = browser.current_window_handle

    #drop 'GeomComponent' onto the grid
    geom_comp_name = workspace_page.put_element_on_grid('GeomComponent')

    #find it on the page
    geom_comp = workspace_page.get_dataflow_figure(geom_comp_name)

    #open the 'edit' dialog on GeomComponent
    geom_comp_editor = geom_comp.editor_page(False)
    geom_comp_editor.show_slots()

    # Plug BoxParametricGeometry into parametric_geometry
    slot = find_slot_figure(workspace_page, 'parametric_geometry', prefix=geom_comp_name)
    workspace_page.fill_slot_from_library(slot, 'BoxParametricGeometry')

    # Open the geom window
    geom_comp_editor('outputs_tab').click()
    outputs = geom_comp_editor.get_outputs()
    outputs.rows[0].cells[2].click()

    time.sleep(2)  # wait to make sure it is displayed

    # Should be two windows now
    eq(len(browser.window_handles), 2)

    # switch to the geom window
    geom_window = browser.window_handles[-1]
    browser.switch_to_window(geom_window)

    # FIXME: there are still problems with diffing the PNG files.  Not sure
    # if there are differences due to platform or what.  Also on windows
    # document.getElementById("statusline") returns null (could be just a timing thing)
    #  For now, just commenting all of this out until someone has time to
    #  fix it and verify it works on all 3 platforms

    # Compare it to what we expect to get
    # file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
    #                                             'files/box-geom-screenshot.png')

    # hide the framerate status line
    #browser.execute_script( 'document.getElementById("statusline").style.display = "none"')
    #browser.save_screenshot( "geom.png")
    #assert filecmp.cmp( "geom.png", file_path)

    #try:
    #    os.remove("geom.png")
    #except IOError:
    #    pass

    # give it a bit
    time.sleep(3)

    geom_page = GeometryPage.verify(browser, workspace_page.port)

    # if we have a canvas... (some test platforms don't support canvas)
    if geom_page.has_canvas():
        # give it a bit more
        time.sleep(5)

        geom_page.expand_edges()
        edges = geom_page.get_edge_names()
        eq(edges, ['Edge 1', 'Edge 2', 'Edge 3', 'Edge 4', 'Edge 5', 'Edge 6'])

        edges = geom_page.get_edge('Edges')
        edge1 = geom_page.get_edge('Edge 1')
        edge2 = geom_page.get_edge('Edge 2')

        eq([edges.viz, edges.grd, edges.ori], [True, False, False])
        eq([edge1.viz, edge1.grd, edge1.ori], [True, False, False])
        eq([edge2.viz, edge2.grd, edge2.ori], [True, False, False])

        # toggle visibility for an edge
        edge1.viz = False

        # check for expected new edges state
        eq([edges.viz, edges.grd, edges.ori], [False, False, False])
        eq([edge1.viz, edge1.grd, edge1.ori], [False, False, False])
        eq([edge2.viz, edge2.grd, edge2.ori], [True, False, False])

        # toggle visibility for all edges
        edges.viz = True

        # check for expected new edges state
        eq([edges.viz, edges.grd, edges.ori], [True, False, False])
        eq([edge1.viz, edge1.grd, edge1.ori], [True, False, False])
        eq([edge2.viz, edge2.grd, edge2.ori], [True, False, False])

        # check initial state of faces tree
        geom_page.expand_faces()
        faces = geom_page.get_face_names()
        eq(faces, ['Face 1', 'Face 2', 'Face 3', 'Face 4', 'Face 5', 'Face 6'])

        faces = geom_page.get_face('Faces')
        face3 = geom_page.get_face('Face 3')
        face5 = geom_page.get_face('Face 5')

        eq([faces.viz, faces.grd, faces.trn], [True, False, False])
        eq([face3.viz, face3.grd, face3.trn], [True, False, False])
        eq([face5.viz, face5.grd, face5.trn], [True, False, False])

        # toggle transparency for a face
        face3.trn = True

        # check for expected new faces state
        eq([faces.viz, faces.grd, faces.trn], [True, False, False])
        eq([face3.viz, face3.grd, face3.trn], [True, False, True])
        eq([face5.viz, face5.grd, face5.trn], [True, False, False])

        # toggle grid for all faces
        faces.grd = True

        # check for expected new faces state
        eq([faces.viz, faces.grd, faces.trn], [True, True, False])
        eq([face3.viz, face3.grd, face3.trn], [True, True, True])
        eq([face5.viz, face5.grd, face5.trn], [True, True, False])

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


# TODO: this test should probably be moved over into the pygem_diamond distrib
def _test_view_csm(browser):
    try:
        from pygem_diamond import gem
    except ImportError:
        raise SkipTest('pygem_diamond is not installed.')

    project_dict, workspace_page = startup(browser)
    workspace_window = browser.current_window_handle

    # add a CSM geometry file
    file_name = 'box.csm'
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/box.csm')
    workspace_page.add_file(file_path)

    time.sleep(2)

    # view the CSM file
    geom_page = workspace_page.view_geometry(file_name)

    # if we have a canvas... (some test platforms don't support canvas)
    if geom_page.has_canvas():
        time.sleep(5)

        geom_page.expand_edges()
        edges = geom_page.get_edge_names()
        eq(edges, ['Body 1 Edge 1',  'Body 1 Edge 2',  'Body 1 Edge 3',
                   'Body 1 Edge 4',  'Body 1 Edge 5',  'Body 1 Edge 6',
                   'Body 1 Edge 7',  'Body 1 Edge 8',  'Body 1 Edge 9',
                   'Body 1 Edge 10', 'Body 1 Edge 11', 'Body 1 Edge 12'])

        geom_page.expand_faces()
        faces = geom_page.get_face_names()
        eq(faces, ['Body 1 Face 1',  'Body 1 Face 2',  'Body 1 Face 3',
                   'Body 1 Face 4',  'Body 1 Face 5',  'Body 1 Face 6'])

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_view_stl(browser):
    project_dict, workspace_page = startup(browser)
    workspace_window = browser.current_window_handle

    # add a STL geometry file
    file_name = 'box.stl'
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/box.stl')
    workspace_page.add_file(file_path)

    time.sleep(2)

    # view the STL file
    geom_page = workspace_page.view_geometry(file_name)

    # if we have a canvas... (some test platforms don't support canvas)
    if geom_page.has_canvas():
        time.sleep(5)

        geom_page.expand_faces()
        faces = geom_page.get_face_names()
        eq(faces, ['box_solid1'])

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)

def _test_grid(browser):
    #This is for testing the new GridRow functionality.
    #Columns that have non-empty names are added as properties
    #to a row. So you can used grid.rows[row_number].name to the
    #cell corresponding to name, With the cell, you can use cell.value
    #to get the text within the cell.

    #This functionality was added for two reasons
    # - Being able to intuitively refer to cells of a row
    # - Reduce the need to compare arrays of arrays in testing
    #   by calling grid.value

    # New methods were also added to ComponentPage for accessing a 
    # single input or output variable by its name. The function will
    # return the corresponding row object if it exists. Currently,
    # if there are name conflicts, only the first match is returned.

    project_dict, workspace_page = startup(browser)
    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')
    workspace_page.add_file(file1_path)
    workspace_page.add_library_item_to_dataflow('paraboloid.Paraboloid', 'paraboloid')
    paraboloid = workspace_page.get_dataflow_figure("paraboloid")
    editor = paraboloid.editor_page(version=ComponentPage.Version.NEW)


    #Checks all the inputs
    inputs = editor.get_inputs()
    eq(inputs[2].name.value, "directory")
    eq(inputs[2].value.value, "")
    eq(inputs[2].units.value, "")
    eq(inputs[2].description.value, "If non-blank, the directory to execute in.")

    eq(inputs[0].name.value, "x")
    eq(inputs[0].value.value, "0")
    eq(inputs[0].units.value, "")
    eq(inputs[0].description.value, "The variable x")

    eq(inputs[1].name.value, "y")
    eq(inputs[1].value.value, "0")
    eq(inputs[1].units.value, "")
    eq(inputs[1].description.value, "The variable y")

    #Checks all the outputs
    outputs = editor.get_outputs()
    eq(outputs[1].name.value, "derivative_exec_count")
    eq(outputs[1].value.value, "0")
    eq(outputs[1].units.value, "")
    eq(outputs[1].description.value, "Number of times this Component's derivative function has been executed.")

    eq(outputs[2].name.value, "exec_count")
    eq(outputs[2].value.value, "0")
    eq(outputs[2].units.value, "")
    eq(outputs[2].description.value, "Number of times this Component has been executed.")

    eq(outputs[0].name.value, "f_xy")
    eq(outputs[0].value.value, "0")
    eq(outputs[0].units.value, "")
    eq(outputs[0].description.value, "F(x,y)")

    eq(outputs[3].name.value, "itername")
    eq(outputs[3].value.value, "")
    eq(outputs[3].units.value, "")
    eq(outputs[3].description.value, "Iteration coordinates.")

    #Access and test a single varible by name
    x = editor.get_input("x")
    eq(x.name.value, inputs[0].name.value)
    eq(x.value.value, inputs[0].value.value)
    eq(x.units.value, inputs[0].units.value)
    eq(x.description.value, inputs[0].description.value)

    y = editor.get_input("y")
    eq(y.name.value, inputs[1].name.value)
    eq(y.value.value, inputs[1].value.value)
    eq(y.units.value, inputs[1].units.value)
    eq(y.description.value, inputs[1].description.value)

    f_xy = editor.get_output("f_xy")
    eq(f_xy.name.value, outputs[0].name.value)
    eq(f_xy.value.value, outputs[0].value.value)
    eq(f_xy.units.value, outputs[0].units.value)
    eq(f_xy.description.value, outputs[0].description.value)

    #Set a value
    x = editor.get_input("x")
    x.value.value = "1"

    #Fetching a single variable refetches the grid
    x = editor.get_input("x")
    eq(x.value.value, "1")

    #Try setting a non-editable cell. 
    f_xy = editor.get_output("f_xy")

    try:
        f_xy.value.value = "1"
    except IndexError:
        #Attribute error should be raised because the cell is not editable, and thus, the property should not have a setter.
        pass
    else:
        #Otherwise, something went wrong
        self.fail("Exception: An AttributeError was not raised and f_xy.value.value should have no setter.")

    #Cleanup and closeout
    editor.close()
    closeout(project_dict, workspace_page)

def _test_passthrough_editor(browser):
    project_dict, workspace_page = startup(browser)

    # Import variable_editor.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/passthrough_editors.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('passthrough_editors.Topp', "top")

    time.sleep(2)
    top = workspace_page.get_dataflow_figure("top")
    top._context_click('edit_passthroughs')

    expand_i = '//*[@id="p1"]/ins'
    browser.find_element_by_xpath(expand_i).click()
    time.sleep(2)
    y_box = '//*[@id="check_y"]'
    y_btn = browser.find_element_by_xpath(y_box)
    eq(y_btn.is_selected(), True)  # check existing passthrough

    browser.find_element_by_xpath('//*[@id="y"]/a').click()  # remove passthrough
    time.sleep(1)

    workspace_page.do_command("top.list_connections()")
    time.sleep(.5)
    output = workspace_page.history.split("\n")[-1]
    eq("('y', 'p1.y')" in output, False)  # verify removed passthrough

    time.sleep(1)
    browser.find_element_by_xpath('//*[@id="y"]/a').click()
    time.sleep(2)
    workspace_page.do_command("top.list_connections()")
    output = workspace_page.history.split("\n")[-1]
    eq("('y', 'p1.y')" in output, True)  # verify added passthrough

    # Clean up.
    closeout(project_dict, workspace_page)
def _test_last_saved_metadata(browser):

    def last_saved(target):
        def wrapper(projects_page, project_name, timestamp, *args, **kargs):
            workspace_page = projects_page.open_project(project_name)
            result = target(workspace_page)

            projects_page = workspace_page.close_workspace()

            if result is False:
                last_saved = timestamp
            else:
                metadata = projects_page.get_project_metadata(project_name)
                last_saved = date_to_datetime(metadata['last_saved'])
                assert(last_saved > timestamp)

            return projects_page, project_name, last_saved

        return wrapper

    def date_to_datetime(date):
        date_regex = re.compile("(\d+)-(\d+)-(\d+)")
        time_regex = re.compile("(\d+):(\d+):(\d+)")

        match_object = date_regex.search(date)
        year  = int(match_object.group(1))
        month = int(match_object.group(2))
        day   = int(match_object.group(3))

        match_object = time_regex.search(date)
        hours   = int(match_object.group(1))
        minutes = int(match_object.group(2))
        seconds = int(match_object.group(3))

        return datetime.datetime(year, month, day, hours, minutes, seconds)

    @last_saved
    def add_file(workspace_page):
        file_path = pkg_resources.resource_filename('openmdao.gui.test.functional', 'files/simple_paraboloid.py')
        workspace_page.add_file(file_path)

    @last_saved
    def new_file(workspace_page):
        workspace_page.new_file('test_file.py')

    @last_saved
    def rename_file(workspace_page):
        workspace_page.get_files()
        workspace_page.rename_file('test_file.py', 'best_file.py')

    @last_saved
    def edit_file(workspace_page):
        if broken_chrome():
            print "Skipping testing metadata after editing file due to broken chrome driver."
            return False

        workspace_window = browser.current_window_handle

        editor_page = workspace_page.open_editor()
        editor_page.edit_file('test_file.py', dclick=False)
        editor_page.add_text_to_file('#just a comment\n')
        editor_page.save_document(check=False)

        browser.switch_to_window(workspace_window)
        port = workspace_page.port
        workspace_page = WorkspacePage.verify(browser, port)

    @last_saved
    def delete_file(workspace_page):
        workspace_page.delete_file('best_file.py')

    @last_saved
    def add_object(workspace_page):
        workspace_page.add_library_item_to_dataflow("openmdao.main.assembly.Assembly", 'top')

    @last_saved
    def replace_object(workspace_page):
        workspace_page.replace_driver("top", 'SLSQPdriver')

    @last_saved
    def commit_project(workspace_page):
        top = workspace_page.get_dataflow_figure('top')
        top.remove()
        workspace_page.commit_project()

    @last_saved
    def revert_project(workspace_page):
        workspace_page.add_library_item_to_dataflow("openmdao.main.assembly.Assembly", 'top')
        workspace_page = workspace_page.revert_project()


    projects_page = begin(browser)
    projects_page, project_dict = random_project(projects_page.new_project(),
                                                 verify=True, load_workspace=False)

    project_name = project_dict['name']
    metadata = projects_page.get_project_metadata(project_name)
    created_time = date_to_datetime(metadata['created'])

    #Testing metadata for file operations
    projects_page, project_name, add_file_time       = add_file(projects_page, project_name, created_time)
    projects_page, project_name, new_file_time       = new_file(projects_page, project_name, add_file_time)
    projects_page, project_name, edit_file_time      = edit_file(projects_page, project_name, new_file_time)
    projects_page, project_name, rename_file_time    = rename_file(projects_page, project_name, edit_file_time)
    projects_page, project_name, delete_file_time    = delete_file(projects_page, project_name, rename_file_time)

    #Testing metadata for project operations
    projects_page, project_name, add_object_time     = add_object(projects_page, project_name, delete_file_time)
    projects_page, project_name, replace_object_time = replace_object(projects_page, project_name, add_object_time)
    projects_page, project_name, commit_project_time = commit_project(projects_page, project_name, replace_object_time)
    projects_page, project_name, revert_project_time = revert_project(projects_page, project_name, commit_project_time)

    projects_page.delete_project(project_name)


#Test creating a project
def _test_new_project(browser):

    browser_download_location_path = get_browser_download_location_path(browser)

    projects_page = begin(browser)
    eq(projects_page.welcome_text, 'Welcome to OpenMDAO %s' % __version__)

    # Create a project.
    projects_page, project_dict = random_project(projects_page.new_project(),
                                                 verify=True, load_workspace=False)
    # Go back to projects page to see if it is on the list.
    assert projects_page.contains(project_dict['name'])

    # Make sure all the project meta data was saved correctly.
    edit_dialog = projects_page.edit_project(project_dict['name'])
    eq(str(edit_dialog.project_name).strip(), project_dict['name'])
    eq(str(edit_dialog.description).strip(), project_dict['description'])
    eq(str(edit_dialog.version).strip(), project_dict['version'])  # maxlength

    # Edit the project meta data
    project_dict['description'] = "pony express"
    project_dict['version'] = "23432"

    projects_page = edit_project(edit_dialog,
                         project_dict['name'],
                         project_dict['description'],
                         project_dict['version'])

    # Make sure all the new project meta data was saved correctly.
    edit_dialog = projects_page.edit_project(project_dict['name'])
    eq(str(edit_dialog.project_name).strip(), project_dict['name'])
    eq(str(edit_dialog.description).strip(), project_dict['description'])
    eq(str(edit_dialog.version).strip(), project_dict['version'][:5])  # maxlength
    edit_dialog.cancel()

    # Export the project
    projects_page.export_project(project_dict['name'])
    project_pattern = project_dict['name'].replace(' ', '_') + '-*.proj'
    project_pattern = os.path.join(browser_download_location_path,
                                   project_pattern)
    for i in range(10):  # Give the download time to complete.
        time.sleep(1)
        project_path = glob.glob(project_pattern)
        if project_path:
            break
    else:
        assert False, 'Download of %r timed-out' % project_pattern
    assert len(project_path) == 1
    project_path = project_path[0]

    # Delete the project in preparation for reimporting
    projects_page.delete_project(project_dict['name'])

    # Make sure the project was deleted
    assert not projects_page.contains(project_dict['name'], False)

    # Import the project and give it a new name
    projects_page, project_dict = import_project(projects_page.import_project(),
                                                 project_path, verify=True,
                                                 load_workspace=False)
    # Go back to projects page to see if it is on the list.
    assert projects_page.contains(project_dict['name'])

    # Delete the project that was just imported
    projects_page.delete_project(project_dict['name'])

    # remove the downloaded file
    os.remove(project_path)

def _test_list_slot(browser):
    project_dict, workspace_page = startup(browser)

    # replace the 'top' assembly driver with a DOEdriver
    # (this additionally verifies that an issue with DOEdriver slots is fixed)
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'DOEdriver')

    # open the object editor dialog for the driver
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(False)
    editor.move(-200, 200)
    editor.show_slots()

    # get the generator slot figure
    generator_slot = find_slot_figure(workspace_page, 'DOEgenerator',
                                      prefix='top.driver')

    # check that slot is not filled
    eq(False, generator_slot.filled,
        "generator slot is showing as filled when it should not be")

    # drop a FullFactorial onto the generator slot
    workspace_page.fill_slot_from_library(generator_slot, 'FullFactorial')

    # refresh and check that slot is now filled
    time.sleep(1.0)
    generator_slot = find_slot_figure(workspace_page, 'DOEgenerator',
                                      prefix='top.driver')
    eq(True, generator_slot.filled,
       "FullFactorial did not drop into generator slot")

    editor.close()

    # open the object editor dialog for the assembly
    assembly = workspace_page.get_dataflow_figure('top', '')
    editor = assembly.editor_page(False)
    editor.move(-200, 200)
    editor.show_slots()

    # get the recorders slot figure
    recorders_slot = find_slot_figure(workspace_page, 'recorders', prefix='top')

    # check that slot is not filled
    eq(False, recorders_slot.filled,
       "recorders slot is showing as filled when it should not be")

    # set center pane to workflow to make sure workflow doesn't steal drops
    workspace_page('workflow_tab').click()

    # drop a DumpCaseRecorder onto the recorders slot
    recorders_slot = find_slot_figure(workspace_page, 'recorders', prefix='top')
    workspace_page.fill_slot_from_library(recorders_slot, 'DumpCaseRecorder')

    # refresh and check that there is now a DumpCaseRecorder in the first slot
    time.sleep(1.0)  # give it a second to update the figure
    recorders_slot = find_slot_figure(workspace_page, 'recorders[0]',
                                      prefix='top')
    eq(True, recorders_slot.filled,
       "DumpCaseRecorder did not drop into recorders slot")
    klass = recorders_slot.root.find_elements_by_css_selector('text#klass')
    eq(klass[0].text, 'DumpCaseRecorder',
       "Filled slot element should show the correct type (DumpCaseRecorder)")

    # check that there is still an unfilled slot in the list
    recorders_slot = find_slot_figure(workspace_page, 'recorders', prefix='top')
    eq(False, recorders_slot.filled,
       "recorders slot is not showing an unfilled slot")
    klass = recorders_slot.root.find_elements_by_css_selector('text#klass')
    eq(klass[0].text, 'ICaseRecorder',
       "Unfilled slot element should show the correct klass (ICaseRecorder)")

    # drop another CaseRecorder onto the recorders slot
    workspace_page.fill_slot_from_library(recorders_slot, 'CSVCaseRecorder')
    time.sleep(1.0)  # give it a second to update the figure
    recorders_slot = find_slot_figure(workspace_page, 'recorders[1]',
                                      prefix='top')
    eq(True, recorders_slot.filled,
       "CSVCaseRecorder did not drop into recorders slot")

    # check that there is still an unfilled slot in the list
    recorders_slot = find_slot_figure(workspace_page, 'recorders', prefix='top')
    eq(False, recorders_slot.filled,
       "recorders slot is not showing an unfilled slot")
    klass = recorders_slot.root.find_elements_by_css_selector('text#klass')
    eq(klass[0].text, 'ICaseRecorder',
       "Unfilled slot element should show the correct klass (ICaseRecorder)")

    # remove the DumpCaseRecorder from the first slot in the list
    recorders_slot = find_slot_figure(workspace_page, 'recorders[0]',
                                      prefix='top')
    recorders_slot.remove()

    # check that the CSVCaseRecorder is now in the first filled slot
    time.sleep(1.0)  # give it a second to update the figure
    recorders_slot = find_slot_figure(workspace_page, 'recorders[0]',
                                      prefix='top')
    eq(True, recorders_slot.filled,
       "CSVCaseRecorder did not drop into recorders slot")
    klass = recorders_slot.root.find_elements_by_css_selector('text#klass')
    eq(klass[0].text, 'CSVCaseRecorder',
       "Filled slot element should show the correct klass (CSVCaseRecorder)")

    # Clean up.
    editor.close()
    closeout(project_dict, workspace_page)


def _test_slot_subclass(browser):
    # test that a slot will accept subclasses
    project_dict, workspace_page = startup(browser)

    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/slot_test.py')
    workspace_page.add_file(file_path)

    name = workspace_page.put_element_on_grid("AutoAssemb")
    aa = workspace_page.get_dataflow_figure(name)
    editor = aa.editor_page(double_click=False)
    editor.move(-200, 200)

    inputs = editor.get_inputs()
    expected = [
        ['', 'input', '0', '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'excludes', '[]', '',
         'Patterns for variables to exclude from the recorders'
         ' (only valid at top level).'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'includes', "['*']", '',
         'Patterns for variables to include in the recorders'
         ' (only valid at top level).'],
        ['', 'missing_deriv_policy', 'assume_zero', '',
         'Determines behavior when some analytical derivatives are provided but'
         ' some are missing'],
    ]
    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    inputs[0][2] = "10"
    aa.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    outputs = editor.get_outputs()
    expected = [
        ['', 'output',                '80', '', ''],
        ['', 'derivative_exec_count',  '0', '',
         "Number of times this Component's derivative function has been executed."],
        ['', 'exec_count',             '1', '',
         'Number of times this Component has been executed.'],
        ['', 'itername',                '', '', 'Iteration coordinates.'],
    ]
    for i, row in enumerate(outputs.value):
        eq(row, expected[i])

    editor.show_slots()
    recorders_slot = find_slot_figure(workspace_page, 'd2', prefix=name)
    workspace_page.fill_slot_from_library(recorders_slot, 'Dummy2')

    aa.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    outputs = editor.get_outputs()
    expected = [
        ['', 'output',                 '160', '', ''],
        ['', 'derivative_exec_count',    '0', '',
         "Number of times this Component's derivative function has been executed."],
        ['', 'exec_count',               '2', '',
         'Number of times this Component has been executed.'],
        ['', 'itername',                  '', '', 'Iteration coordinates.'],
    ]
    for i, row in enumerate(outputs.value):
        eq(row, expected[i])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_dict_slot(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')

    # load in some files needed for the tests

    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')
    workspace_page.add_file(file1_path)

    file2_path = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                 'transmission.py')
    workspace_page.add_file(file2_path)

    vt_comp_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                   'files/simple_vartree_component.py')
    workspace_page.add_file(vt_comp_path)

    workspace_page.show_dataflow('top')
    args = ["('ratio1', 'ratio2')", "('torque_ratio', 'RPM')"]
    workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.components.metamodel.MetaModel', 'mm', args=args)
    mm_figure = workspace_page.get_dataflow_figure('mm', 'top')
    mm_editor = mm_figure.editor_page()
    mm_editor.show_slots()
    mm_editor.move(-500, 0)  # need clear LOS to the library

    # see what happens when you change the model
    #model_slot = find_slot_figure(workspace_page, 'model', prefix='top.mm')
    #workspace_page.fill_slot_from_library(model_slot, 'Transmission')

    # There should two surrogates slots
    time.sleep(1.0)  # give it a bit to update the figure
    surrogates = browser.find_elements_by_xpath(
        "//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    eq(2, len(surrogates),
       "There should be two surrogates in the surrogates dict but "
       "%d surrogate(s) are being displayed" % len(surrogates))

    # They should all be empty: RPM and torque_ratio
    for surrogate in surrogates:
        eq(False, ("filled" in surrogate.get_attribute('class')),
           "Surrogate should not be filled")

    # Fill the torque_ratio surrogate slot with FloatKrigingSurrogate
    surrogate_slot = find_slot_figure(workspace_page, 'torque_ratio',
                                      prefix='top.mm.surrogates')
    workspace_page.fill_slot_from_library(surrogate_slot, 'KrigingSurrogate')

    # One should be filled now
    time.sleep(2)  # give it a bit to update the figure
    num_surrogates_filled = 0
    surrogates = browser.find_elements_by_xpath(
        "//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    for surrogate in surrogates:
        if "filled" in surrogate.get_attribute('class'):
            num_surrogates_filled += 1
    eq(1, num_surrogates_filled,
       "Exactly one surrogate slot should be filled but "
       "%d are filled" % num_surrogates_filled)

    # Fill the RPM surrogate slot with FloatKrigingSurrogate
    surrogate_slot = find_slot_figure(workspace_page, 'RPM',
                                      prefix='top.mm.surrogates')
    workspace_page.fill_slot_from_library(surrogate_slot,
                                          'FloatKrigingSurrogate')

    # Two should be filled now
    time.sleep(2)  # give it a bit to update the figure
    num_surrogates_filled = 0
    surrogates = browser.find_elements_by_xpath(
        "//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    for surrogate in surrogates:
        if "filled" in surrogate.get_attribute('class'):
            num_surrogates_filled += 1
    eq(2, num_surrogates_filled,
       "Exactly two surrogate slot should be filled but "
       "%d are filled" % num_surrogates_filled)

    # Vartrees currently not supported in the new Metamodel -- KTM

    ## Test with components that have variable trees

    ## test vartree with metamodel
    #model_slot = find_slot_figure(workspace_page, 'model', prefix='top.mm')
    #workspace_page.fill_slot_from_library(model_slot, 'InandOutTree')

    ## There should 3 surrogates slots
    #time.sleep(2)  # give it a bit to update the figure
    #surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    #eq(3, len(surrogates),
        #"There should be three surrogates in the surrogates dict but %d surrogate(s) are being displayed" % len(surrogates))

    ## They should all be empty
    #for surrogate in surrogates:
        #eq(False, ("filled" in surrogate.get_attribute('class')), "Surrogate should not be filled")

    ## Fill the outs.x surrogate slot with FloatKrigingSurrogate
    #surrogate_slot = find_slot_figure(workspace_page, 'outs.x', prefix='top.mm.surrogates')
    #workspace_page.fill_slot_from_library(surrogate_slot, 'FloatKrigingSurrogate')

    ## One should be filled now
    #time.sleep(2)  # give it a bit to update the figure
    #num_surrogates_filled = 0
    #surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    #for surrogate in surrogates:
        #if "filled" in surrogate.get_attribute('class'):
            #num_surrogates_filled += 1
    #eq(1, num_surrogates_filled,
       #"Exactly one surrogate slot should be filled but %d are filled" % num_surrogates_filled)

    ## Fill the zzz surrogate slot with KrigingSurrogate
    #surrogate_slot = find_slot_figure(workspace_page, 'zzz', prefix='top.mm.surrogates')
    #workspace_page.fill_slot_from_library(surrogate_slot, 'KrigingSurrogate')

    ## Two should be filled now
    #time.sleep(2)  # give it a bit to update the figure
    #num_surrogates_filled = 0
    #surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    #for surrogate in surrogates:
        #if "filled" in surrogate.get_attribute('class'):
            #num_surrogates_filled += 1
    #eq(2, num_surrogates_filled,
       #"Exactly two surrogate slot should be filled but %d are filled" % num_surrogates_filled)

    ## Fill the outs.y surrogate slot with ResponseSurface
    #surrogate_slot = find_slot_figure(workspace_page, 'outs.y', prefix='top.mm.surrogates')
    #workspace_page.fill_slot_from_library(surrogate_slot, 'ResponseSurface', [1, 1])

    ## Three should be filled now
    #time.sleep(2)  # give it a bit to update the figure
    #num_surrogates_filled = 0
    #surrogates = browser.find_elements_by_xpath("//div[starts-with( @id,'SlotFigure-top-mm-surrogates')]")
    #for surrogate in surrogates:
        #if "filled" in surrogate.get_attribute('class'):
            #num_surrogates_filled += 1
    #eq(3, num_surrogates_filled,
       #"Exactly three surrogate slots should be filled but %d are filled" % num_surrogates_filled)

    # Clean up.
    closeout(project_dict, workspace_page)

def _test_MDAO_MDF(browser):
    # Build the MDF model as per the tutorial.

    project_dict, workspace_page = startup(browser)

    # Import the files that contain the disciplines
    file_path = pkg_resources.resource_filename('openmdao.lib.optproblems',
                                                'sellar.py')
    workspace_page.add_file(file_path)

    # Add Disciplines to assembly.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow('sellar.Discipline1', 'dis1')
    workspace_page.add_library_item_to_dataflow('sellar.Discipline2', 'dis2')

    # Replace Run_Once with SLSQP
    workspace_page.replace_driver('top', 'SLSQPdriver')

    # Add Solver
    workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.drivers.iterate.FixedPointIterator',
        'solver')

    # One data connection
    dis1 = workspace_page.get_dataflow_figure('dis1', 'top')
    dis2 = workspace_page.get_dataflow_figure('dis2', 'top')
    conn_page = workspace_page.connect(dis1, dis2)
    conn_page.move(-100, -100)
    conn_page.connect_vars('dis1.y1', 'dis2.y1')
    conn_page.close()

    # Add solver to optimizer workflow
    workspace_page.add_object_to_workflow('top.solver', 'top')

    # Add disciplines to solver workflow
    workspace_page.expand_object('top')
    workspace_page.add_object_to_workflow('top.dis1', 'top.solver')
    workspace_page.add_object_to_workflow('top.dis2', 'top.solver')

    workspace_page('dataflow_tab').click()

    # Configure Solver
    driver = workspace_page.get_dataflow_figure('solver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-100, -100)

    editor('inputs_tab').click()

    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'dis1.y2'
    dialog.low = '-9.e99'
    dialog.high = '9.e99'
    dialog('ok').click()

    editor('constraints_tab').click()
    dialog = editor.new_constraint()
    dialog.expr = 'dis2.y2 = dis1.y2'
    dialog('ok').click()
    editor.close()

    # Configure Optimizer
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-100, -100)

    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'dis1.z1,dis2.z1'
    dialog.low = '-10.0'
    dialog.high = '10.0'
    dialog('ok').click()

    dialog = editor.new_parameter()
    dialog.target = 'dis1.z2,dis2.z2'
    dialog.low = '0.0'
    dialog.high = '10.0'
    dialog('ok').click()

    dialog = editor.new_parameter()
    dialog.target = "dis1.x1"
    dialog.low = '0.0'
    dialog.high = '10.0'
    dialog('ok').click()

    editor('constraints_tab').click()
    dialog = editor.new_constraint()
    dialog.expr = '3.16 < dis1.y1'
    dialog('ok').click()

    dialog = editor.new_constraint()
    dialog.expr = 'dis2.y2 < 24.0'
    dialog('ok').click()

    editor('objectives_tab').click()
    dialog = editor.new_objective()
    dialog.expr = '(dis1.x1)**2 + dis1.z2 + dis1.y1 + math.exp(-dis2.y2)'
    dialog('ok').click()
    editor.close()

    # Set Initial Conditions
    workspace_page.do_command("top.dis1.z1 = top.dis2.z1 = 5.0")
    workspace_page.do_command("top.dis1.z2 = top.dis2.z2 = 2.0")
    workspace_page.do_command("top.dis1.x1 = 1.0")
    workspace_page.do_command("top.solver.tolerance = .00001")

    # Get an implicitly connected output before the run.
    dis1_fig = workspace_page.get_dataflow_figure('dis1', 'top')
    editor = dis1_fig.editor_page()
    outputs = editor.get_outputs()
    eq(outputs.value[0][1:3], ['y1', '0'])
    editor.close()

    # Run the model
    top = workspace_page.get_dataflow_figure('top')
    top.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    # Verify implicitly connected output has been updated with valid result.
    editor = dis1_fig.editor_page()
    outputs = editor.get_outputs()
    eq(outputs.value[0][1], 'y1')
    dis1_y1 = float(outputs.value[0][2])
    if abs(dis1_y1 - 3.16) > 0.01:
        raise TestCase.failureException(
            "Output dis1.y1 did not reach correct value, but instead is %s"
            % dis1_y1)
    editor.close()

    # Check the objective
    workspace_page.do_command("top.dis1.z1")
    output1 = workspace_page.history.split("\n")[-1]
    workspace_page.do_command("top.dis1.z2")
    output2 = workspace_page.history.split("\n")[-1]

    if abs(float(output1) - 1.977657) > 0.01:
        raise TestCase.failureException(
            "Parameter z1 did not reach correct value, but instead is %s"
            % output1)

    if abs(float(output2) - 0.0) > 0.0001:
        raise TestCase.failureException(
            "Parameter z2 did not reach correct value, but instead is %s"
            % output2)

    # Clean up.
    closeout(project_dict, workspace_page)
def _test_partial_array_connections(browser):
    # Creates a file in the GUI.
    project_dict, workspace_page = startup(browser)

    # Import partial_connections.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/partial_connections.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('partial_connections.PartialConnectionAssembly', 'top')

    workspace_page.add_library_item_to_dataflow('partial_connections.PartialConnectionAssembly2', 'top_2')

    paraboloid = workspace_page.get_dataflow_figure("paraboloid_1", "top")
    #var_fields_path = '//*[@id="inArray-editor"]/input'

    props = paraboloid.properties_page()

    #array 1d editor - check that implicitly connected elements are disabled
    inputs = props.inputs

    # Can't single click on an entry you are focused on, so focus on next line, then come back.
    inputs.rows[1].cells[1].click()
    inputs.rows[0].cells[1].click()
    array_inputs_path = '//*[@id="inArray-editor"]/input'
    cancel_path = '//*[@id="array-edit-inArray-cancel"]'

    array_inputs = browser.find_elements_by_xpath(array_inputs_path)

    for array_input in array_inputs:
        eq(array_input.is_enabled(), False)

    browser.find_element_by_xpath(cancel_path).click()

    props.close()

    paraboloid = workspace_page.get_dataflow_figure("paraboloid_2", "top")
    props = paraboloid.properties_page()

    #array 1d editor - check that explicitly connected elements are disabled
    inputs = props.inputs
    inputs.rows[0].cells[1].click()

    array_inputs = browser.find_elements_by_xpath(array_inputs_path)

    for array_input in array_inputs:
        eq(array_input.is_enabled(), False)

    #browser.find_element_by_xpath(cancel_path).click()
    props.close()

    #array 2d editor - check that implicitly connected elements are disabled
    paraboloid = workspace_page.get_dataflow_figure("array_comp_1", "top_2")
    props = paraboloid.properties_page()

    inputs = props.inputs
    inputs.rows[0].cells[1].click()
    array_inputs_path = '//*[@id="inArray-editor"]/input'
    cancel_path = '//*[@id="array-edit-inArray-cancel"]'

    array_inputs = browser.find_elements_by_xpath(array_inputs_path)

    for index, array_input in enumerate(array_inputs):
        if (index % 3 == 2):
            eq(array_input.is_enabled(), True)
        else:
            eq(array_input.is_enabled(), False)

    browser.find_element_by_xpath(cancel_path).click()

    props.close()

    #array 2d editor - check that explicitly connected elements are disabled
    paraboloid = workspace_page.get_dataflow_figure("array_comp_2", "top_2")
    props = paraboloid.properties_page()

    inputs = props.inputs
    # Can't single click on an entry you are focused on, so focus on next line, then come back.
    inputs.rows[1].cells[1].click()
    inputs.rows[0].cells[1].click()

    array_inputs = browser.find_elements_by_xpath(array_inputs_path)

    for index, array_input in enumerate(array_inputs):
        if (index % 3 == 1):
            eq(array_input.is_enabled(), True)
        else:
            eq(array_input.is_enabled(), False)

    #browser.find_element_by_xpath(cancel_path).click()
    props.close()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_value_editors(browser):
    # Creates a file in the GUI.
    project_dict, workspace_page = startup(browser)

    # Import variable_editor.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/variable_editors.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('variable_editors.Topp', 'top')

    dummy_comp = workspace_page.get_dataflow_figure('p1', 'top')
    props = dummy_comp.properties_page()
    props.move(-100, -100)  # Ensure Project menu fully visible.
    inputs = props.inputs

    #edit dictionary - remove 'e', add 'phi', round down 'pi'
    #action_chain = ActionChains(browser)
    #action_chain.double_click(inputs.rows[0].cells[1]).perform()
    # Can't single click on an entry you are focused on, so focus on next line, then come back.
    inputs.rows[1].cells[1].click()
    inputs.rows[0].cells[1].click()

    pi_value_path = '//*[@id="d-editor"]/input[2]'
    pi_value = browser.find_element_by_xpath(pi_value_path)
    pi_value.clear()
    pi_value.send_keys("3.0")

    e_remove_btn = '//*[@id="e"]'
    browser.find_element_by_xpath(e_remove_btn).click()

    key_path = '//*[@id="d-dialog"]/input[1]'
    value_path = '//*[@id="d-dialog"]/input[2]'
    add_new_path = '//*[@id="d-dialog"]/button'
    submit_path = '//*[@id="dict-edit-d-submit"]'

    browser.find_element_by_xpath(key_path).send_keys("phi")
    browser.find_element_by_xpath(value_path).send_keys("1.61")
    browser.find_element_by_xpath(add_new_path).click()
    browser.find_element_by_xpath(submit_path).click()
    time.sleep(0.5)
    inputs = props.inputs

    # string editor - set to "abcd"
    inputs.rows[9].cells[1].click()
    inputs[9][1] = "abcd"
    time.sleep(1)

    #enum editor - set to 3
    inputs = props.inputs
    inputs.rows[1].cells[1].click()
    selection_path = '//*[@id="editor-enum-e"]/option[4]'
    browser.find_element_by_xpath(selection_path).click()
    time.sleep(0.5)

    # float editor - set to 2.71
    inputs = props.inputs
    inputs.rows[2].cells[1].click()
    inputs[2][1] = '2.71'
    time.sleep(0.5)

    #bool editor - set to true
    inputs = props.inputs
    inputs.rows[10].cells[1].click()
    selection_path = '//*[@id="bool-editor-force_fd"]/option[1]'
    browser.find_element_by_xpath(selection_path).click()
    time.sleep(0.5)

    #array 1d editor - add element, set to 4
    inputs = props.inputs
    inputs.rows[3].cells[1].click()
    add_path = '//*[@id="array-edit-add-X"]'
    browser.find_element_by_xpath(add_path).click()
    new_cell_path = '//*[@id="array-editor-dialog-X"]/div/input[5]'
    new_cell = browser.find_element_by_xpath(new_cell_path)
    new_cell.clear()
    new_cell.send_keys("4.")
    submit_path = '//*[@id="array-edit-X-submit"]'
    browser.find_element_by_xpath(submit_path).click()
    time.sleep(0.5)

    #fixed array 1d editor - verify no add
    inputs = props.inputs
    inputs.rows[4].cells[1].click()
    add_path = '//*[@id="array-edit-add-Xfixed"]'
    browser.implicitly_wait(1)  # Not expecting to find anything.
    try:
        browser.find_element_by_xpath(add_path)
    except NoSuchElementException:
        pass
    else:
        raise TestCase.failureException('Expecting NoSuchElementException'
                                        ' for add-Xfixed')
    finally:
        browser.implicitly_wait(TMO)
    cancel_path = '//*[@id="array-edit-Xfixed-cancel"]'
    browser.find_element_by_xpath(cancel_path).click()
    time.sleep(0.5)

    # array 2d editor - set to [[1, 4],[9, 16]]
    inputs = props.inputs
    inputs.rows[5].cells[1].click()
    for i in range(1, 5):
        cell_path = '//*[@id="array-editor-dialog-Y"]/div/input[' + str(i) + ']'
        cell_input = browser.find_element_by_xpath(cell_path)
        cell_input.clear()
        cell_input.send_keys(str(i**2))
    submit_path = '//*[@id="array-edit-Y-submit"]'
    browser.find_element_by_xpath(submit_path).click()

    # array 2d editor - special case for a bug - set to [[5],[7]]
    inputs = props.inputs
    inputs.rows[6].cells[1].click()
    cell_path = '//*[@id="array-editor-dialog-Y2"]/div/input[2]'
    cell_input = browser.find_element_by_xpath(cell_path)
    cell_input.clear()
    cell_input.send_keys(str(7))
    submit_path = '//*[@id="array-edit-Y2-submit"]'
    browser.find_element_by_xpath(submit_path).click()

    # array 2d editor - special case for a bug - set to [[99]]
    inputs = props.inputs
    inputs.rows[7].cells[1].click()
    cell_path = '//*[@id="array-editor-dialog-Y3"]/div/input[1]'
    cell_input = browser.find_element_by_xpath(cell_path)
    cell_input.clear()
    cell_input.send_keys(str(99))
    submit_path = '//*[@id="array-edit-Y3-submit"]'
    browser.find_element_by_xpath(submit_path).click()

    #list editor - set to [1, 2, 3, 4, 5]
    inputs = props.inputs
    eq(inputs[8][1].startswith("["), True)
    eq(inputs[8][1].endswith("]"), True)
    values = [int(value.strip()) for value in inputs[8][1].strip("[]").split(",")]
    eq(len(values), 4)
    eq(values, [1, 2, 3, 4])

    values.append(5)
    values = str([value for value in values])
    inputs[8][1] = values

    props.close()

    #check that all values were set correctly by the editors
    commands = ["top.p1.d['pi']",
                "top.p1.d['phi']",
                "top.p1.e",
                "top.p1.x",
                "top.p1.X",
                "top.p1.directory",
                "top.p1.Z"]
    values = ["3.0",
              "1.61",
              "3",
              "2.71",
              "[ 0.  1.  2.  3.  4.]",
              "abcd",
              "[1, 2, 3, 4, 5]"]

    for cmd_str, check_val in zip(commands, values):
        workspace_page.do_command(cmd_str)
        output = workspace_page.history.split("\n")[-1]
        eq(output, check_val)

    #separate check for 2d arrays
    workspace_page.do_command("top.p1.Y")
    output = workspace_page.history.split("\n")
    eq(output[-2], "[[ 1  4]")
    eq(output[-1], " [ 9 16]]")

    #separate check for 2d arrays
    workspace_page.do_command("top.p1.Y2")
    output = workspace_page.history.split("\n")
    eq(output[-2], "[[5]")
    eq(output[-1], " [7]]")

    #separate check for 2d arrays
    workspace_page.do_command("top.p1.Y3")
    output = workspace_page.history.split("\n")
    eq(output[-1], "[[99]]")

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_Avartrees(browser):
    project_dict, workspace_page = startup(browser)

    # Import variable_editor.py
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/model_vartree.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('model_vartree.Topp', "top")

    comp = workspace_page.get_dataflow_figure('p1', "top")
    editor = comp.editor_page()
    editor.move(-100, 0)
    inputs = editor.get_inputs()
    expected = [
        ['', ' cont_in', '',  '', ''],
        ['', 'directory', '', '',
            'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided but some are missing']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # Expand first vartree
    inputs.rows[0].cells[1].click()
    inputs = editor.get_inputs()
    expected = [
        ['', ' cont_in', '',  '', ''],
        ['', 'v1', '1',  '', 'vv1'],
        ['', 'v2', '2',  '', 'vv2'],
        ['', ' vt2', '',  '', ''],
        ['', 'directory', '', '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided but some are missing']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # While expanded, verify that 'v1' is editable.
    inputs.rows[1].cells[2].click()
    inputs = editor.get_inputs()
    inputs[1][2] = "42"
    expected[1][2] = "42"

    time.sleep(0.5)
    inputs = editor.get_inputs()
#FIXME sometimes row 2 gets a value of '' because slickgrid is editing it.
#    for i, row in enumerate(inputs.value):
#        eq(row, expected[i])
    eq(inputs.value[1], expected[1])

    # While expanded, verify that cell that became the 2nd vartree is now
    # uneditable
    inputs.rows[3].cells[1].click()
    inputs = editor.get_inputs()
    try:
        inputs[3][2] = "abcd"
    except IndexError:
        pass
    else:
        raise TestCase.failureException(
            'Exception expected: VarTree value should not be settable on inputs.')

    # Contract first vartree
    inputs.rows[0].cells[1].click()
    inputs = editor.get_inputs()
    expected = [
        ['', ' cont_in', '',  '', ''],
        ['', 'directory', '', '',
            'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided but some are missing']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    editor.close()

    # Now, do it all again on the Properties Pane
    workspace_page('properties_tab').click()
    obj = workspace_page.get_dataflow_figure('p1', 'top')
    chain = ActionChains(browser)
    chain.click(obj.root)
    chain.perform()
    inputs = workspace_page.props_inputs
    expected = [
        [' cont_in',      ''],
        ['directory',     ''],
        ['force_fd', 'False'],
        ['missing_deriv_policy', 'error']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # Expand first vartree
    inputs.rows[0].cells[0].click()
    inputs = workspace_page.props_inputs
    expected = [
        [' cont_in',      ''],
        ['v1', '42'],
        ['v2', '2'],
        [' vt2', ''],
        ['directory',     ''],
        ['force_fd', 'False'],
        ['missing_deriv_policy', 'error']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # While expanded, verify that 'v1' is editable.
    inputs.rows[1].cells[1].click()
    inputs = workspace_page.props_inputs
    inputs[1][1] = "43"
    expected[1][1] = "43"

    time.sleep(1)
    inputs = workspace_page.props_inputs
#FIXME sometimes row 2 gets a value of '' because slickgrid is editing it.
#    for i, row in enumerate(inputs.value):
#        eq(row, expected[i])
    eq(inputs.value[1], expected[1])

    # Contract first vartree
    inputs.rows[0].cells[0].click()
    inputs = workspace_page.props_inputs
    expected = [
        [' cont_in',      ''],
        ['directory',     ''],
        ['force_fd', 'False'],
        ['missing_deriv_policy', 'error']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # Clean up.
    closeout(project_dict, workspace_page)

def _test_basic(browser):
    project_dict, workspace_page = startup(browser)

    filename = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/rosen_suzuki.py')
    workspace_page.add_file(filename)

    # Add a NestedSimulation.
    workspace_page.add_library_item_to_dataflow('rosen_suzuki.NestedSimulation',
                                                'nested', offset=(300, 300))
    # Verify full workflow shown.
    workspace_page('workflow_tab').click()
    eq(len(workspace_page.get_workflow_figures()), 2)
    eq(len(workspace_page.get_workflow_component_figures()), 5)

    # Verify flow layout is horizontal and can be switched to vertical
    sim = workspace_page.get_workflow_figure('sim.driver')
    assert sim.horizontal
    sim.flip()
    assert not sim.horizontal

    # Verify workflow can be collapsed and expanded
    sim.collapse()
    assert sim.collapsed
    sim.expand()
    assert sim.expanded

    # Verify that component state is represented properly
    driver = workspace_page.get_workflow_component_figure('sim.driver')
    driver.run()
    time.sleep(2.0)
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    # Verify workflow can be cleared
    nested = workspace_page.get_workflow_figure('nested.driver')
    nested.clear()
    eq(len(workspace_page.get_workflow_component_figures()), 1)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_evaluate(browser):
    project_dict, workspace_page = startup(browser)

    # create an assembly with an implicit component in it's workflow
    filename = pkg_resources.resource_filename('openmdao.main.test',
                                               'test_implicit_component.py')
    workspace_page.add_file(filename)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')

    workspace_page.add_library_item_to_dataflow('test_implicit_component.MyComp_Deriv',
                                                'comp', prefix='top')

    workspace_page.add_object_to_workflow('top.comp', 'top')

    # Verify that the evaluate menu option has the expected effect
    (header, inputs, outputs) = workspace_page.get_properties('comp')
    eq(outputs.value, [
        ['y_out', '0'],
        ['derivative_exec_count', '0'],
        ['exec_count', '0'],
        ['itername', '']
    ])

    workspace_page('workflow_tab').click()

    comp = workspace_page.get_workflow_component_figure('comp')
    comp.evaluate()

    (header, inputs, outputs) = workspace_page.get_properties('comp')
    eq(outputs.value, [
        ['y_out', '2'],
        ['derivative_exec_count', '0'],
        ['exec_count', '0'],
        ['itername', '']
    ])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_update(browser):
    # Adding a parameter to a driver should update the driver's workflow.
    project_dict, workspace_page = startup(browser)

    # Create model with CONMIN and ExecComp.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.replace_driver('top', 'CONMINdriver')
    workspace_page.add_library_item_to_dataflow(
        'openmdao.test.execcomp.ExecComp', 'exe', args=["('z = x * y',)"])

    # Add parameter to CONMIN.
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'exe.x'
    dialog.low = '-1'
    dialog.high = '1'
    dialog('ok').click()
    editor.close()

    # Verify workflow contains ExecComp.
    workspace_page('workflow_tab').click()
    eq(len(workspace_page.get_workflow_figures()), 1)
    eq(len(workspace_page.get_workflow_component_figures()), 2)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_duplicates(browser):
    # Duplicate unconnected components are legal in a workflow.
    project_dict, workspace_page = startup(browser)

    # Create model with multiple ExecComps.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow(
        'openmdao.test.execcomp.ExecComp', 'exe', args=["('z = x * y',)"])
    workspace_page.expand_object('top')
    workspace_page.add_object_to_workflow('top.exe', 'top')
    workspace_page.add_object_to_workflow('top.exe', 'top')
    workspace_page('workflow_tab').click()
    eq(len(workspace_page.get_workflow_figures()), 1)
    eq(len(workspace_page.get_workflow_component_figures()), 3)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_parameter_auto(browser):
    # Test auto-filling the min and max for a parameter.
    project_dict, workspace_page = startup(browser)

    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/connect.py')
    workspace_page.add_file(file_path)

    workspace_page.add_library_item_to_dataflow('connect.Conn_Assy',
                                                'top')
    # Add parameter to driver.
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'comp.x'
    dialog('ok').click()

    parameters = editor.get_parameters()
    expected = [['', 'comp.x', '0', '299', '1', '0', '', 'comp.x']]
    eq(len(parameters.value), len(expected))
    for i, row in enumerate(parameters.value):
        eq(row, expected[i])

    editor.close()

    closeout(project_dict, workspace_page)


def _test_array_parameter(browser):
    # Test adding an array parameter.
    project_dict, workspace_page = startup(browser)

    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/array_parameters.py')
    workspace_page.add_file(file_path)
    workspace_page.add_library_item_to_dataflow('array_parameters.ArrayParameters',
                                                'top')
    # Add parameter to driver.
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'paraboloid.x'
    dialog.low = '-50'
    dialog.high = '[40, 50]'
    dialog.scaler = '[[1., 1]]'
    dialog('ok').click()

    parameters = editor.get_parameters()
    expected = [['', 'paraboloid.x', '-50', '40,50', '1,1', '0', '', 'paraboloid.x']]
    eq(len(parameters.value), len(expected))
    for i, row in enumerate(parameters.value):
        eq(row, expected[i])

    editor.close()
    time.sleep(1)

    # Run optimization.
    top = workspace_page.get_dataflow_figure('top')
    top.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')

    # Check results.
    workspace_page.do_command("top.paraboloid.x[0][0]")
    x00 = workspace_page.history.split("\n")[-1]
    workspace_page.do_command("top.paraboloid.x[0][1]")
    x01 = workspace_page.history.split("\n")[-1]

    if abs(float(x00) - 6.6667) > 0.01:
        raise TestCase.failureException(
            "Parameter x[0][0] did not reach correct value, but instead is %s"
            % x00)

    if abs(float(x01) - -7.3333) > 0.01:
        raise TestCase.failureException(
            "Parameter x[0][1] did not reach correct value, but instead is %s"
            % x01)

    closeout(project_dict, workspace_page)

def _test_slots_sorted_by_name(browser):
    project_dict, workspace_page = startup(browser)

    #drop 'metamodel' onto the grid
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    args = ["('ratio1', 'ratio2')", "('torque_ratio', 'RPM')"]
    workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.components.metamodel.MetaModel', 'mm', args=args)
    #open the 'edit' dialog on metamodel
    metamodel = workspace_page.get_dataflow_figure('mm', 'top')
    mm_editor = metamodel.editor_page()

    # see if the slot names are sorted
    slot_name_elements = mm_editor.root.find_elements_by_css_selector('text#name')
    slot_names = [s.text for s in slot_name_elements]
    eq(slot_names, sorted(slot_names))

    closeout(project_dict, workspace_page)


def _test_console(browser):
    # Check basic console functionality.
    project_dict, workspace_page = startup(browser)

    workspace_page.do_command("print 'blah'")
    expected = ">>> print 'blah'\nblah"
    eq(workspace_page.history, expected)

    # Check that browser title contains project name.
    title = browser.title
    expected = 'OpenMDAO: ' + project_dict['name'] + ' - '
    eq(title[:len(expected)], expected)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_console_history(browser):
    # Check up and down arrow navigation through the command history
    project_dict, workspace_page = startup(browser)

    command_elem = browser.find_element(By.ID, "cmdline")

    # Fill up the command history
    workspace_page.do_command("import sys")
    workspace_page.do_command("import os")
    workspace_page.do_command("import time")

    # Try out the up and down arrows
    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import time")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import os")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import sys")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import sys")

    command_elem.send_keys(Keys.ARROW_DOWN)
    eq(workspace_page.command, "import os")

    command_elem.send_keys(Keys.ARROW_DOWN)
    eq(workspace_page.command, "import time")

    command_elem.send_keys(Keys.ARROW_DOWN)
    eq(workspace_page.command, "import time")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import os")

    workspace_page.do_command("import traceback")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import traceback")

    command_elem.send_keys(Keys.ARROW_UP)
    eq(workspace_page.command, "import time")

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_palette_update(browser):
    # Import some files and add components from them.
    project_dict, workspace_page = startup(browser)

    # View dataflow.
    workspace_page('dataflow_tab').click()

    # Get file paths
    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')
    file2_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'optimization_unconstrained.py')

    # add first file from workspace
    workspace_page.add_file(file1_path)

    # Open code editor.and add second file from there
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()
    time.sleep(0.5)
    editor_page.add_file(file2_path)

    # Check code editor to make sure the files were added.
    time.sleep(0.5)
    file_names = editor_page.get_files()
    expected_file_names = ['optimization_unconstrained.py', 'paraboloid.py']
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Check workspace to make sure the files also show up there.
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    expected_file_names = ['optimization_unconstrained.py', 'paraboloid.py']
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))

    # Make sure there are only two dataflow figures (top & driver)
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    eq(len(workspace_page.get_dataflow_figures()), 2)

    # Drag element into workspace.
    paraboloid_name = 'parab'
    workspace_page.add_library_item_to_dataflow('paraboloid.Paraboloid',
                                                paraboloid_name)

    # Now there should be three.
    eq(len(workspace_page.get_dataflow_figures()), 3)

    # Make sure the item added is there with the name we gave it.
    component_names = workspace_page.get_dataflow_component_names()
    if paraboloid_name not in component_names:
        raise TestCase.failureException(
            "Expected component name, '%s', to be in list of existing"
            " component names, '%s'" % (paraboloid_name, component_names))

    workspace_page.commit_project('added paraboloid')
    projects_page = workspace_page.close_workspace()

    # Now try to re-open that project to see if items are still there.
    #project_info_page = projects_page.edit_project(project_dict['name'])
    workspace_page = projects_page.open_project(project_dict['name'])

    # Check to see that the added files are still there.
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()
    file_names = editor_page.get_files()
    if sorted(file_names) != sorted(expected_file_names):
        raise TestCase.failureException(
            "Expected file names, '%s', should match existing file names, '%s'"
            % (expected_file_names, file_names))
    browser.close()
    browser.switch_to_window(workspace_window)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_loading_docs(browser):
    project_dict, workspace_page = startup(browser)

    # Check that the docs are viewable
    workspace_page('help_menu').click()
    time.sleep(0.5)
    eq(workspace_page('doc_button').get_attribute('id'), 'help-doc')

    workspace_window = browser.current_window_handle
    current_windows = set(browser.window_handles)
    workspace_page('doc_button').click()
    new_windows = set(browser.window_handles) - current_windows
    docs_window = list(new_windows)[0]
    browser.switch_to_window(docs_window)
    time.sleep(0.5)
    eq("OpenMDAO User Guide" in browser.title, True)
    eq("OpenMDAO Documentation" in browser.title, True)

    browser.close()
    browser.switch_to_window(workspace_window)
    workspace_page.show_library()
    browser.switch_to_window(workspace_page.view_library_item_docs("openmdao.main.assembly.Assembly"))

    # Just check to see if a Traceback 404 message was sent.
    try:
        browser.find_element((By.XPATH, "/html/head/body/pre[1]"))
        assert False
    except:
        pass
    browser.close()
    browser.switch_to_window(workspace_window)
    closeout(project_dict, workspace_page)


def _test_menu(browser):
    project_dict, workspace_page = startup(browser)

    # Check enable/disable of commit/revert.
    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), 'omg-disabled')
    eq(workspace_page('revert_button').get_attribute('class'), 'omg-disabled')
    workspace_page('project_menu').click()

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.replace_driver('top', 'SLSQPdriver')

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), '')
    eq(workspace_page('revert_button').get_attribute('class'), '')
    workspace_page('project_menu').click()

    workspace_page.commit_project()

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), 'omg-disabled')
    eq(workspace_page('revert_button').get_attribute('class'), 'omg-disabled')
    workspace_page('project_menu').click()

    #FIXME: These need to verify that the request has been performed.
    # View menu.
    for item in ('console', 'library', 'objects', 'files',
                 'properties', 'workflow', 'dataflow', 'refresh'):
        workspace_page('view_menu').click()
        workspace_page('%s_button' % item).click()
        time.sleep(0.5)  # Just so we can see it.

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_file_commit(browser):
    project_dict, workspace_page = startup(browser)

    # Check that adding a file enables commit.
    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), 'omg-disabled')
    eq(workspace_page('revert_button').get_attribute('class'), 'omg-disabled')
    workspace_page('project_menu').click()

    stl_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                               'files/box.stl')
    workspace_page.add_file(stl_path)
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if file_names != ['box.stl']:
        raise TestCase.failureException('Expected box.stl, got %s' % file_names)

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), '')
    eq(workspace_page('revert_button').get_attribute('class'), '')  # Enabled?
    workspace_page('project_menu').click()

    # Commit and check that commit is disabled but revert is enabled.
    workspace_page.commit_project()

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), 'omg-disabled')
    eq(workspace_page('revert_button').get_attribute('class'), 'omg-disabled')
    workspace_page('project_menu').click()                     # Disabled?

    # Remove file and check commit & revert enabled.
    workspace_page.delete_file('box.stl')
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if file_names:
        raise TestCase.failureException('Unexpected files %s' % file_names)

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), '')
    eq(workspace_page('revert_button').get_attribute('class'), '')
    workspace_page('project_menu').click()

    # revert back to version with file.
    workspace_page = workspace_page.revert_project()
    time.sleep(0.5)
    file_names = workspace_page.get_files()
    if file_names != ['box.stl']:
        raise TestCase.failureException('Expected box.stl, got %s' % file_names)

    workspace_page('project_menu').click()
    time.sleep(0.5)
    eq(workspace_page('commit_button').get_attribute('class'), 'omg-disabled')
    eq(workspace_page('revert_button').get_attribute('class'), 'omg-disabled')
    workspace_page('project_menu').click()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_macro(browser):
    project_dict, workspace_page = startup(browser)

    # Open code editor.
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()

    # Create a file (code editor automatically indents).
    editor_page.new_file('foo.py', """
from openmdao.main.api import Component
from openmdao.main.datatypes.api import Float

class Foo(Component):

a = Float(0.0, iotype='in')
b = Float(0.0, iotype='out')
""")
    # Back to workspace.
    browser.close()
    browser.switch_to_window(workspace_window)

    # Add some Foo instances.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    time.sleep(2)  # Wait for it to get registered.
    workspace_page.set_library_filter('In Project')
    workspace_page.add_library_item_to_dataflow('foo.Foo', 'comp1')
    workspace_page.add_library_item_to_dataflow('foo.Foo', 'comp2')

    comp1 = workspace_page.get_dataflow_figure('comp1', 'top')
    comp2 = workspace_page.get_dataflow_figure('comp2', 'top')
    conn_page = workspace_page.connect(comp1, comp2)
    conn_page.connect_vars('comp1.b', 'comp2.a')
    conn_page.close()

    workspace_page.commit_project('added some Foos')

    if broken_chrome():
        raise SkipTest('Test broken for chrome/selenium combination')
    editor_page = workspace_page.open_editor()
    editor_page.edit_file('foo.py', dclick=False)
    editor_page.add_text_to_file('#just a comment\n')

    # forces a save and reload of project
    editor_page.save_document(overwrite=True, check=False)
    browser.switch_to_window(workspace_window)
    port = workspace_page.port
    workspace_page = WorkspacePage.verify(browser, port)

    workspace_page.show_dataflow('top')
    time.sleep(0.5)
    eq(sorted(workspace_page.get_dataflow_component_names()),
       ['comp1', 'comp2', 'driver', 'top'])

    # Check if running a component is recorded (it shouldn't be).
    top = workspace_page.get_dataflow_figure('top')
    top.run()
    message = NotifierPage.wait(workspace_page)
    eq(message, 'Run complete: success')
    history = workspace_page.history.split('\n')
    eq(history[-2], 'Executing...')
    eq(history[-1], 'Execution complete.')

    workspace_page.toggle_files('foo.py')
    workspace_page.expand_folder('_macros')
    editor = workspace_page.edit_file('_macros/default')
    contents = editor.get_code()
    browser.close()
    browser.switch_to_window(workspace_window)
    for line in contents.split('\n'):
        if 'run' in line:
            raise AssertionError(line)

    # Check if command errors are recorded (they shouldn't be).
    workspace_page.do_command('print xyzzy', ack=False)
    NotifierPage.wait(workspace_page, base_id='command')
    expected = "NameError: name 'xyzzy' is not defined"
    assert workspace_page.history.endswith(expected)

    editor = workspace_page.edit_file('_macros/default')
    contents = editor.get_code()
    browser.close()
    browser.switch_to_window(workspace_window)
    for line in contents.split('\n'):
        if 'xyzzy' in line:
            raise AssertionError(line)

    # Clean up.
    closeout(project_dict, workspace_page)

def _test_properties(browser):
    # Checks right-hand side properties display.
    project_dict, workspace_page = startup(browser)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')

    (header, inputs, outputs) = workspace_page.get_properties('top')
    eq(header, 'Driver: top.driver')
    eq(inputs.value, [
        ['directory',         ''],
        ['force_fd',          'False'],
        [' gradient_options', ''],  # vartree, has leading space after the [+]
    ])
    eq(outputs.value, [
        ['derivative_exec_count', '0'],
        ['exec_count',            '0'],
        ['itername',              '']
    ])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_implicit_component(browser):
    project_dict, workspace_page = startup(browser)

    # create an assembly with an implicit component in it's workflow
    filename = pkg_resources.resource_filename('openmdao.main.test',
                                               'test_implicit_component.py')
    workspace_page.add_file(filename)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')

    workspace_page.add_library_item_to_dataflow('test_implicit_component.MyComp_Deriv',
                                                'comp', prefix='top')

    workspace_page.add_object_to_workflow('top.comp', 'top')

    # Verify that the evaluate menu option has the expected effect
    comp = workspace_page.get_dataflow_figure('comp', 'top')
    comp_editor = comp.editor_page(base_type='ImplicitComponent')

    states = comp_editor.get_states()
    eq(states.value, [
        ['', 'x', '0', '', ''],
        ['', 'y', '0', '', ''],
        ['', 'z', '0', '', ''],
    ])

    residuals = comp_editor.get_residuals()
    eq(residuals.value, [
        ['', 'res', '[0.0, 0.0, 0.0]', '', '']
    ])

    comp_editor.set_state('x', '1')
    comp_editor.set_state('y', '2')
    comp_editor.set_state('z', '3')

    comp.evaluate()

    states = comp_editor.get_states()
    eq(states.value, [
        ['', 'x', '1', '', ''],
        ['', 'y', '2', '', ''],
        ['', 'z', '3', '', ''],
    ])

    residuals = comp_editor.get_residuals()
    eq(residuals.value, [
        ['', 'res', '[7.0, 12.0, -3.0]', '', '']
    ])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_component_tree(browser):
    project_dict, workspace_page = startup(browser)

    workspace_page.select_objects_view('Components')

    # Add maxmin.py to project
    file_path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                'files/maxmin.py')
    workspace_page.add_file(file_path)

    # Add MaxMin to 'top'.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow('maxmin.MaxMin', 'maxmin')

    # Maximize 'top' and 'top.maxmin'
    visible = workspace_page.get_objects_attribute('path', True)
    eq(visible, ['top'])
    workspace_page.expand_object('top')
    time.sleep(0.5)
    visible = workspace_page.get_objects_attribute('path', True)
    eq(visible, ['top', 'top.driver', 'top.maxmin'])
    workspace_page.expand_object('top.maxmin')
    time.sleep(0.5)
    visible = workspace_page.get_objects_attribute('path', True)
    eq(visible, ['top', 'top.driver', 'top.maxmin',
                 'top.maxmin.driver', 'top.maxmin.sub'])

    workspace_page.add_library_item_to_dataflow('maxmin.MaxMin', 'maxmin2')
    visible = workspace_page.get_objects_attribute('path', True)
    eq(visible, ['top', 'top.driver', 'top.maxmin',
                 'top.maxmin.driver', 'top.maxmin.sub', 'top.maxmin2'])

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_editable_inputs(browser):
    raise SkipTest

    def test_color(actual, expected, alpha=False):
        if alpha:
            eq(actual, expected)
        else:
            eq(actual[0:3], expected[0:3])

    def test_inputs(inputs):
        for i, row in enumerate(inputs):
            connected_to_cell = row.cells[len(row.cells) - 2]
            implicit_cell = row.cells[len(row.cells) - 1]
            name_cell = row.cells[0]
            value_cell = row.cells[2]

            if connected_to_cell.value:
                test_color(name_cell.color, [255, 255, 255, 1])
                test_color(value_cell.color, [255, 255, 255, 1])
                test_color(value_cell.background_color, [0, 0, 0, 1])
            elif implicit_cell.value:
                test_color(name_cell.color, [100, 180, 255, 1])
                test_color(value_cell.color, [100, 180, 255, 1])
                test_color(value_cell.background_color, [255, 255, 255, 1])
            else:
                test_color(name_cell.color, [255, 255, 255, 1])
                test_color(value_cell.color, [0, 0, 0, 1])
                test_color(value_cell.background_color, [255, 255, 255, 1])

    def test_outputs(outputs):
        for i, row in enumerate(outputs):
            implicit_cell = row.cells[len(row.cells) - 1]
            name_cell = row.cells[0]
            value_cell = row.cells[2]

            if implicit_cell.value:
                test_color(name_cell.color, [100, 180, 255, 1])
                test_color(value_cell.color, [100, 180, 255, 1])
            else:
                test_color(name_cell.color, [255, 255, 255, 1])
                test_color(value_cell.color, [255, 255, 255, 1])

            test_color(value_cell.background_color, [0, 0, 0, 1])

    project_dict, workspace_page = startup(browser)

    # Import vehicle_singlesim
    file_path_one = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                                    'files/basic_model.py')
    file_path_two = pkg_resources.resource_filename('openmdao.examples.enginedesign',
                                                    'vehicle_singlesim.py')
    workspace_page.add_file(file_path_one)
    workspace_page.add_file(file_path_two)

    assembly_name = "sim"
    workspace_page.add_library_item_to_dataflow('basic_model.Basic_Model',
                                                assembly_name)
    paraboloid = workspace_page.get_dataflow_figure('paraboloid', assembly_name)

    #Test highlighting for implicit connections
    component_editor = paraboloid.editor_page()
    test_inputs(component_editor.get_inputs())
    test_outputs(component_editor.get_outputs())

    component_editor.close()

    #Remove sim from the dataflow
    assembly = workspace_page.get_dataflow_figure(assembly_name)
    assembly.remove()

    #Add VehicleSim to the dataflow
    workspace_page.add_library_item_to_dataflow('vehicle_singlesim.VehicleSim',
                                                assembly_name)

    # Get component editor for transmission.
    workspace_page.expand_object(assembly_name)
    workspace_page.show_dataflow(assembly_name + ".vehicle")
    transmission = workspace_page.get_dataflow_figure('transmission',
                                                      assembly_name + '.vehicle')

    #Test highlighting for explicit connections
    component_editor = transmission.editor_page()
    test_inputs(component_editor.get_inputs())
    test_outputs(component_editor.get_outputs())

    component_editor.close()

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_console_errors(browser):
    project_dict, workspace_page = startup(browser)

    # Set input to illegal value.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    top = workspace_page.get_dataflow_figure('top', '')
    editor = top.editor_page(double_click=False, base_type='Assembly')
    editor.move(-100, -40)  # Make viewable on small screen.
    inputs = editor.get_inputs()
    inputs.rows[1].cells[2].click()
    inputs[1][2] = '42'  # 'excludes'
    expected = "TraitError: The 'excludes' trait of an "     \
               "Assembly instance must be a list of items "  \
               "which are a legal value, but a value of 42 " \
               "<type 'int'> was specified."
    time.sleep(0.5)
    assert workspace_page.history.endswith(expected)
    editor.close()

    # Attempt to save file with syntax error.
    workspace_window = browser.current_window_handle
    editor_page = workspace_page.open_editor()
    editor_page.new_file('bug.py', """
from openmdao.main.api import Component
class Bug(Component):
def execute(self)
    pass
""", check=False)

    # We expect 2 notifiers: save successful and file error.
    # These will likely overlap in a manner that 'Ok' is found but
    # later is hidden by the second notifier.
    try:
        message = NotifierPage.wait(editor_page, base_id='file-error')
    except WebDriverException as exc:
        err = str(exc)
        if 'Element is not clickable' in err:
            NotifierPage.wait(editor_page)
            message = NotifierPage.wait(editor_page)
    else:
        NotifierPage.wait(editor_page)
    eq(message, 'Error in file bug.py: invalid syntax (bug.py, line 6)')

    browser.close()
    browser.switch_to_window(workspace_window)

    # Load file with instantiation error.
    workspace_window = browser.current_window_handle
    if broken_chrome():
        raise SkipTest('Test broken for chrome/selenium combination')
    editor_page = workspace_page.open_editor()
    editor_page.new_file('bug2.py', """
from openmdao.main.api import Component
class Bug2(Component):
def __init__(self):
raise RuntimeError("__init__ failed")
""")
    browser.close()
    browser.switch_to_window(workspace_window)

    workspace_page.add_library_item_to_dataflow('bug2.Bug2', 'bug', check=False)
    expected = "NameError: unable to create object of type 'bug2.Bug2': __init__ failed"
    assert workspace_page.history.endswith(expected)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_driver_config(browser):
    project_dict, workspace_page = startup(browser)

    # Add MetaModel so we can test events.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    args = ["('x', )", "('y', )"]
    workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.components.metamodel.MetaModel', 'mm', args=args)

    # Replace default driver with CONMIN and edit.
    workspace_page.replace_driver('top', 'CONMINdriver')
    driver = workspace_page.get_dataflow_figure('driver', 'top')
    editor = driver.editor_page(base_type='Driver')
    editor.move(-100, -40)  # Make viewable on small screen.

    # Add a (nonsense) named parameter.
    editor('parameters_tab').click()
    dialog = editor.new_parameter()
    dialog.target = 'mm.force_fd'
    dialog.low = '0'
    dialog.high = '1'
    dialog.name = 'nonsense'
    dialog('ok').click()
    parameters = editor.get_parameters()
    expected = [['', 'mm.force_fd', '0', '1', '1', '0', '', 'nonsense']]
    eq(len(parameters.value), len(expected))
    for i, row in enumerate(parameters.value):
        eq(row, expected[i])

    # Delete the parameter
    delbutton = editor('parameters').find_elements_by_css_selector('.ui-icon-trash')
    delbutton[0].click()
    parameters = editor.get_parameters()
    expected = []
    browser.implicitly_wait(1)  # Not expecting to find anything.
    try:
        for i, row in enumerate(parameters.value):
            eq(row, expected[i])
    finally:
        browser.implicitly_wait(TMO)

    # Add a (nonsense) named objective.
    editor('objectives_tab').click()
    dialog = editor.new_objective()
    dialog.expr = 'mm.force_fd'
    dialog.name = 'nonsense'
    dialog('ok').click()
    objectives = editor.get_objectives()
    expected = [['', 'mm.force_fd', 'nonsense']]
    eq(len(objectives.value), len(expected))
    for i, row in enumerate(objectives.value):
        eq(row, expected[i])

    # Delete the objective
    delbutton = editor('objectives').find_elements_by_css_selector('.ui-icon-trash')
    delbutton[0].click()
    objectives = editor.get_objectives()
    expected = []
    browser.implicitly_wait(1)  # Not expecting to find anything.
    try:
        for i, row in enumerate(objectives.value):
            eq(row, expected[i])
    finally:
        browser.implicitly_wait(TMO)

    # Add a (nonsense) named constraint.
    editor('constraints_tab').click()
    dialog = editor.new_constraint()
    dialog.expr = 'mm.force_fd > 0'
    dialog.name = 'nonsense'
    dialog('ok').click()
    constraints = editor.get_constraints()
    expected = [['', 'mm.force_fd > 0', 'nonsense']]
    eq(len(constraints.value), len(expected))
    for i, row in enumerate(constraints.value):
        eq(row, expected[i])

    # Delete the constraint
    delbutton = editor('constraints').find_elements_by_css_selector('.ui-icon-trash')
    delbutton[0].click()
    constraints = editor.get_constraints()
    expected = []
    browser.implicitly_wait(1)  # Not expecting to find anything.
    try:
        for i, row in enumerate(constraints.value):
            eq(row, expected[i])
    finally:
        browser.implicitly_wait(TMO)

    # Clean up.
    editor.close()
    closeout(project_dict, workspace_page)


def _test_remove(browser):
    project_dict, workspace_page = startup(browser)

    # Show assembly information.
    top = workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.select_object('top')
    workspace_page.show_dataflow('top')
    workspace_page.hide_left()

    # open various views on the top assembly
    top = workspace_page.get_dataflow_figure('top', '')
    editor = top.editor_page(double_click=False)
    editor.move(100, 200)
    connections = top.connections_page()
    properties = top.properties_page()

    eq(editor.is_visible, True)
    eq(connections.is_visible, True)
    eq(properties.is_visible, True)

    # Remove component.
    top.remove()

    # make sure all the views on the top assembly go away
    time.sleep(1)
    eq(editor.is_visible, False)
    eq(connections.is_visible, False)
    eq(properties.is_visible, False)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_noslots(browser):
    project_dict, workspace_page = startup(browser)

    # Add ExternalCode to assembly.
    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    ext = workspace_page.add_library_item_to_dataflow(
        'openmdao.lib.components.external_code.ExternalCode', 'ext',
        prefix='top')

    # Display editor and check that no 'Slots' tab exists.
    editor = ext.editor_page(double_click=False)
    eq(editor('inputs_tab').is_visible, True)  # This waits.
    eq(editor('inputs_tab').is_present, True)  # These are quick tests.
    eq(editor('slots_tab').is_present, False)
    eq(editor('outputs_tab').is_present, True)

    # Clean up.
    editor.close()
    closeout(project_dict, workspace_page)


def _test_logviewer(browser):
    # Verify log viewer functionality.
    # Note that by default the logging level is set to WARNING.
    project_dict, workspace_page = startup(browser)
    viewer = workspace_page.show_log()
    viewer.move(0, -200)  # Sometimes get a lot of 'send event' messages...

    # Incremental display.
    workspace_page.do_command("import logging")
    workspace_page.do_command("logging.error('1 Hello World')")
    msgs = viewer.get_messages()
    while "Shouldn't have handled a send event" in msgs[-1]:
        msgs = msgs[:-1]
    eq(msgs[-1][-13:], '1 Hello World')

    # Exercise pausing the display. Since there's room on-screen,
    # the lack of scrollbar update isn't noticable.
    text = viewer.pause()
    eq(text, 'Pause')
    for i in range(2, 4):
        workspace_page.do_command("logging.error('%d Hello World')" % i)
    text = viewer.pause()  # Toggle-back.
    eq(text, 'Resume')

    # Clear display.
    viewer.clear()
    msgs = viewer.get_messages()
    eq(msgs, [''])

    # move log viewer away from file tree pane
    viewer.move(300, 0)

    # Exercise filtering.
    logger = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                             'files/logger.py')
    workspace_page.add_file(logger)
    msgs = viewer.get_messages()
    # Remove any spurious messages and drop timestamp.
    initial = [msg[16:] for msg in msgs
                        if "Shouldn't have handled a send event" not in msg and
                           'Connection reset by peer' not in msg]
    eq(initial,
       [u'W root: warning 1',
        u'E root: error 1',
        u'C root: critical 1',
        u'W root: warning 2',
        u'E root: error 2',
        u'C root: critical 2',
        u'W root: warning 3',
        u'E root: error 3',
        u'C root: critical 3'])

    # Turn off errors.
    dialog = viewer.filter()
    dialog('error_button').click()
    dialog('ok_button').click()

    msgs = viewer.get_messages()
    # Remove any spurious messages and drop timestamp.
    filtered = [msg[16:] for msg in msgs
                         if 'Connection reset by peer' not in msg]
    eq(filtered,
       [u'W root: warning 1',
        u'C root: critical 1',
        u'W root: warning 2',
        u'C root: critical 2',
        u'W root: warning 3',
        u'C root: critical 3'])

    # Pop-out to separate window.
    workspace_window = browser.current_window_handle
    viewer.popout()
    time.sleep(1)
    for handle in browser.window_handles:
        if handle != workspace_window:
            browser.switch_to_window(handle)
            browser.close()
            break
    browser.switch_to_window(workspace_window)

    # Verify that viewer was closed.
    try:
        viewer.get_messages()
    except StaleElementReferenceException:
        pass
    else:
        raise RuntimeError('Expected StaleElementReferenceException')

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_libsearch(browser):
    # Verify library search functionality.
    project_dict, workspace_page = startup(browser)

    # Get default objects.
    def_objects = workspace_page.get_object_types()
    def_searches = workspace_page.get_library_searches()

    # Get 'doe' search results.
    workspace_page.set_library_filter('doe')
    objects = workspace_page.get_object_types()
    eq(objects, [
        'CentralComposite',
        'CSVFile',
        'DOEdriver',
        'FullFactorial',
        'NeighborhoodDOEdriver',
        'OptLatinHypercube',
        'PlugNozzleGeometry',
        'Uniform'])
    doe_searches = workspace_page.get_library_searches()
    eq(doe_searches, def_searches + ['doe'])

    # Clear search, now back to default objects.
    workspace_page.clear_library_filter()
    objects = workspace_page.get_object_types()
    eq(objects, def_objects)

    # Get 'xyzzy' search results.
    workspace_page.set_library_filter('xyzzy')
    objects = workspace_page.get_object_types()
    eq(objects, ['No matching records found'])
    searches = workspace_page.get_library_searches()
    eq(searches, doe_searches)

    # Clean up.
    closeout(project_dict, workspace_page)


def _test_casefilters(browser):
    # Verify that CaseFilter objects are listed in the library.
    project_dict, workspace_page = startup(browser)

    for classname in ('ExprCaseFilter', 'IteratorCaseFilter',
                      'SequenceCaseFilter', 'SliceCaseFilter'):
        workspace_page.find_library_button(classname)

    closeout(project_dict, workspace_page)


def _test_sorting(browser):
    # Check that inputs and outputs are sorted alphanumerically.
    project_dict, workspace_page = startup(browser)

    path = pkg_resources.resource_filename('openmdao.gui.test.functional',
                                           'files/sorting_test.py')
    workspace_page.add_file(path)

    workspace_page.add_library_item_to_dataflow(
        'openmdao.main.assembly.Assembly', 'top')
    workspace_page.show_dataflow('top')
    workspace_page.add_library_item_to_dataflow(
        'sorting_test.SortingComp', 'comp')
    comp = workspace_page.get_dataflow_figure('comp', 'top')
    editor = comp.editor_page()

    # Check order of inputs.
    inputs = editor.get_inputs()
    expected = [
        ['', 'stress_i1', '0', '', ''],
        ['', 'stress_i2', '0', '', ''],
        ['', 'stress_i10', '0', '', ''],
        ['', 'directory',  '',  '',
         'If non-blank, the directory to execute in.'],
        ['', 'force_fd', 'False', '',
         'If True, always finite difference this component.'],
        ['', 'missing_deriv_policy', 'error', '',
         'Determines behavior when some analytical derivatives are provided'
         ' but some are missing']
    ]

    for i, row in enumerate(inputs.value):
        eq(row, expected[i])

    # Check order of outputs.
    outputs = editor.get_outputs()
    expected = [
        ['', 'stress_o1', '0', '', ''],
        ['', 'stress_o2', '0', '', ''],
        ['', 'stress_o10', '0', '', ''],
        ['', 'derivative_exec_count', '0', '',
         "Number of times this Component's derivative function has been executed."],
        ['', 'exec_count', '0', '',
         'Number of times this Component has been executed.'],
        ['', 'itername', '', '', 'Iteration coordinates.'],
    ]

    for i, row in enumerate(outputs.value):
        eq(row, expected[i])

    editor.close()
    closeout(project_dict, workspace_page)


def _test_standard_library(browser):
    project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()

    eq(objects, [
        'BraninProblem',
        'PolyScalableProblem',
        'SellarProblem',])

    closeout(project_dict, workspace_page)


if __name__ == '__main__':
    main()
