# Gateway-to-Research Client Library

The GtR client library offers a Python implementation which can interact with the GtR API, giving developers a quick route to the data and dealing with complexities such as paging through result sets.

It currently supports the XML and JSON data formats from the native data format.  It does not currently support the CERIF API.

## Installation

Installation is easy:

1. Check it out from github!

2. Go into the "gtrclient" directory, and install in the normal way

    sudo python setup.py install

## Basic Usage

Import the "gtr" module from the client library

    >>> from gtrclient import gtr
    
Create an instance of the client, pointing at the standard public instance of the Gateway-to-Research API (which is also the web user interface)

    >>> client = gtr.GtRNative("http://gtr.rcuk.ac.uk/")

There are 4 different types of entity in the GtR data:

* Projects
* People
* Organisations
* Publications

Lists of these can be retrieved via the client using the following commands:

    >>> client.projects()
    <gtrclient.gtr.Projects object at 0xe63fd0>
    
    >>> client.people()
    <gtrclient.gtr.People object at 0xfb0790>
    
    >>> client.organisations()
    <gtrclient.gtr.Organisations object at 0xe630d0>
    
    >>> client.publications()
    <gtrclient.gtr.Publications object at 0xfb0e90>

Each of these list types is paged, so although you have a handle on all of the projects, or all of the people, you don't yet have the data.  You can interact with the list of projects/people/organisations/publications on the current page with:

    >>> p = client.projects()
    >>> p.projects()
    [<gtrclient.gtr.Project object at 0xe63e10>, <gtrclient.gtr.Project object at 0xfb0790>, ... ]

and so on for people, organisations and publications

To move between pages you can use the paging commands, thus:

    >>> p.current_page()
    1
    >>> p.next_page()
    True
    >>> p.next_page()
    True
    >>> p.current_page()
    3
    >>> p.previous_page()
    True
    >>> p.current_page()
    2
    >>> p.last_page()
    True
    >>> p.current_page()
    1247
    >>> p.first_page()
    True
    >>> p.current_page()
    1

Note that the page navigation methods return True or False, so next_page() will respond with False when there are no more pages to traverse.

The list types also behave like good Python iterables:

    >>> len(p)
    31151
    
    >>> for project in p:
    ...   print project.id()

The length of the list is the total number of entities (not the number of pages).  

BE WARNED: when you iterate over one of these lists you are iterating over everything in the dataset of that type, which will involve multiple HTTP requests to the GtR API.

You can retrieve individual records from the API as well:

    >>> project = client.project("B26AE9E7-B30A-46BD-8181-776BA55779E2")

Each object (project, person, organisation, project) has different properties.  All of them, though, will respond to id() and url() requests:

    >>> project.id()
    u'B26AE9E7-B30A-46BD-8181-776BA55779E2'
    
    >>> project.url()
    u'http://gtr.rcuk.ac.uk:80/project/B26AE9E7-B30A-46BD-8181-776BA55779E2'

You can also get the raw, underlying data that came from the API with one of the methods:


    >>> project.xml()
    '<gtr:projectOverview xmlns:gtr="http://gtr.rcuk.ac.uk/api"> ... '

    >>> project.as_dict()
    {u'projectComposition': {u'project': {u'status': u'Active', ...

    >>> project.json()
    '{\n  "projectComposition": {\n    "project": {\n ... '

All entity objects support these operations.

NOTE: if you are working with the JSON API and you request the XML serialisation, this will invoke an HTTP request to the API, and vice versa (see Advanced Usage for info on how to switch which serialisation of the API you are using).

Each entity object also supports a range of different data access operations.  Use dir() to discover more.  For example, you can do:

    >>> project.title()
    u'An anthropological investigation of bird sound'
    
    >>> project.funder()
    u'AHRC'

Entities also link out to other related entites, such as the organisations involved in a project:

    >>> project.orgs()
    [<gtrclient.gtr.Organisation object at 0xfce610>, <gtrclient.gtr.Organisation object at 0xfce490>, 
    <gtrclient.gtr.Organisation object at 0xfce450>, <gtrclient.gtr.Organisation object at 0xfce510>]
    
## Advanced Usage

TODO



