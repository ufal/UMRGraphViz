'''
 AMR Node Object
'''

class Node(object):
    def __init__(self, name='', ful_name='', next_nodes=[], edge_label='',
                 wikititle=None, wikiid=None,
                 is_entity=False, entity_type='', entity_name=None,
                 polarity=False, content='', attrs={}):
        self.set_all(name, ful_name, next_nodes, edge_label,
                    wikititle, wikiid,
                    is_entity, entity_type, entity_name,
                    polarity, content, attrs)

    def set_all(self, name='', ful_name='', next_nodes=[], edge_label='',
                 wikititle=None, wikiid=None,
                 is_entity=False, entity_type='', entity_name=None,
                 polarity=False, content='', attrs={}):
        self.name = name               # Node name (acronym)
        self.ful_name = ful_name       # Full name of the node
        self.next_nodes = next_nodes   # Next nodes (list)
        self.edge_label = edge_label   # Edge label between two nodes
        self.wikititle = wikititle     # Entity Wikipedia title
        self.wikiid = wikiid           # Entity WikiData ID
        self.is_entity = is_entity     # Whether the node is named entity
        self.entity_type = entity_type # Entity type
        self.entity_name = entity_name # Entity name
        self.polarity = polarity       # Whether the node is polarity
        self.content = content         # Original content
        self.attrs = attrs             # Key:Value attributes
        return

    def __str__(self):
        s = ""
        if not self.ful_name:
            s += f"NODE NAME: {self.name}\n"
        else:
            s += f"NODE NAME: {self.name} / {self.ful_name}\n"

        if self.wikititle or self.wikiid:
            s += f"WIKI: {self.wikititle or 'unk'} (ID={self.wikiid or 'unk'})\n"

        if self.is_entity:
            s += f"ENTITY TYPE: {self.entity_type}\n"
            s += f"ENTITY NAME: {self.entity_name}\n"

        s += f"POLARITY: {self.polarity}\n"

        for k,v in self.attrs.items():
            s += f"ATTRS/{k}: {v}\n"

        s += 'LINK TO:\n'
        for i in self.next_nodes:
            if not i.ful_name:
                s += f"\t({i.edge_label}) -> {i.name}\n"
            else:
                s += f"\t({i.edge_label}) -> {i.name} / {i.ful_name}\n"
        return s

