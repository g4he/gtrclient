import requests, urlparse
from lxml import etree
from copy import deepcopy

class GtRNative(object):
    
    def __init__(self, base_url, page_size=25, username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.page_size = self._constrain_page_size(page_size)
        
        self.project_base = self.base_url + "/project/"
        self.org_base = self.base_url + "/organisation/"
        self.person_base = self.base_url + "/person/"
        self.publication_base = self.base_url + "/publication/"
    
    def _get_xml(self, url):
        headers = {"Accept" : "application/xml"}
        resp = None
        
        if self.username is None:
            resp = requests.get(url, headers=headers)
        else:
            resp = requests.get(url, headers=headers, auth=(self.username, self.password))
        xml = None
        
        if resp is not None and resp.status_code == 200:
            xml = etree.fromstring(resp.text.encode("utf-8"))
        
        paging = self._extract_paging(resp)
        return xml, paging
    
    def _extract_paging(self, resp):
        try:
            record_count = int(resp.headers.get("link-records"))
        except (ValueError, TypeError):
            record_count = None
        try:
            pages = int(resp.headers.get("link-pages"))
        except (ValueError, TypeError):
            pages = None
        
        link_header = resp.headers.get("link")
        
        if record_count is None or pages is None or link_header is None:
            return None
        
        bits = [tuple(p.split(";")) for p in link_header.split(",")]
        fpnl = [None]*4
        for bit in bits:
            if bit[1].strip() == "rel=first":
                fpnl[0] = bit[0].strip()[1:-1]
            elif bit[1].strip() == "rel=previous":
                fpnl[1] = bit[0].strip()[1:-1]
            elif bit[1].strip() == "rel=next":
                fpnl[2] = bit[0].strip()[1:-1]
            elif bit[1].strip() == "rel=last":
                fpnl[3] = bit[0].strip()[1:-1]
        
        return Paging(record_count, pages, fpnl[0], fpnl[1], fpnl[2], fpnl[3])
    
    def _set_page_size(self, url, page_size=None):
        if "?" not in url:
            url += "?"
        else:
            url += "&"
        if "fetchSize" not in url:
            url += "fetchSize=" + (str(self.page_size) if page_size is None else str(page_size))
        return url
    
    def _set_page_number(self, url, page_no):
        if page_no is None:
            return url
        if "?" not in url:
            url += "?"
        else:
            url += "&"
        if "page" not in url:
            url += "page=" + str(page_no)
        return url
    
    def _constrain_page_size(self, page_size):
        if page_size is None:
            return None
        if page_size < 25:
            return 25
        if page_size > 100:
            return 100
        return page_size
    
    def projects(self, page=None, page_size=None):
        page_size = self._constrain_page_size(page_size)
        url = self.project_base
        if page is not None:
            url = self._set_page_number(self.project_base, page)
        xml, paging = self._get_xml(self._set_page_size(url, page_size))
        return Projects(self, xml, paging)
    
    def search(self, term):
        pass
        
    def get_project(self, uuid):
        raw, paging = self._get_xml(self.project_base + uuid)
        return Project(self, raw)

    def get_organisation(self, uuid):
        raw, paging = self._get_xml(self.org_base + uuid)
        return Organisation(self, raw, paging)
        
    def get_person(self, uuid):
        raw, paging = self._get_xml(self.person_base + uuid)
        return Person(self, raw)

    def get_publication(self, uuid):
        raw, paging = self._get_xml(self.publication_base + uuid)
        return Publication(self, raw)

class Paging(object):
    def __init__(self, record_count, pages, first, previous, next, last):
        self.record_count = record_count
        self.pages = pages
        self.first = first
        self.previous = previous
        self.next = next
        self.last = last
        
    def current_page(self):
        # oddly, we have to work this out by looking at the previous and next pages
        if self.previous is None or self.previous == "":
            return 1
        if self.next is None or self.next == "":
            return self.pages
        
        prev = self._extract_args(self.previous)
        prev_page = prev.get('page', [])
        try:
            if len(prev_page) == 1:
                return int(prev_page[0]) + 1
        except (ValueError, TypeError):
            pass
        
        n = self._extract_args(self.next)
        next_page = next.get('page', [])
        try:
            if len(next_page) == 1:
                return int(next_page[0]) - 1
        except (ValueError, TypeError):
            pass
        
        return -1
        
    def _extract_args(self, page_url):
        url = urlparse.urlparse(page_url)
        return urlparse.parse_qs(url.query)
    
    def current_page_size(self):
        try:
            if self.first is not None and self.first != "":
                args = self._extract_args(self.first)
                fetch_size = args.get("fetchSize", [])
                if len(fetch_size) == 1:
                    return int(fetch_size[0])
        except (ValueError, TypeError):
            pass
        return -1

class Native(object):
    def __init__(self, client, raw, paging=None):
        self.client = client
        self.raw = raw
        self.paging = paging
    
    # FIXME: all of these methods belong in another Paged class
    # which paged objects inherit from - do that at first refactor
    def record_count(self):
        if self.paging is not None:    
            return self.paging.record_count
        return 1
    
    def pages(self):
        if self.paging is not None:
            return self.paging.pages
        return 1
        
    def next_page(self):
        if self.paging is None:
            return False
        if self.paging.next is None or self.paging.next == "":
            return False
        xml, paging = self.client._get_xml(self.paging.next)
        self.raw = xml
        self.paging = paging
        return True
    
    def previous_page(self):
        if self.paging is None:
            return False
        if self.paging.previous is None or self.paging.previous == "":
            return False
        xml, paging = self.client._get_xml(self.paging.previous)
        self.raw = xml
        self.paging = paging
        return True
        
    def first_page(self):
        if self.paging is None:
            return False
        if self.paging.first is None or self.paging.first == "":
            return False
        xml, paging = self.client._get_xml(self.paging.first)
        self.raw = xml
        self.paging = paging
        return True
        
    def last_page(self):
        if self.paging is None:
            return False
        if self.paging.last is None or self.paging.last == "":
            return False
        xml, paging = self.client._get_xml(self.paging.last)
        self.raw = xml
        self.paging = paging
        return True
        
    def skip_to_page(self, page_no):
        if self.paging is None:
            return False
        if self.page_no > self.paging.pages:
            return False
        if self.page_no < 1:
            return False
        
        
    def current_page(self):
        if self.paging is not None:
            return self.paging.current_page()
        return -1
        
    def current_page_size(self):
        if self.paging is not None:
            return self.paging.current_page_size()
        return -1
    ## end paging methods ##
    
    def _from_xpath(self, xp):
        els = self.raw.xpath(xp, namespaces={"gtr" : "http://gtr.rcuk.ac.uk/api"})
        if els is not None and len(els) > 0:
            return els[0].text
        return None
    
    def _get_subs(self, parent_xpath, siblings=()):
        os = []
        for org in self.raw.xpath(parent_xpath, namespaces={"gtr" : "http://gtr.rcuk.ac.uk/api"}):
            sibs = []
            for sib in siblings:
                els = org.xpath(sib, namespaces={"gtr" : "http://gtr.rcuk.ac.uk/api"})
                val = None
                if els is not None and len(els) > 0:
                    val = els[0].text
                    sibs.append(val)
            os.append(tuple(sibs))
        return os
    
    def _do_xpath(self, xp):
        return self.raw.xpath(xp, namespaces={"gtr" : "http://gtr.rcuk.ac.uk/api"})
    
    def _port(self, xp, new_root):
        ports = []
        for el in self.raw.xpath(xp, namespaces={"gtr" : "http://gtr.rcuk.ac.uk/api"}): 
            root = etree.Element("{http://gtr.rcuk.ac.uk/api}" + new_root, nsmap={"gtr" : "http://gtr.rcuk.ac.uk/api"})
            for child in el:
                root.append(deepcopy(child))
            ports.append(root)
        return ports
    
    def _wrap(self, element, wrapper, clone=True):
        root = etree.Element("{http://gtr.rcuk.ac.uk/api}" + wrapper, nsmap={"gtr" : "http://gtr.rcuk.ac.uk/api"})
        if clone:
            element = deepcopy(element)
        root.append(element)
        return root
    
    def xml(self):
        return etree.tostring(self.raw, pretty_print=True)

class Person(Native):
    def id(self):
        return self._from_xpath("/gtr:personOverview/gtr:person/gtr:id")
        
    def name(self):
        return self._from_xpath("/gtr:personOverview/gtr:person/gtr:name")
            
    def projects(self):
        raws = self._do_xpath("/gtr:personOverview/gtr:projectCompositions/gtr:projectComposition")
        return [Project(self.client, self._wrap(raw, "projectOverview")) for raw in raws]
        
    def fetch(self):
        updated_person = self.client.get_person(self.id())
        self.raw = updated_person.raw
        self.paging = updated_person.paging

class Organisation(Native):
    def id(self):
        return self._from_xpath("/gtr:organisationOverview/gtr:organisation/gtr:id")
        
    def name(self):
        return self._from_xpath("/gtr:organisationOverview/gtr:organisation/gtr:name")
    
    def fetch(self):
        updated_org = self.client.get_organisation(self.id())
        self.raw = updated_org.raw
        self.paging = updated_org.paging

class Projects(Native):

    def projects(self):
        raws = self._do_xpath("/gtr:projects/gtr:project")
        return [Project(self.client, self._wrap(self._wrap(raw, "projectComposition"), "projectOverview")) for raw in raws]
    
    def __iter__(self):
        return self.iterator()
    
    def iterator(self, reset_pages=True, stop_at_page_boundary=False):
        if reset_pages:
            self.first_page()
        def f():
            while True:
                projects = self.projects()
                for p in projects:
                    yield p
                if stop_at_page_boundary:
                    break
                if not self.next_page():
                    break
        return f()

class Project(Native):
    def id(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:id")

    def title(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:title")
    
    def start(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:fund/gtr:start")
    
    def status(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:status")
    
    def end(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:fund/gtr:end")
    
    def abstract(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:abstractText")
    
    def funder(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:fund/gtr:funder/gtr:name")
    
    def value(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:fund/gtr:valuePounds")
    
    def category(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:grantCategory")
    
    def reference(self):
        return self._from_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:project/gtr:grantReference")
    
    def lead(self):
        raws = self._port("/gtr:projectOverview/gtr:projectComposition/gtr:leadResearchOrganisation", "organisation")
        return [Organisation(self.client, self._wrap(raw, "organisationOverview")) for raw in raws]
        
    def orgs(self):
        raws = self._do_xpath("/gtr:projectOverview/gtr:projectComposition/gtr:organisations/gtr:organisation")
        return [Organisation(self.client, self._wrap(raw, "organisationOverview")) for raw in raws]
        
    def people(self):
        raws = self._port("/gtr:projectOverview/gtr:projectComposition/gtr:projectPeople/gtr:projectPerson", "person")
        return [Person(self.client, self._wrap(raw, "personOverview")) for raw in raws]
    
    def collaborators(self):
        raws = self._port("/gtr:projectOverview/gtr:projectComposition/gtr:collaborations/gtr:collaborator", "organisation")
        return [Organisation(self.client, self._wrap(raw, "organisationOverview")) for raw in raws]
    
    def collaboration_outputs(self):
        pass
    
    def intellectual_property_outputs(self):
        pass
        
    def policy_influence_outputs(self):
        pass
        
    def product_outputs(self):
        pass
        
    def research_material_outputs(self):
        pass
        
    def publications(self):
        pass
    
    def fetch(self):
        updated_proj = self.client.get_project(self.id())
        self.raw = updated_proj.raw
        self.paging = updated_proj.paging
