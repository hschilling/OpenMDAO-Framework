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


def _test_1(browser, project_dict, workspace_page):
    #project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')

    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')

    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')


    #closeout(project_dict, workspace_page)

def _qqqtest_2(browser, project_dict, workspace_page):
    #project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')
    #closeout(project_dict, workspace_page)

def _qqqtest_3(browser, project_dict, workspace_page):
    #project_dict, workspace_page = startup(browser)
    workspace_page.set_library_filter('optproblems')
    objects = workspace_page.get_object_types()
    
    browser.execute_script('openmdao.project.clear();')
    #closeout(project_dict, workspace_page)


# def _test_standard_library(browser, project_dict, workspace_page):
#     #project_dict, workspace_page = startup(browser)
#     workspace_page.set_library_filter('optproblems')
#     objects = workspace_page.get_object_types()

#     eq(objects, [
#         'BraninProblem',
#         'PolyScalableProblem',
#         'SellarProblem',])

#     browser.execute_script('openmdao.project.clear();')
#     #closeout(project_dict, workspace_page)

# def _test_console(browser,project_dict, workspace_page):
#     # Check basic console functionality.
#     #project_dict, workspace_page = startup(browser)

#     workspace_page.do_command("print 'blah'")
#     expected = ">>> print 'blah'\nblah"
#     eq(workspace_page.history, expected)

#     # Check that browser title contains project name.
#     title = browser.title
#     expected = 'OpenMDAO: ' + project_dict['name'] + ' - '
#     eq(title[:len(expected)], expected)

#     browser.execute_script('openmdao.project.clear();')
#     # Clean up.
#     #closeout(project_dict, workspace_page)

# def _test_add_file(browser,project_dict, workspace_page):
# #def _test_add_file(browser):
#     # Check basic console functionality.
#     #project_dict, workspace_page = startup(browser)
#     # Get file paths

#     # file1_path = pkg_resources.resource_filename('openmdao.examples.simple',
#     #                                              'paraboloid.py')

#     # # add first file from workspace
#     # workspace_page.add_file(file1_path)

#     # workspace_page.add_library_item_to_dataflow('openmdao.main.assembly.Assembly', 'top')

#     # workspace_page.new_folder('test_folder')
#     # time.sleep(1.0)
#     # workspace_page.add_file_to_folder('test_folder', file1_path)

#     # print 'port',  TEST_CONFIG[ 'port' ]

#     # import requests
#     # r = requests.delete("http://localhost:%s/workspace/file/paraboloid.py" % str(TEST_CONFIG[ 'port' ]))

#     # print "requests status", r.status_code


#     #browser.execute_script('openmdao.project.closeWebSockets();')
#     #browser.execute_script('openmdao.project.removeFile("/paraboloid.py");')
#     #browser.execute_script('openmdao.project.remove_all_user_files();')
#     #browser.execute_script('openmdao.project.removeFile("/_macros/default");')
#     #browser.execute_script('openmdao.project.reload();')
#     browser.execute_script('openmdao.project.clear();')

#     # Clean up.
#     #closeout(project_dict, workspace_page)


if __name__ == '__main__':
    main()
