
Case Recording Structure
-------------------------

Overall Concepts
++++++++++++++++

Use JSON/BSON for primary recording with post processors for other formats.

Record everything by default philosophy

Case Recording and Querying Classes
+++++++++++++++++++++++++++++++++++

Recording Classes
=================

``_BaseRecorder`` - Base class for JSONRecorder and BSONRecorder

``JSONRecorder`` - Dumps a run in JSON form to any object that looks like a file

``BSONRecorder`` - Dumps a run in BSON form to any object that looks like a file

Query Classes
=================

``CaseDataset`` - Reads case data from `filename` and allows queries on it.

``Query`` - Retains query information for a :class:`CaseDataset`. All methods other than :meth:`fetch` and :meth:`write` return ``self``, so operations are easily chained.  If the same method is called more than once, only the last call has an effect.


Still to add::

3.	Key methods and where they are called
4.	Recording options
5.	How it is determined what gets recorded
a.	Collapsed depgraph
i.	What is that?
b.	Successors to components in the workflow
c.	Include examples
6.	Structure of JSON files
a.	Metadata/Simulation Info
i.	graphs
1.	depgraph
2.	component graph
b.	Driver info
c.	Cases
i.	What constitutes a case? What about cases from derivative calculation?
ii.	Subcases and subdrivers
iii.	UUIDs
7.	Pro Tip: What’s a good way to view a JSON file? Use Chrome if it isn’t too big since you can expand/collapse
8.	Why use BSON files?
9.	Post processors
10.	Significant digits stored
11.	Query capability
a.	Concept of chaining of query methods
b.	Flow from JSON/BSON file to what you want:
i.	cds = CaseDataset(‘filename.json’, 'json')
ii.	JSON/BSON file -> casehandlers.query.CaseDataset 
iii.	CaseDataSet’s .data -> casehandlers.query.Query object
iv.	Do filtering on the Query object using methods like:
1.	vars
2.	locals
v.	Then call .fetch() on the Query object to get the actual data
