'''
 UMR Sentence Object
'''

class Sentence(object):
    def __init__(self, sentid='', sent='', sent_info='',
                 raw_umr='', sent_umr='',
                 amr_nodes=dict(), graph=list()):
        self.sentid = sentid         # Sentence id
        self.sent = sent             # Sentence
        self.sent_info = sent_info   # Sent info block
        self.raw_umr = raw_umr       # Full raw UMR
        self.sent_umr = sent_umr     # Sent part of UMR
        self.amr_nodes = amr_nodes   # AMR ndoes table
        self.graph = graph           # Path of the whole graph
        self.amr_paths = dict()      # AMR paths
        self.named_entities = dict() # Named entities

    def __str__(self):
        return '%s%s\n' % (self.sent_info, self.sent_umr)
