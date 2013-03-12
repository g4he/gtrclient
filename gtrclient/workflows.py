import logging, time
import gtr

log = logging.getLogger(__name__)

def crawl(base_url, username=None, password=None, 
            project_callback=None, person_callback=None, organisation_callback=None, publication_callback=None,
            project_limit=None, person_limit=None, organisation_limit=None, publication_limit=None,
            min_request_gap=0):
    # create a client which crawls json at 100 records per page
    client = gtr.GtRNative(base_url, page_size=100, serialisation="json", username=username, password=password)
    
    # do projects
    projects = client.projects()
    _mine(projects, project_limit, project_callback, "project", min_request_gap)
    
    # do people
    people = client.people()
    _mine(people, person_limit, person_callback, "person", min_request_gap)
    
    # do organisations
    organisations = client.organisations()
    _mine(organisations, organisation_limit, organisation_callback, "organisation", min_request_gap)
    
    # do publications
    publications = client.publications()
    _mine(publications, publication_limit, publication_callback, "publication", min_request_gap)
                
def _mine(iterable, limit, callback, name, min_request_gap=0, fetch=True):
    if limit == 0:
        return
    
    if callback is None:
        return
        
    count = 0
    for p in iterable:
        start = time.time()
        
        count += 1
        if limit is not None and count > limit:
            break
        
        if fetch:
            if not p.fetch():
                log.info("skipping " + str(name) + " " + str(p.id()) + " (" + str(count) + " of " + str(len(iterable)) + ")")
                continue
        
        log.info("processing " + str(name) + " " + str(p.id()) + " (" + str(count) + " of " + str(len(iterable)) + ")")
        callback(p)
        
        end = time.time()
        diff = end - start
        if diff < min_request_gap:
            wait = min_request_gap - diff
            log.debug("sleeping for " + str(wait) + "s")
            time.sleep(wait)
