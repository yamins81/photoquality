from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion

from .utils import tr_events

def run(credentials=None):
    for e in tr_events:
        event_url = "http://web.mit.edu/yamins/www/mturk_pq_%s.html" % e
        q = ExternalQuestion(external_url=event_url, frame_height=800)
        if credentials is not None:
            conn = MTurkConnection(*credentials)
        else:
            conn = MTurkConnection()
        keywords=['boto', 'test', 'doctest']
        create_hit_rs = conn.create_hit(question=q, 
                                        lifetime=60*65,
                                        max_assignments=2,
                                        title="Boto External Question Test", 
                                        keywords=keywords,
                                        reward = 0.05,
                                        duration=60*6,
                                        approval_delay=60*60, 
                                        annotation=e)
        assert(create_hit_rs.status == True)

if __name__ == "__main__":
    test()