
Case Recording Structure
-------------------------

Overall Concepts
++++++++++++++++

The developers of OpenMDAO believe that by default, users would prefer to record everything, so that is the default. So OpenMDAO records, in addition to metadata about the model, constants, inputs, outputs.

The primary file formats for case recording in OpenMDAO are `JSON <http://en.wikipedia.org/wiki/JSON/>`_ and `BSON <http://en.wikipedia.org/wiki/BSON/>`_ 

http://en.wikipedia.org/wiki/BSON

If users need to have the case records in another format, OpenMDAO provides post processors that convert the JSON and BSON case record files to those formats. The formats currently supported are CSV, sqlite, and a simple text-based data dump format.

Record everything by default philosophy

Post processors

Case Recording and Querying Classes
+++++++++++++++++++++++++++++++++++

Recording Classes
=================

``_BaseRecorder`` - Base class for JSONRecorder and BSONRecorder

``JSONRecorder`` - Dumps a run in JSON form to any object that looks like a file

``BSONRecorder`` - Dumps a run in BSON form to any object that looks like a file

Query Classes
=================

``CaseDataset`` - Reads case data from a file like objects and allows queries on it

``Query`` - Retains query information for a class ``CaseDataset``. All methods other than ``fetch`` and ``write`` return ``self``, so operations are easily chained.  If the same method is called more than once, only the last call has an effect.

Key Methods
+++++++++++

Recording options
+++++++++++++++++

Includes and Excludes

How it is determined what gets recorded
+++++++++++++++++++++++++++++++++++++++

Collapsed depgraph. What is that? Successors to components in the workflow. Include examples

Structure of JSON files
++++++++++++++++++++++++

Metadata/Simulation Info
========================

Graphs: Depgraph, Component graph
Driver info

Cases
=====
What constitutes a case? What about cases from derivative calculation?

Subcases and subdrivers

UUIDs

Pro Tip: What’s a good way to view a JSON file? Use Chrome if it isn’t too big since you can expand/collapse

Why use BSON files?
+++++++++++++++++++

Significant digits stored

Query capability
++++++++++++++++

Concept of chaining of query methods.

Flow from JSON/BSON file to what you want [ maybe make a diagram ]:

* cds = CaseDataset(‘filename.json’, 'json')
  - JSON/BSON file -> casehandlers.query.CaseDataset 
  - CaseDataSet’s .data -> casehandlers.query.Query object
  -	Do filtering on the Query object using methods like:
	+ vars
	+ locals
	+ Then call .fetch() on the Query object to get the actual data
