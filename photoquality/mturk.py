from string import Template

import json

from .utils import tr_events
from .datasets import TechRehearsalImages

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
import boto.mturk.qualification as qual

from .utils import tr_events
from .mturk_templates import (html_template, js_template)


class Template1(Template):
    delimiter = '%'


def register_hit_type(credentials):
    if credentials is not None:
        conn = MTurkConnection(*credentials, host='mechanicalturk.sandbox.amazonaws.com')
    else:
        conn = MTurkConnection(host='mechanicalturk.sandbox.amazonaws.com')

    q = qual.Qualifications()
    q.add(qual.NumberHitsApprovedRequirement('GreaterThanOrEqualTo', 50))
    q.add(qual.PercentAssignmentsApprovedRequirement('GreaterThanOrEqualTo', 80))
    reward = conn.get_price_as_price(0.05)
    title = 'Photoquality_TR'
    description = "Test Description of Photoquality"
    duration = 60*60
    approval_delay = 60*60
    keywords = ['photoquality', 'test']
    return conn.register_hit_type(title, description, reward, duration, 
                    keywords=keywords, approval_delay=approval_delay, qual_req=q)


def run(credentials=None):
    if credentials is not None:
        conn = MTurkConnection(*credentials, host='mechanicalturk.sandbox.amazonaws.com')
    else:
        conn = MTurkConnection(host='mechanicalturk.sandbox.amazonaws.com')
    for e in tr_events:
        e = e.replace(' ', '_')
        event_url = "http://web.mit.edu/yamins/www/mturk_pq_%s.html" % e
        q = ExternalQuestion(external_url=event_url, frame_height=800)
        create_hit_rs = conn.create_hit(hit_type='28U4IXKO2L92OXJ0GJO31OCCFM2DCS',
                                        question=q, 
                                        lifetime=60*65,
                                        max_assignments=100,
                                        annotation=e)
        assert(create_hit_rs.status == True)


def make_html_files():
    numImages = 4
    for e in tr_events:
        e = e.replace(' ', '_').lower()
        d = Template1(html_template).substitute(JSPATH=e, NUMIMAGES=numImages)
        outfile = "mturk_pq_%s.html" % e
        with open(outfile, 'w') as f:
            f.write(d)


def make_js_files(credentials):
    dataset = TechRehearsalImages(credentials)
    subsets = dataset.get_subsets(4, 250)
    for e in tr_events:
        el = e.replace(' ', '_').lower()
        d = js_template % json.dumps(subsets[e])
        outfile = "%s_subsets.js" % el
        with open(outfile, 'w') as f:
            f.write(d)
