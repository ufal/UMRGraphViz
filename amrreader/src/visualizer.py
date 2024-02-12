import re
import pygraphviz as pgv


def visualizer(sent, outdir, show_wiki=True):
    '''
    AMR visualizer
    Please install
      - graphviz
      - pygraphviz

    :param Sentence_object sent: input Sentence object
    :param str outdir: output dir
    :param bool show_wiki: visualize wiki title
    '''

    nodes = set()
    for i in sent.graph:
        nodes.add(i[0])
        nodes.add(i[1])

    # Draw nodes
    G = pgv.AGraph(strict=False, directed=True)
    for i in nodes:
        if i == '@': # Root
            continue
        node = sent.amr_nodes[i]
        pol = ''
        if node.polarity:
            pol = '\npolarity'
        if node.ful_name:
            # 1. Node is a named entity
            if node.is_entity:
                ne = sent.named_entities[node.name]
                if show_wiki:
                    ne_name = '%s\nwiki: %s' % (ne.entity_name, ne.wiki)
                else:
                    ne_name = '%s\n' % ne.entity_name
                G.add_node(i, shape='point', fillcolor='red')
                G.add_node(i + '#' + ne.subtype, shape='box', color='blue',
                           label=ne_name)
                G.add_edge(i, i + '#' + ne.subtype,
                           label=ne.subtype + pol)
            # 2. Node is an instance
            else:
                full_name = '%s' % node.ful_name
                G.add_node(i, shape='point', fillcolor='red')
                if re.match('\S+-\d+', full_name): # Node has sense tag
                    G.add_node(i + '#instance', shape='egg', color='orange',
                               label=full_name)
                else:
                    G.add_node(i + '#instance', shape='egg', color='green',
                               label=full_name)
                G.add_edge(i, i + '#instance', label='instance' + pol,
                           fontname='times italic')
        # 3. Node is a concept
        else:
            G.add_node(i, shape='ellipse', color='black')

    # Draw edge label
    for i in sent.graph:
        if i[0] == '@':
            continue
        G.add_edge(i[0], i[1], label=i[2], fontname='monospace')

    G.layout()
    G.layout(prog='dot')
    G.draw('%s/%s.png' % (outdir, sent.sentid))


def visualizer_curt(sen, outdir, show_wiki=True):
    '''
    AMR visualizer simplified graph
    Please install
      - graphviz
      - pygraphviz

    :param Sentence_object sent: input Sentence object
    :param str outdir: output dir
    :param bool show_wiki: visualize wiki title
    '''

    nodes = set()
    for i in sen.graph:
        nodes.add(i[0])
        nodes.add(i[1])

    # Draw nodes
    G = pgv.AGraph(strict=False, directed=True)
    for i in sorted(nodes):
        if i == '@': # Root
            continue
        node = sen.amr_nodes[i]
        if node.ful_name:
            label = '<<TABLE BORDER="0" CELLBORDER="0">'
            label += f'<TR><TD COLSPAN="2"><B>{node.ful_name}</B></TD></TR>'
            if node.is_entity:
                label += f'<TR><TD ALIGN="RIGHT">:name</TD><TD ALIGN="LEFT">{node.entity_name}</TD></TR>'
            if show_wiki and (node.wikititle or node.wikiid):
                wikilabel = f"{node.wikititle or 'unk'}"
                if node.wikiid:
                    wikilabel += f" <SUB>{node.wikiid}</SUB>"
                label += f'<TR><TD ALIGN="RIGHT">:wiki</TD><TD ALIGN="LEFT">{wikilabel}</TD></TR>'
            if node.polarity:
                label += '<TR><TD COLSPAN="2">- polarity</TD></TR>'
            for k,v in node.attrs.items():
                label += f'<TR><TD ALIGN="RIGHT">{k}</TD><TD ALIGN="LEFT">{v}</TD></TR>'
            label += '</TABLE>>'
            # 1. Node is a named entity
            if node.is_entity:
                G.add_node(i, shape='box', color='blue', label=label)
            # 2. Node is an instance
            else:
                if re.match('\S+-\d+', node.ful_name): # Node has sense tag
                    G.add_node(i, shape='egg', color='orange', label=label)
                else:
                    G.add_node(i, shape='egg', color='green', label=label)
        # 3. Node is a concept
        else:
            G.add_node(i, shape='ellipse', color='black')

    # Draw edge label
    for i in sen.graph:
        if i[0] == '@':
            continue
        G.add_edge(i[0], i[1], label=i[2], fontname='monospace')

    G.layout()
    G.layout(prog='dot')
    G.draw('%s/%s.png' % (outdir, sen.sentid))
