'''
 UMR Sentence Object
'''

class Sentence(object):
    def __init__(self, sentid='', sent='', raw_umr='',
                 sent_umr='', comments=[],
                 amr_nodes=dict(), graph=list()):
        self.sentid = sentid         # Sentence id
        self.sent = sent             # Sentence
        self.raw_umr = raw_umr       # Full raw UMR
        self.comments = comments     # Comments
        self.sent_umr = sent_umr     # Sent part of UMR
        self.amr_nodes = amr_nodes   # AMR ndoes table
        self.graph = graph           # Path of the whole graph
        self.amr_paths = dict()      # AMR paths
        self.named_entities = dict() # Named entities

    def __str__(self):
        return '%s%s\n' % (self.comments, self.sent_umr)
