import requests, json
import urler

MIME_MAP = {"xml" : "application/xml", "json" : "application/json"}

class GtR(object):
    
    def __init__(self, base_url, page_size=25, serialisation="json", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.page_size = self._constrain_page_size(page_size)
        self.serialisation = serialisation if serialisation in ["xml", "json"] else "xml"
        self.mimetype = MIME_MAP.get(self.serialisation, "application/xml")
    
    def _api(self, rest_url, mimetype=None, page=None, page_size=None):
        accept = self.mimetype
        if mimetype is not None and mimetype in MIME_MAP.values():
            accept = mimetype
        headers = {"Accept" : accept}
        
        if page is not None:
            rest_url = urler.set_query_param(rest_url, "page", page)
        
        if page_size is not None:
            rest_url = urler.set_query_param(rest_url, "fetchSize", page_size)
        
        #print headers
        #print rest_url
        
        resp = None
        if self.username is None:
            resp = requests.get(rest_url, headers=headers)
        else:
            resp = requests.get(rest_url, headers=headers, auth=(self.username, self.password))
        
        #print resp
        #print resp.status_code
        
        if resp is None or resp.status_code != 200:
            return None, None # FIXME: maybe raise an exception?
        
        data = None
        if accept == "application/xml":
            data = etree.fromstring(resp.text.encode("utf-8"))
        elif accept == "application/json":
            data = json.loads(resp.text)
        
        paging = self._extract_paging(resp)
        return data, paging
    
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
    
    def _constrain_page_size(self, page_size):
        if page_size is None:
            return None
        if page_size < 25:
            return 25
        if page_size > 100:
            return 100
        return page_size
        
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
        # although the JSON serialisation does actually provide this as part of
        # the data, the XML serialisation does not, so this is suitably general
        if self.previous is None or self.previous == "":
            return 1
        if self.next is None or self.next == "":
            return self.pages
        
        prev_page = urler.get_query_param(self.previous, "page")
        try:
            return int(prev_page) + 1
        except (ValueError, TypeError):
            pass
        
        next_page = urler.get_query_param(self.next, "page")
        try:
            return int(next_page) - 1
        except (ValueError, TypeError):
            pass
        
        return -1
        
    def current_page_size(self):
        try:
            if self.first is not None and self.first != "":
                fetch_size = urler.get_query_param(self.first, "fetchSize")
                return int(fetch_size)
        except (ValueError, TypeError):
            pass
        return -1
