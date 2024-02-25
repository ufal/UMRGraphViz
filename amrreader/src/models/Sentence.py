'''
 UMR Sentence Object
'''

import logging

class Sentence(object):
    def __init__(self, sentid='', sent='', sent_info='',
                 raw_umr='', sent_umr='', align_info=None,
                 amr_nodes=dict(), graph=list()):
        self.sentid = sentid         # Sentence id
        self.sent = sent             # Sentence
        self.tokens = sent.split(" ") # Sentence as a list of tokens
        self.sent_info = sent_info   # Sent info block
        self.raw_umr = raw_umr       # Full raw UMR
        self.sent_umr = sent_umr     # Sent part of UMR
        self.amr_nodes = amr_nodes   # AMR ndoes table
        self.aligned_text = self._aligned_token_idx_to_text(align_info, self.tokens) # node-token alignmnent
        self.graph = graph           # Path of the whole graph
        self.amr_paths = dict()      # AMR paths
        self.named_entities = dict() # Named entities

    def _aligned_token_idx_to_text(self, align_info, tokens):
        aligned_text = {}
        for line in align_info:
            var, token_range_str = line.split(":")
            aligned_tokens = []
            for range_str in token_range_str.split(","):
                range_elems = range_str.strip().split("-", 2)
                # skip "-1--1" alignments
                if len(range_elems) > 2:
                    continue
                range_elems = [int(elem_str) for elem_str in range_elems]
                # skip "0-0" alignments
                if not range_elems[0]:
                    continue
                # warn if descending range
                if range_elems[0] > range_elems[1]:
                    logging.warn(f"Descending alignment range, skipping: {line}")
                    continue
                # warn if the end is out of range
                if range_elems[1] > len(tokens):
                    logging.warn(f"Alignment range out of scope (tokens = {len(tokens)}), skipping: {line}")
                    continue
                aligned_tokens.extend(tokens[range_elems[0]-1:range_elems[1]])
            aligned_text[var] = " ".join(aligned_tokens)
        return aligned_text

    def __str__(self):
        return '%s%s\n' % (self.sent_info, self.sent_umr)
