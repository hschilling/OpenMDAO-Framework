"""
Basic unit testing of OpenMDAO's derivative capability.
"""

from cStringIO import StringIO
import networkx as nx
import re
import unittest
from mock import Mock

from numpy import zeros, array, identity, random

from openmdao.lib.architectures.api import MDF, CO
from openmdao.lib.optproblems.api import UnitScalableProblem

import openmdao.main.derivatives
from openmdao.main.api import Component, VariableTree, Driver, Assembly, set_as_top
from openmdao.main.datatypes.api import Array, Float, VarTree, Int
from openmdao.main.derivatives import applyJ, applyJT
from openmdao.main.hasparameters import HasParameters
from openmdao.main.hasobjective import HasObjective
from openmdao.main.hasconstraints import HasConstraints
from openmdao.main.interfaces import IHasParameters, implements
from openmdao.test.execcomp import ExecCompWithDerivatives, ExecComp
from openmdao.util.decorators import add_delegate
from openmdao.util.testutil import assert_rel_error
from openmdao.util.graph import list_deriv_vars

class Tree2(VariableTree):

    d1 = Array(zeros((1, 2)))

class Tree1(VariableTree):

    a1 = Float(3.)
    vt1 = VarTree(Tree2())

class MyComp(Component):

    x1 = Float(0.0, iotype='in')
    x2 = Float(0.0, iotype='in')
    x3 = Array(zeros((2, 1)), iotype='in')
    x4 = Array(zeros((2, 2)), iotype='in')
    vt = VarTree(Tree1(), iotype='in')

    xx1 = Float(0.0, iotype='out')
    xx2 = Float(0.0, iotype='out')
    xx3 = Array(zeros((2, 1)), iotype='out')
    xx4 = Array(zeros((2, 2)), iotype='out')
    vvt = VarTree(Tree1(), iotype='out')

    def execute(self):
        """ doubler """
        pass

    def provideJ(self):
        """ calculates the Jacobian """

        self.J = array([[1.5, 3.7, 2.5, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1],
                        [7.4, 23.7, 1.1, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2],
                        [5.5, 8.7, 1.9, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3],
                        [1.4, 2.4, 3.4, 4.4, 5.4, 6.4, 7.4, 8.4, 9.4, 10.4, 11.4],
                        [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5],
                        [1.6, 2.6, 3.6, 4.6, 5.6, 6.6, 7.6, 8.6, 9.6, 10.6, 11.6],
                        [1.7, 2.7, 3.7, 4.7, 5.7, 6.7, 7.7, 8.7, 9.7, 10.7, 11.7],
                        [1.8, 2.8, 3.8, 4.8, 5.8, 6.8, 7.8, 8.8, 9.8, 10.8, 11.8],
                        [1.9, 2.9, 3.9, 4.9, 5.9, 6.9, 7.9, 8.9, 9.9, 10.9, 11.9],
                        [1.10, 2.10, 3.10, 4.10, 5.10, 6.10, 7.10, 8.10, 9.10, 10.10, 11.10],
                        [1.11, 2.11, 3.11, 4.11, 5.11, 6.11, 7.11, 8.11, 9.11, 10.11, 11.11]])

        return self.J

    def list_deriv_vars(self):
        input_keys = ('x1', 'x2', 'x3', 'x4', 'vt.a1', 'vt.vt1.d1')
        output_keys = ('xx1', 'xx2', 'xx3', 'xx4', 'vvt.a1', 'vvt.vt1.d1')

        return input_keys, output_keys

class IntComp(Component):
    x = Float(0.0, iotype='in')
    x_ignore = Float(0.0, iotype='in', deriv_ignore=True)
    int_in = Int(0, iotype='in', deriv_ignore=True)
    int_out = Int(0, iotype='out', deriv_ignore=True)
    y = Float(0.0, iotype='out')
    y_ignore = Float(0.0, iotype='out', deriv_ignore=True)

    def execute(self):
        self.y = 2.0*self.x
        self.int_out = self.int_in

    def list_deriv_vars(self):
        return ('x',), ('y',)

    def provideJ(self):
        return array([[2.0]])

class BadListDerivsComp(Component):
    x = Float(iotype='in')
    y = Float(iotype='out')

    def execute(self):
        self.y = self.x * 2.0

    def list_deriv_vars(self):
        return ['x', 'y']

    def provideJ(self):
        return array([[2.0]])

class SimpleComp(Component):

    x = Float(3.0, iotype='in')
    y = Float(6.0, iotype='out')

    def execute(self):
        self.y = 2.0*self.x

    def provideJ(self):
        return array([[2.0]])

    def list_deriv_vars(self):
        return ('x',), ('y',)

@add_delegate(HasParameters, HasObjective, HasConstraints)
class SimpleDriver(Driver):
    """Driver with Parameters"""

    implements(IHasParameters)


top = set_as_top(Assembly())
top.add('comp', SimpleComp())
top.add('driver', SimpleDriver())
top.add('inner_driver', SimpleDriver())
top.add('target', Float(3.0, iotype='in'))

top.driver.workflow.add('inner_driver')
top.driver.add_parameter('target', low=-100, high=100)
top.driver.add_objective('target + comp.x + comp.y')

top.inner_driver.workflow.add('comp')
top.inner_driver.add_parameter('comp.x', low=-100, high=100)
top.inner_driver.add_objective('2.0*target + 2.0*comp.x + 2.0*comp.y')

top.run()
top.inner_driver.workflow.initialize_residual()
#J = top.inner_driver.workflow.calc_gradient()
edges = top.inner_driver.workflow._edges
#print edges
#print top.inner_driver.list_objective_targets()

from openmdao.util.dotgraph import plot_graph
plot_graph( top._depgraph, fmt='plain-ext' )



contents = '''<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>Depgraph</title>
  <meta name="description" content="Depgraph in D3">
  <meta name="author" content="OpenMDAO">

  <script src="http://d3js.org/d3.v3.min.js"></script>
</head>

<body>

    <div id="svgContent">
    </div>

        <script type="text/javascript">



window.onload = function(){
  var w = 500,
      h = 500;

    var xscale = d3.scale.linear()
        .domain([0, 5.0])
        .range([0, w]);
    var yscale = d3.scale.linear()
        .domain([0, 5.0])
        .range([h, 0]);

    var svg = d3.select("#svgContent")
                  .append("svg")
                  .attr("width", w)
                  .attr("height", h)
                  .attr('preserveAspectRatio', 'xMinYMin slice') ;
    var dataSet = {
            nodes: [ '''

with open("graph.plain-ext", "r") as f:
  node_content = ''
  edge_content = ''
  node_locations = {}
  for i, line in enumerate(f):
    if line.startswith( "node"):
        # node name x y width height label style shape color fillcolor
        # shape can be ellipse, diamond, box or invhouse
        dummy, name, x, y, width, height, label, style, shape, color, fillcolor = line.split()
        if name.startswith('"'):
            name = name[1:-1]
        node_content += '{ name: "%s", id:"%s", x:%s, y:%s, shape:"%s", fixed:true},\n' % ( label, name, x, y, shape )
        node_locations[ name ] = (x,y)
    if line.startswith( "edge"):
        # edge tail head n x1 y1 .. xn yn [label xl yl] style color
        #{ source: 0, target: 1 },
        dummy, tail, head = line.split()[:3]
        if tail.startswith('"'):
            tail = tail[1:-1]
        if head.startswith('"'):
            head = head[1:-1]
        edge_content += '{sourcex: %s ,sourcey: %s, targetx: %s, targety: %s},\n' % ( node_locations[tail][0], node_locations[tail][1], node_locations[head][0], node_locations[head][1] )

contents += node_content

contents += '''
            ],
            edges: [
            '''
contents += edge_content


contents += '''
            ]
        };
    
        var force = self.force = d3.layout.force()
            .nodes(dataSet.nodes)
            .links(dataSet.edges)
            .size([w,h])
            .start();

        var link = svg.selectAll(".link")
            .data(dataSet.edges)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke", "green")
            .attr("stroke-width", 5)
            .attr("x1", function(d) { alert(d.sourcex); return d.sourcex; })
            .attr("y1", function(d) { return d.sourcey; })
            .attr("x2", function(d) { return d.targetx; })
            .attr("y2", function(d) { return d.targety; });
  

        var node = svg.selectAll(".node")
            .data(dataSet.nodes)
            .enter().append("g")
            .attr("class", function (d) {
                return d.shape + " node";
            })
            .attr("transform", function(d) { return "translate(" + xscale(d.x) + "," + yscale(d.y) + " )" } )
            ;

        d3.selectAll(".ellipse").append("ellipse")
            .attr("rx", 40)
            .attr("fill", "none")
            .attr("ry", 20)
            .attr("stroke", "black")
            .attr("stroke-width", 2)
            .attr("class", function (d) {
            return "node type" + d.type
        });

        d3.selectAll(".box").append("rect")
            .attr("width", 80)
            .attr("fill", "none")
            .attr("height", 40)
            .attr("stroke", "black")
            .attr("stroke-width", 2)
            .attr("transform", "translate(-40,-20)")
            .attr("class", function (d) {
            return "node type" + d.type
        });

        poly = [{"x":0.0, "y":25.0},
                {"x":8.5,"y":23.4},
                {"x":13.0,"y":21.0},
                {"x":19.0,"y":15.5}];

        d3.selectAll(".diamond").append("polygon")
            .attr("points", "-30,0, 0,25, 30,0 0,-25")
            .attr("fill", "none")
            .attr("stroke","black")
            .attr("stroke-width",2);

        d3.selectAll(".invhouse").append("polygon")
            .attr("points", "-40,-25, 40,-25, 40,10 0,25 -40,10")
            .attr("fill", "none")
            .attr("stroke","black")
            .attr("stroke-width",2);

        node.append("text")
            .text(function(d) { return d.name })
            .style("text-anchor", "middle")
            ;
        
        force.on("tick", tick);

        function tick() {
          link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

        }

};

    



        </script>


</body>
</html>'''

f = open("depgraph.html","w")
f.write(contents)
f.close()




