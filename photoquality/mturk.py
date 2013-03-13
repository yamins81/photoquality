from string import Template

import json

from .utils import tr_events
from .datasets import TechRehearsalImages

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
import boto.mturk.qualification as qual

from .utils import tr_events
from .mturk_templates import (html_template_all,
                              html_template_all_2,
                              js_template)

import numpy as np

class Template1(Template):
    delimiter = '%'


def register_hit_type(credentials, host='mechanicalturk.sandbox.amazonaws.com'):
    conn = MTurkConnection(*credentials, host=host)
    q = qual.Qualifications()
    q.add(qual.NumberHitsApprovedRequirement('GreaterThanOrEqualTo', 50))
    q.add(qual.PercentAssignmentsApprovedRequirement('GreaterThanOrEqualTo', 80))
    reward = conn.get_price_as_price(0.15)
    title = 'Photoquality'
    description = "Photoquality Assesments"
    duration = 60*60
    approval_delay = 240*60
    keywords = ['photograph quality', 'image quality', 'ranking', 'photography', 'images', 'image cognition', 'vision']
    return conn.register_hit_type(title, description, reward, duration, 
                    keywords=keywords, approval_delay=approval_delay, qual_req=q)


#ht = '28U4IXKO2L92OXJ0GJO31OCCFM2DCS'
#ht = '2HQULRGNTBJ3T5K1BSG7Q62KHXZ7TC'
#ht = '2WC51Y7QEOZF59Z5I5KMRFXRDEUDG2'
#ht = u'2UF25L8I9NZWD0L3C154TW7T8SYTJ4'
#ht = '2CZ6RLPHIT3H2FHZQVX2UJQ21CDH9F'
#ht = 2NLVQ8H88MQUD4CSH83I8RXX4FU8RF
#ht = 2ZZ2NJQ2172ZGSXLCOBLJVEBU6DXPI'
#ht = 27XJ3NAB6BFMMYV24VK10JFDGJ9GTL


NUM_IMAGES = 2
NUM_GROUPS = 1000
GROUP_SIZE = 100


def run(ht, credentials, host='mechanicalturk.sandbox.amazonaws.com'):
    conn = MTurkConnection(*credentials, host=host)
    global tr_events
    tr_events = np.array(tr_events) 
    for e in tr_events[[9]]:
        NS = NUM_GROUPS/GROUP_SIZE
        for ns in range(NS)[-2:]:
            e = e.replace(' ', '_').lower()
            event_url = "http://web.mit.edu/yamins/www/pq/mturk_pq_%s_%d.html" % (e, ns)
            q = ExternalQuestion(external_url=event_url, frame_height=800)
            create_hit_rs = conn.create_hit(hit_type=ht,
                                            question=q, 
                                            max_assignments=15,
                                            annotation='%s_%d' % (e, ns))
            assert(create_hit_rs.status == True)


def make_html_files():
    if NUM_IMAGES == 2:
        html_template = html_template_all_2
    else:
        html_template = html_template_all
    NS = NUM_GROUPS/GROUP_SIZE
    for ns in range(NS):
        for e in tr_events:
            e = e.replace(' ', '_').lower()
            jspath = '%s_subsets_%d.js' % (e, ns)
            d = Template1(html_template).substitute(JSPATH=jspath,
                                                NUMIMAGES=NUM_IMAGES,
                                                NUMGROUPS=GROUP_SIZE)
            outfile = "mturk_pq_%s_%d.html" % (e, ns)
            with open(outfile, 'w') as f:
                f.write(d)


def make_js_files(credentials):
    dataset = TechRehearsalImages(credentials)
    NS = NUM_GROUPS/GROUP_SIZE
    subsets = dataset.get_subsets(NUM_IMAGES, NUM_GROUPS)
    for ns in range(NS):
        for e in tr_events:
            ss = subsets[e][GROUP_SIZE*ns: GROUP_SIZE*(ns + 1)]
            el = e.replace(' ', '_').lower()
            d = js_template % json.dumps(ss)
            outfile = "%s_subsets_%d.js" % (el, ns)
            with open(outfile, 'w') as f:
                f.write(d)
