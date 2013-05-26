import requests, json
import urler
from lxml import etree
from copy import deepcopy
from common import GtR, Paging, MIME_MAP

NSMAP = {"gtr" : "http://gtr.rcuk.ac.uk/api"}
GTR_PREFIX = "gtr"

class GtRNative(GtR):
    
    def __init__(self, base_url, page_size=25, serialisation="json", username=None, password=None):
        super(GtRNative, self).__init__(base_url, page_size, serialisation, username, password)
        
        self.factory = GtRDAOFactory()
        
        self.project_base = self.base_url + "/project/"
        self.org_base = self.base_url + "/organisation/"
        self.person_base = self.base_url + "/person/"
        self.publication_base = self.base_url + "/publication/"
    
    ## List Retrieval Methods ##
    
    def projects(self, page=None, page_size=None):
        page_size = self._constrain_page_size(page_size)
        page_size = page_size if page_size is not None else self.page_size
        data, paging = self._api(self.project_base, page=page, page_size=page_size)
        if data is not None and paging is not None:
            return Projects(self, data, paging, self.project_base)
        return None
        
    def organisations(self, page=None, page_size=None):
        page_size = self._constrain_page_size(page_size)
        page_size = page_size if page_size is not None else self.page_size
        data, paging = self._api(self.org_base, page=page, page_size=page_size)
        if data is not None and paging is not None:
            return Organisations(self, data, paging, self.org_base)
        return None

    def people(self, page=None, page_size=None):
        page_size = self._constrain_page_size(page_size)
        page_size = page_size if page_size is not None else self.page_size
        data, paging = self._api(self.person_base, page=page, page_size=page_size)
        if data is not None and paging is not None:
            return People(self, data, paging, self.person_base)
        return None
        
    def publications(self, page=None, page_size=None):
        page_size = self._constrain_page_size(page_size)
        page_size = page_size if page_size is not None else self.page_size
        data, paging = self._api(self.publication_base, page=page, page_size=page_size)
        if data is not None and paging is not None:
            return Publications(self, data, paging, self.publication_base)
        return None
    
    ## Individual retrieval methods ##
    
    def project(self, uuid):
        url = self.project_base + uuid
        raw, _ = self._api(url)
        if raw is not None:
            return Project(self, raw)
        return None

    def organisation(self, uuid, page_size=None):
        url = self.org_base + uuid
        page_size = self._constrain_page_size(page_size)
        page_size = page_size if page_size is not None else self.page_size
        raw, paging = self._api(url, page_size=page_size)
        if raw is not None and paging is not None:
            return Organisation(self, raw, paging)
        return None
        
    def person(self, uuid):
        url = self.person_base + uuid
        raw, _ = self._api(url)
        if raw is not None:
            return Person(self, raw)
        return None

    def publication(self, uuid):
        url = self.publication_base + uuid
        raw, _ = self._api(url)
        if raw is not None:
            return Publication(self, raw)
        return None
        
class GtRDAOFactory(object):
    def __init__(self):
        self.class_map = {
            "application/xml" : {
                "projects" : ProjectsXMLDAO,
                "organisations" : OrganisationsXMLDAO,
                "people" : PeopleXMLDAO,
                "publications" : PublicationsXMLDAO,
                "project" : ProjectXMLDAO,
                "organisation" : OrganisationXMLDAO,
                "person" : PersonXMLDAO,
                "publication" : PublicationXMLDAO
            },
            "application/json" : {
                "projects" : ProjectsJSONDAO,
                "organisations" : OrganisationsJSONDAO,
                "people" : PeopleJSONDAO,
                "publications" : PublicationsJSONDAO,
                "project" : ProjectJSONDAO,
                "organisation" : OrganisationJSONDAO,
                "person" : PersonJSONDAO,
                "publication" : PublicationJSONDAO
            }
        }
    
    def projects(self, client, data):
        return self._load(client, data, "projects")
        
    def project(self, client, data):
        return self._load(client, data, "project")
        
    def organisations(self, client, data):
        return self._load(client, data, "organisations")
    
    def organisation(self, client, data):
        return self._load(client, data, "organisation")
    
    def people(self, client, data):
        return self._load(client, data, "people")
    
    def person(self, client, data):
        return self._load(client, data, "person")
    
    def publications(self, client, data):
        return self._load(client, data, "publications")
    
    def publication(self, client, data):
        return self._load(client, data, "publication")
    
    def _load(self, client, data, domain):
        klazz = self.class_map.get(client.mimetype, {}).get(domain)
        if domain is not None:
            return klazz(data)
        return None

class Native(object):
    def __init__(self, client):
        self.client = client
        self.dao = None
    
    def url(self):
        raise NotImplementedError()

    def xml(self, pretty_print=True):
        if self.dao is None:
            return None
        
        if hasattr(self.dao, "xml"):
            return self.dao.xml(pretty_print)
        
        xml, _ = self.client._api(self.url(), mimetype="application/xml")
        if xml is not None:
            return etree.tostring(xml, pretty_print=pretty_print)
        return None
        
    def as_dict(self):
        if self.dao is None:
            return None
        
        if hasattr(self.dao, "as_dict"):
            return self.dao.as_dict()
        
        j, _ = self.client._api(self.url(), mimetype="application/json")
        return j
        
    def json(self, pretty_print=True):
        d = self.as_dict()
        if pretty_print:
            return json.dumps(d, indent=2)
        return json.dumps(d)

class NativeXMLDAO(object):

    def __init__(self, raw):
        self.raw = raw
    
    ## Methods for use by extending classes ##
    
    def _from_xpath(self, xp):
        """
        return the text from the first element found by the provided xpath
        """
        els = self.raw.xpath(xp, namespaces=NSMAP)
        if els is not None and len(els) > 0:
            if hasattr(els[0], "text"):
                return els[0].text
            return str(els[0])
        return None
    
    def _get_subs(self, parent_xpath, siblings=()):
        """
        get a tuple containing the text from the first sibling xpath inside each parent xpath
        """
        tups = []
        for org in self.raw.xpath(parent_xpath, namespaces=NSMAP):
            sibs = []
            for sib in siblings:
                els = org.xpath(sib, namespaces=NSMAP)
                if els is not None and len(els) > 0:
                    val = els[0].text
                    sibs.append(val)
            tups.append(tuple(sibs))
        return tups
    
    def _do_xpath(self, xp):
        """
        just apply the xpath to the raw appropriately
        """
        return self.raw.xpath(xp, namespaces=NSMAP)
    
    def _port(self, xp, new_root):
        """
        for each result for the xpath, port (via a deep copy) the result to an element 
        named by new_root
        """
        ports = []
        for el in self.raw.xpath(xp, namespaces=NSMAP): 
            root = self._gtr_element(new_root)
            for child in el:
                root.append(deepcopy(child))
            ports.append(root)
        return ports
    
    def _wrap(self, source, wrappers, clone=True):
        """
        wrap the provided element (via a deep copy if requested) in an 
        element named by wrappers (which may be a hierarchy of elements with their namespacessa
        """
        # first create the a list of elements from the hierarchy
        hierarchy = wrappers.split("/")
        elements = []
        for wrapper in hierarchy:
            parts = wrapper.split(":")
            element = None
            if len(parts) == 1:
                element = self._element(GTR_PREFIX, parts[0])
            elif len(parts) == 2:
                element = self._element(parts[0], parts[1])
            elements.append(element)
        
        if clone:
            source = deepcopy(source)
        
        # now add the elements to eachother in reverse
        for i in range(len(elements) - 1, -1, -1):
            elements[i].append(source)
            source = elements[i]
        
        return source
    
    def _element(self, prefix, name):
        return etree.Element("{" + NSMAP.get(prefix) + "}" + name, nsmap=NSMAP)
    
    def _gtr_element(self, name):
        """
        create a new element with the GTR prefix and namespace map
        """
        return self._element(GTR_PREFIX, name)
    
    def xml(self, pretty_print=True):
        return etree.tostring(self.raw, pretty_print=pretty_print)
    
class NativeJSONDAO(object):
    def __init__(self, raw):
        self.raw = raw
    
    def as_dict(self):
        return self.raw
        
    def json(self, pretty_print=True):
        d = self.as_dict()
        if pretty_print:
            return json.dumps(d, indent=2)
        return json.dumps(d)

class NativePaged(Native):
    def __init__(self, client, paging):
        super(NativePaged, self).__init__(client)
        self.paging = paging

    def record_count(self):
        return self.paging.record_count
    
    def pages(self):
        return self.paging.pages
        
    def next_page(self):
        if self.paging.next is None or self.paging.next == "":
            return False
        raw, paging = self.client._api(self.paging.next)
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
    
    def previous_page(self):
        if self.paging.previous is None or self.paging.previous == "":
            return False
        raw, paging = self.client._api(self.paging.previous)
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
        
    def first_page(self):
        if self.paging.first is None or self.paging.first == "":
            return False
        raw, paging = self.client._api(self.paging.first)
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
        
    def last_page(self):
        if self.paging.last is None or self.paging.last == "":
            return False
        raw, paging = self.client._api(self.paging.last)
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
    
    def skip_to_page(self, page):
        if self.paging.last is None or self.paging.last == "":
            return False
        if page > self.paging.last:
            return False
        if page < 1:
            return False
        raw, paging = self.client._api(self.url(), page=page)
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
    
    def current_page(self):
        return self.paging.current_page()
        
    def current_page_size(self):
        return self.paging.current_page_size()
        
    def list_elements(self):
        """
        subclass should implement this to return a list of Native objects.
        It will be used to run the iterator
        """
        raise NotImplementedError("list_elements has not been implemented")
    
    def __iter__(self):
        return self.iterator()
    
    def iterator(self, reset_pages=True, stop_at_page_boundary=False):
        if reset_pages:
            self.first_page()
        def f():
            while True:
                elements = self.list_elements()
                for p in elements:
                    yield p
                if stop_at_page_boundary:
                    break
                if not self.next_page():
                    break
        return f()
        
    def __len__(self):
        return self.record_count()


#### List Objects ####

## ------ Projects ------- ##

class Projects(NativePaged):

    def __init__(self, client, raw, paging, url, dao=None):
        super(Projects, self).__init__(client, paging)
        self.dao = dao if dao is not None else client.factory.projects(client, raw)
        self._url = url

    def url(self):
        return self._url

    def projects(self):
        return self.dao.projects(self.client)
        
    def list_elements(self):
        return self.projects()

class ProjectsXMLDAO(NativeXMLDAO):

    project_xpath = "/gtr:projects/gtr:project"
    
    project_wrapper = "gtr:projectOverview/gtr:projectComposition"

    def __init__(self, raw):
        super(ProjectsXMLDAO, self).__init__(raw)

    def projects(self, client):
        raws = self._do_xpath(self.project_xpath)
        return [Project(client, self._wrap(raw, self.project_wrapper)) for raw in raws]

class ProjectsJSONDAO(NativeJSONDAO):
    def __init__(self, raw):
        super(ProjectsJSONDAO, self).__init__(raw)
    
    def projects(self, client):
        return [Project(client, {"projectComposition" : {"project" : data}}) for data in self.raw.get('project', [])]

### -------- End Projects -------- ###

### ------- Organisations -------- ###

class Organisations(NativePaged):

    def __init__(self, client, raw, paging, url, dao=None):
        super(Organisations, self).__init__(client, paging)
        self.dao = dao if dao is not None else client.factory.organisations(client, raw)
        self._url = url

    def url(self):
        return self._url
        
    def organisations(self):
        return self.dao.organisations(self.client)
        
    def list_elements(self):
        return self.organisations()

class OrganisationsXMLDAO(NativeXMLDAO):

    organisation_xpath = "/gtr:organisations/gtr:organisation"
    
    organisation_wrapper = "gtr:organisationOverview"

    def __init__(self, raw):
        super(OrganisationsXMLDAO, self).__init__(raw)

    def organisations(self):
        raws = self._do_xpath(self.organisation_xpath)
        return [Organisation(self.client, self._wrap(raw, self.organisation_wrapper), None) for raw in raws]

class OrganisationsJSONDAO(NativeJSONDAO):
    def __init__(self, raw):
        super(OrganisationsJSONDAO, self).__init__(raw)
    
    def organisations(self, client):
        return [Organisation(client, {"organisationOverview" : {"organisation" : data}}, None) 
                    for data in self.raw.get('organisation', [])]


## ---- End Organisations ---- ##

## ----- People ------ ##

class People(NativePaged):

    def __init__(self, client, raw, paging, url, dao=None):
        super(People, self).__init__(client, paging)
        self.dao = dao if dao is not None else client.factory.people(client, raw)
        self._url = url

    def url(self):
        return self._url
        
    def people(self):
        return self.dao.people(self.client)
        
    def list_elements(self):
        return self.people()

class PeopleXMLDAO(NativeXMLDAO):

    person_xpath = "/gtr:people/gtr:person"
    
    person_wrapper = "gtr:personOverview"

    def __init__(self, raw):
        super(PeopleXMLDAO, self).__init__(raw)

    def people(self, client):
        raws = self._do_xpath(self.person_xpath)
        return [Person(client, None, self._wrap(raw, self.person_wrapper)) for raw in raws]

class PeopleJSONDAO(NativeJSONDAO):
    def __init__(self, raw):
        super(PeopleJSONDAO, self).__init__(raw)

    def people(self, client):
        return [Person(client, {"person" :  data})
                    for data in self.raw.get("person", [])]

## ----- End People ------ ##

## ------ Publications ------ ##

class Publications(NativePaged):

    def __init__(self, client, raw, paging, url, dao=None):
        super(Publications, self).__init__(client, paging)
        self.dao = dao if dao is not None else client.factory.publications(client, raw)
        self._url = url

    def url(self):
        return self._url
        
    def publications(self):
        return self.dao.publications(self.client)
        
    def list_elements(self):
        return self.publications()

class PublicationsXMLDAO(NativeXMLDAO):

    publication_xpath = "/gtr:publications/gtr:publication"
    
    publication_wrapper = "gtr:publicationOverview"

    def __init__(self, raw):
        super(PublicationsXMLDAO, self).__init__(raw)

    def publications(self, client):
        raws = self._do_xpath(self.publication_xpath)
        return [Publication(client, self._wrap(raw, self.publication_wrapper)) for raw in raws]

class PublicationsJSONDAO(NativeJSONDAO):

    def __init__(self, raw):
        super(PublicationsJSONDAO, self).__init__(raw)

    def publications(self, client):
        return [Publication(client, { "publication" : data })
                        for data in self.raw.get("publication", [])]

## ------- End Publications ------ ##

##### Individual Entity Objects ####

## ------ Project ------- ##

class Project(Native):
    def __init__(self, client, raw, dao=None):
        super(Project, self).__init__(client)
        self.dao = dao if dao is not None else client.factory.project(client, raw)

    def url(self): return self.dao.url()
    def id(self): return self.dao.id()
    def title(self): return self.dao.title()
    def start(self): return self.dao.start()
    def status(self): return self.dao.status()  
    def end(self): return self.dao.end()
    def abstract(self): return self.dao.abstract()
    def value(self): return self.dao.value()
    def category(self): return self.dao.category()
    def reference(self): return self.dao.reference()
    
    def funder(self): return self.dao.funder(self.client)
    def lead(self): return self.dao.lead(self.client)
    def orgs(self): return self.dao.orgs(self.client)
    def people(self): return self.dao.people(self.client)
    def collaborators(self): return self.dao.collaborators(self.client)
    
    def collaboration_outputs(self): pass
    def intellectual_property_outputs(self): pass
    def policy_influence_outputs(self): pass
    def product_outputs(self): pass
    def research_material_outputs(self): pass
    def publications(self): pass
    
    def fetch(self):
        updated_proj = self.client.project(self.id())
        if updated_proj is not None:
            self.dao.raw = updated_proj.dao.raw
            return True
        return False

class ProjectXMLDAO(NativeXMLDAO):

    composition_base = "/gtr:projectOverview/gtr:projectComposition"
    project_base = composition_base + "/gtr:project"
    
    url_xpath = project_base + "/@url"
    id_xpath = project_base + "/gtr:id"
    title_xpath = project_base + "/gtr:title"
    start_xpath = project_base + "/gtr:fund/gtr:start"
    status_xpath = project_base + "/gtr:status"
    end_xpath = project_base + "/gtr:fund/gtr:end"
    abstract_xpath = project_base + "/gtr:abstractText"
    funder_xpath = project_base + "/gtr:fund/gtr:funder/gtr:name"
    value_xpath = project_base + "/gtr:fund/gtr:valuePounds"
    category_xpath = project_base + "/gtr:grantCategory"
    reference_xpath = project_base + "/gtr:grantReference"
    
    lead_xpath = composition_base + "/gtr:leadResearchOrganisation"
    orgs_xpath = composition_base + "/gtr:organisations/gtr:organisation"
    person_xpath = composition_base + "/gtr:projectPeople/gtr:projectPerson"
    collaborator_xpath = composition_base + "/gtr:collaborations/gtr:collaborator"
    
    organisation_wrapper = "organisationOverview"
    person_wrapper = "personOverview"
    
    organisation_element = "organisation"
    person_element = "person"

    def __init__(self, raw):
        super(ProjectXMLDAO, self).__init__(raw)

    def url(self):
        return self._from_xpath(self.url_xpath)

    def id(self):
        return self._from_xpath(self.id_xpath)

    def title(self):
        return self._from_xpath(self.title_xpath)
    
    def start(self):
        return self._from_xpath(self.start_xpath)
    
    def status(self):
        return self._from_xpath(self.status_xpath)
    
    def end(self):
        return self._from_xpath(self.end_xpath)
    
    def abstract(self):
        return self._from_xpath(self.abstract_xpath)
    
    # FIXME
    def funder(self):
        return self._from_xpath(self.funder_xpath)
    
    def value(self):
        return self._from_xpath(self.value_xpath)
    
    def category(self):
        return self._from_xpath(self.category_xpath)
    
    def reference(self):
        return self._from_xpath(self.reference_xpath)
    
    def lead(self, client):
        raws = self._port(self.lead_xpath, self.organisation_element)
        if len(raws) > 0:
            return Organisation(client, self._wrap(raws[0], self.organisation_wrapper), None)
        return None
        
    def orgs(self, client):
        raws = self._do_xpath(self.orgs_xpath)
        return [Organisation(client, self._wrap(raw, self.organisation_wrapper), None) for raw in raws]
        
    def people(self, client):
        raws = self._port(self.person_xpath, self.person_element)
        return [Person(client, self._wrap(raw, self.person_wrapper)) for raw in raws]
    
    def collaborators(self, client):
        raws = self._port(self.collaborator_xpath, self.organisation_element)
        return [Organisation(client, self._wrap(raw, self.organisation_wrapper), None) for raw in raws]

class ProjectJSONDAO(NativeJSONDAO):
    def __init__(self, raw):
        super(ProjectJSONDAO, self).__init__(raw)

    def _composition(self):
        return (self.raw.get("projectComposition", {}))

    def _project(self):
        return (self.raw.get("projectComposition", {})
                        .get("project", {}))

    def url(self):
        return self._project().get("url")

    def id(self):
        return self._project().get("id")
    
    def title(self):
        return self._project().get("title")
    
    def start(self):
        return self._project().get("fund", {}).get("start")
    
    def status(self):
        return self._project().get("status")
    
    def end(self):
        return self._project().get("fund", {}).get("end")
    
    def abstract(self):
        return self._project().get("abstractText")
    
    def funder(self, client):
        return Organisation(client, {"organisationOverview" : {"organisation" : self._project().get("fund", {}).get("funder", {})}}, None)
    
    def value(self):
        return self._project().get("fund", {}).get("valuePounds")
    
    def category(self):
        return self._project().get("grantCategory")
    
    def reference(self):
        return self._project().get("grantReference")
    
    def lead(self, client):
        lro = self._composition().get("leadResearchOrganisation")
        if lro is not None:
            return Organisation(client, {"organisationOverview" : {"organisation" : lro}}, None)
        return None
        
    def orgs(self, client):
        return [Organisation(client, {"organisationOverview" : {"organisation" : data}}, None) 
                    for data in self._composition().get("organisation", [])]
        
    def people(self, client):
        return [Person(client, {"person" : data })
                    for data in self._composition().get("projectPerson", [])]
    
    def collaborators(self, client):
        return [Organisation(client, {"organisationOverview" : {"organisation" : data}}, None)
                    for data in self._composition().get("collaborator", [])]

## ------ End Project -------- ##

## -------- Organisation -------- ##

class Organisation(NativePaged):

    def __init__(self, client, raw, paging, dao=None):
        super(Organisation, self).__init__(client, paging)
        self.dao = dao if dao is not None else client.factory.organisation(client, raw)
        self.custom_dao = dao is not None
    
    def url(self): return self.dao.url()
    def id(self): return self.dao.id()
    def name(self): return self.dao.name()
    def projects(self): return self.dao.projects(self.client)
    
    def load_all_projects(self):
        # use with caution, will load all the projects for this organisation
        # and if you use any of the paging features afterwards, it will be
        # reset
        current_projects = self.projects()
        self.next_page()
        self.dao.add_projects(current_projects)
        """
        if self.paging.next is None or self.paging.next == "":
            return
        raw, paging = self.client._api(self.paging.next)
        if paging is not None:
            self.paging = paging
        if raw is not None:
            interim_dao = None
            if self.custom_dao:
                interim_dao = deepcopy(self.dao)
                interim_dao.raw = raw
            else:
                interim_dao = client.factory.organisation(client, raw)
            
            projects = raw.get("organisationOverview", {}).get("project", [])
        
        if raw is not None and paging is not None:
            self.dao.raw = raw
            self.paging = paging
            return True
        return False
        next.get("organisationOverview", {})
        """
    
    def fetch(self):
        updated_org = self.client.organisation(self.id())
        if updated_org is not None:
            self.dao.raw = updated_org.dao.raw
            self.paging = updated_org.paging
            return True
        return False

class OrganisationXMLDAO(NativeXMLDAO):

    overview_base = "/gtr:organisationOverview"
    
    url_xpath = overview_base + "/gtr:organisation/@url"
    id_xpath = overview_base + "/gtr:organisation/gtr:id"
    name_xpath = overview_base + "/gtr:organisation/gtr:name"

    def __init__(self, raw):
        super(OrganisationXMLDAO, self).__init__(raw)
    
    def url(self):
        return self._from_xpath(self.url_xpath)
    
    def id(self):
        return self._from_xpath(self.id_xpath)
        
    def name(self):
        return self._from_xpath(self.name_xpath)
    
class OrganisationJSONDAO(NativeJSONDAO):

    def __init__(self, raw):
        super(OrganisationJSONDAO, self).__init__(raw)
    
    def _overview(self):
        return self.raw.get("organisationOverview", {})
    
    def _org(self):
        return (self.raw.get("organisationOverview", {})
                        .get("organisation", {}))
    
    def url(self):
        return self._org().get("url")
    
    def id(self):
        return self._org().get("id")
        
    def name(self):
        return self._org().get("name")
        
    def projects(self, client):
        return [Project(client, {"projectOverview" : {"project" : data}})
                        for data in self._overview().get("project", [])]
                        
    def add_projects(self, projects):
        project_raw = [p.dao.raw['projectOverview']['project'] for p in projects]
        self.raw['organisationOverview']['project'] += project_raw
        

## ------- End Organisation ---------- ##

## -------- Person -------------- ##

class Person(Native):

    def __init__(self, client, raw, dao=None):
        super(Person, self).__init__(client)
        self.dao = dao if dao is not None else client.factory.person(client, raw)

    def url(self): return self.dao.url()
    def id(self): return self.dao.id()
    
    def isPI(self): 
        pr = self.dao.get_project_roles()
        pi = self.dao.principal_investigator()
        return pi and "PRINCIPAL_INVESTIGATOR" in pr
        
    def isCI(self):
        pr = self.dao.get_project_roles()
        ci = self.dao.co_investigator()
        return ci and "CO_INVESTIGATOR" in pr
    
    def projects(self): return self.dao.projects(self.client)
    
    def fetch(self):
        """ will flesh this item out with full data from the API - this WILL lose relation information from the parent object """
        updated_person = self.client.person(self.id())
        if updated_person is not None:
            self.dao.raw = updated_person.dao.raw
            return True
        return False
        
    def get_full(self):
        """ will return a full person object from the API """
        return self.client.person(self.id())

class PersonXMLDAO(NativeXMLDAO):

    overview_base = "/gtr:personOverview"
    person_base = overview_base + "/gtr:person"

    url_xpath = person_base + "/@url"    
    id_xpath = person_base + "/gtr:id"
    projects_xpath = overview_base + "/gtr:projectCompositions/gtr:projectComposition"
    
    project_wrapper = "projectOverview"

    def __init__(self, raw):
        super(PersonXMLDAO, self).__init__(raw)

    def url(self):
        return self._from_xpath(self.url_xpath)

    def id(self):
        return self._from_xpath(self.id_xpath)
            
    def projects(self, client):
        raws = self._do_xpath(self.projects_xpath)
        return [Project(client, self._wrap(raw, self.project_wrapper)) for raw in raws]
        
class PersonJSONDAO(NativeJSONDAO):

    def __init__(self, raw):
        super(PersonJSONDAO, self).__init__(raw)
    
    def _person(self):
        return self.raw.get("person", {})
    
    def url(self):
        return self._person().get("url")
    
    def id(self):
        return self._person().get("id")
    
    def get_project_roles(self):
        return self._person().get("projectRole", [])
    
    def principal_investigator(self):
        return self._person().get("principalInvestigator", False)
        
    def co_investigator(self):
        return self._person().get("coInvestigator", False)
    
    def projects(self, client):
        return [Project(client, {"projectOverview" : {"project" : data}})
                        for data in self._overview().get("projectComposition", [])]

## --------- End Person ----------- ##

## -------- Publication ----------- ##

class Publication(Native):
    def __init__(self, client, raw, dao=None):
        super(Publication, self).__init__(client)
        self.dao = dao if dao is not None else client.factory.publication(client, raw)
    
    def url(self): return self.dao.url()
    def id(self): return self.dao.id()
    def title(self): return self.dao.title()
    
    def fetch(self):
        updated_pub = self.client.publication(self.id())
        if updated_pub is not None:
            self.dao.raw = updated_pub.dao.raw
            return True
        return False

class PublicationXMLDAO(NativeXMLDAO):
    overview_base = "/gtr:publicationOverview"
    publication_base = overview_base + "/gtr:publication"
    
    url_xpath = publication_base + "/@url"
    id_xpath = publication_base + "/gtr:id"
    title_xpath = publication_base + "/gtr:title"
    
    def __init__(self, raw):
        super(PublicationXMLDAO, self).__init__(raw)
    
    def url(self):
        return self._from_xpath(self.url_xpath)
    
    def id(self):
        return self._from_xpath(self.id_xpath)
        
    def title(self):
        return self._from_xpath(self.title_xpath)
    
class PublicationJSONDAO(NativeJSONDAO):
    def __init__(self, raw):
        super(PublicationJSONDAO, self).__init__(raw)
    
    def _publication(self):
        return self.raw.get("publication", {})
    
    def url(self):
        return self._publication().get("url")
    
    def id(self):
        return self._publication().get("id")
        
    def title(self):
        return self._publication().get("title")
        
## ---------- End Publication -------- ##





