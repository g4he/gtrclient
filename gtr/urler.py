import urlparse, urllib

def set_query_param(url, param, value):
    urld = URL(url)
    urld.set_query_param(param, value)
    return urld.url()

def get_query_param(url, param):
    urld = URL(url)
    return urld.get_query_param(param)

class URL(object):
    def __init__(self, url):
        self.parsed_url = urlparse.urlparse(url)
    
    def add_query_param(self, param, value):
        tuples = urlparse.parse_qsl(self.parsed_url.query)
        tuples.append((param, value))
        new_query = urllib.urlencode(tuples)
        self._patch(new_query=new_query)
    
    def set_query_param(self, param, value):
        tuples = urlparse.parse_qsl(self.parsed_url.query)
        stripped = [(k,v) for k,v in tuples if k != param]
        stripped.append((param, value))
        new_query = urllib.urlencode(stripped)
        self._patch(new_query=new_query)
    
    def get_query_param(self, param, allow_list_response=False):
        d = urlparse.parse_qs(self.parsed_url.query)
        vs = d.get(param, [])
        if allow_list_response:
            return vs
        if len(vs) > 0:
            return vs[0]
    
    def url(self):
        return urlparse.urlunparse(self.parsed_url)
    
    def _patch(self, new_query=None):
        scheme, netloc, path, params, query, fragment = self.parsed_url
        if new_query is not None:
            query = new_query
        url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
        self.parsed_url = urlparse.urlparse(url)
    
    def __str__(self):
        return self.url()
        
    def __repr__(self):
        return self.url()
        
