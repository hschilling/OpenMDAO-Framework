"""
Tests of overall workspace functions.
"""

import time

import pkg_resources

from nose import SkipTest
from nose.tools import eq_ as eq
from nose.tools import with_setup

from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, \
                                       WebDriverException
from util import main, setup_server, teardown_server, generate, \
                 startup, closeout, broken_chrome, TEST_CONFIG

from pageobjects.basepageobject import TMO
from pageobjects.util import NotifierPage
from pageobjects.workspace import WorkspacePage


@with_setup(setup_server(virtual_display=True), teardown_server)
def test_generator():
    #q = generate( __name__ )
    for _test, browser in generate(__name__):
        yield _test, browser


def _qqqtest_1(browser, project_dict, workspace_page):
    #project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')

    # workspace_page.set_library_filter('optproblems')
    # objects = workspace_page.get_object_types()
    
    # browser.execute_script('openmdao.project.clear();')

    # workspace_page.set_library_filter('optproblems')
    # objects = workspace_page.get_object_types()
    
    # browser.execute_script('openmdao.project.clear();')


    #closeout(project_dict, workspace_page)

# def _test_2(browser, project_dict, workspace_page):
#     #project_dict, workspace_page = startup(browser)
#     workspace_page.set_library_filter('optproblems')
#     objects = workspace_page.get_object_types()
    
#     browser.execute_script('openmdao.project.clear();')
#     #closeout(project_dict, workspace_page)

# def _test_3(browser, project_dict, workspace_page):
#     #project_dict, workspace_page = startup(browser)
#     workspace_page.set_library_filter('optproblems')
#     objects = workspace_page.get_object_types()
    
#     browser.execute_script('openmdao.project.clear();')
#     #closeout(project_dict, workspace_page)


def _test_standard_library(browser, project_dict, workspace_page):
    #project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()

    eq(objects, [
        'BraninProblem',
        'PolyScalableProblem',
        'SellarProblem',])

    browser.execute_script('openmdao.project.clear();')


    ######################################
    project_dict, workspace_page = startup(browser)
    workspace_page('project_menu').click()

    browser.execute_script('openmdao.project.clear();')



    #closeout(project_dict, workspace_page)

def _test_console(browser,project_dict, workspace_page):
    # Check basic console functionality.
    #project_dict, workspace_page = startup(browser)

    # time.sleep(6.0)
    # workspace_page.do_command("print 'blah'") ###### problems
    # expected = ">>> print 'blah'\nblah"
    # eq(workspace_page.history, expected)

    # Check that browser title contains project name.
    title = browser.title
    expected = 'OpenMDAO: ' + project_dict['name'] + ' - '
    eq(title[:len(expected)], expected)

    browser.execute_script('openmdao.project.clear();')
    # Clean up.
    #closeout(project_dict, workspace_page)

def _test_slots_sorted_by_name(browser,project_dict, workspace_page):
#def _test_slots_sorted_by_name(browser):
    #project_dict, workspace_page = startup(browser)

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

    browser.execute_script('openmdao.project.clear();')
    #closeout(project_dict, workspace_page)

def _qqqtest_menu(browser,project_dict, workspace_page):
#def _test_menu(browser):
    #project_dict, workspace_page = startup(browser)

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


def _qqqtest_add_file(browser,project_dict, workspace_page):
#def _test_add_file(browser):
    # Check basic console functionality.
    #project_dict, workspace_page = startup(browser)
    # Get file paths

    file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
                                                 'paraboloid.py')

    # add first file from workspace
    time.sleep(3.0)
    workspace_page.add_file(file1_path)

    workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')

    workspace_page.new_folder('test_folder')
    time.sleep(1.0)
    workspace_page.add_file_to_folder('test_folder', file1_path)

    # print 'port',  TEST_CONFIG[ 'port' ]

    # import requests
    # r = requests.delete("http://localhost:%s/workspace/file/paraboloid.py" % str(TEST_CONFIG[ 'port' ]))

    # print "requests status", r.status_code


    #browser.execute_script('openmdao.project.closeWebSockets();')
    #browser.execute_script('openmdao.project.removeFile("/paraboloid.py");')
    #browser.execute_script('openmdao.project.remove_all_user_files();')
    #browser.execute_script('openmdao.project.removeFile("/_macros/default");')
    #browser.execute_script('openmdao.project.reload();')
    browser.execute_script('openmdao.project.clear();')

    # Clean up.
    #closeout(project_dict, workspace_page)


if __name__ == '__main__':
    main()
