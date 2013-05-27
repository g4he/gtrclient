import logging, time
import native, cerif

log = logging.getLogger(__name__)

def crawl(base_url, username=None, password=None, min_request_gap=0,
            project_callback=None, project_limit=None, pass_cerif_project=False,
            person_callback=None, person_limit=None, 
            organisation_callback=None, organisation_limit=None, 
            publication_callback=None, publication_limit=None):
    
    # create a client which crawls json at 100 records per page
    client = native.GtRNative(base_url, page_size=100, serialisation="json", username=username, password=password)
    cerif_client = cerif.GtRCerif(base_url, page_size=100, serialisation="json", username=username, password=password)
    
    # do projects
    if project_callback is not None and (project_limit > 0 or project_limit is None):
        projects = client.projects()
        _mine(projects, project_limit, project_callback, "project", min_request_gap, pass_cerif=pass_cerif_project, native_client=client, cerif_client=cerif_client)
    
    # do people
    if person_callback is not None and (person_limit > 0 or person_limit is None):
        people = client.people()
        _mine(people, person_limit, person_callback, "person", min_request_gap)
    
    # do organisations
    if organisation_callback is not None and (organisation_limit > 0 or organisation_limit is None):
        organisations = client.organisations()
        _mine(organisations, organisation_limit, organisation_callback, "organisation", min_request_gap, load_all_projects=True)
    
    # do publications
    if publication_callback is not None and (publication_limit > 0 or publication_limit is None):
        publications = client.publications()
        _mine(publications, publication_limit, publication_callback, "publication", min_request_gap)
                
def _mine(iterable, limit, callback, name, min_request_gap=0, fetch=True, load_all_projects=False, pass_cerif=False, native_client=None, cerif_client=None):
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
        
        if load_all_projects:
            log.info("loading all projects for this entity")
            p.load_all_projects()
        
        if pass_cerif:
            c = None
            if isinstance(p, native.Project):
                c = cerif_client.project(p.id())
            callback(p, c)
        else:
            callback(p)
        
        end = time.time()
        diff = end - start
        if diff < min_request_gap:
            wait = min_request_gap - diff
            log.debug("sleeping for " + str(wait) + "s")
            time.sleep(wait)
