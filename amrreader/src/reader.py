import sys
sys.setrecursionlimit(10000)
import os
import re
import copy
import urllib.parse
import uuid
import logging

import requests

from .models.Node import Node
from .models.Sentence import Sentence

WIKIDATA_URL = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"

def split_amr(raw_amr, contents):
    '''
    Split raw AMR based on '()'

    :param str raw_amr:
    :param list contentss:
    '''
    if not raw_amr:
        return
    else:
        if raw_amr[0] == '(':
            contents.append([])
            for i in contents:
                i.append(raw_amr[0])
        elif raw_amr[0] == ')':
            for i in contents:
                i.append(raw_amr[0])
            amr_contents.append(''.join(contents[-1]))
            contents.pop(-1)
        else:
            for i in contents:
                i.append(raw_amr[0])
        raw_amr = raw_amr[1:]
        split_amr(raw_amr, contents)


def collect_acronyms(content, amr_nodes_acronym):
    predict_event = re.search('(\w+)\s*/\s\S+', content)
    if predict_event:
        acr = predict_event.group(1) # Acronym
        if acr not in amr_nodes_acronym:
            amr_nodes_acronym[acr] = Node(name=acr)

def extract_wiki(attrs):
    wikititle, wikiid = None, None
    if ":wiki" not in attrs:
        return wikititle, wikiid
    wikivalue = attrs.pop(":wiki")
    # wikidata ID strored
    wikivalue = wikivalue.rstrip('"').lstrip('"').strip()
    if not wikivalue:
        return wikititle, wikiid
    if re.match(r'[QPL]\d+', wikivalue):
        wikiid = wikivalue
        try:
            response = requests.get(WIKIDATA_URL, params={"ids": wikiid})
            data = response.json()
            wiki_labels = data["entities"][wikiid]["labels"]
            # English title as default
            if "en" in wiki_labels:
                wikititle = wiki_labels["en"]["value"]
            # any title otherwise
            elif wiki_labels:
                wikititle = list(wiki_labels.values())[0]
            wikititle = wikititle.replace(" ", "_")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error when retrieving data from WikiData for the id={wikiid}: {e}")
        except KeyError:
            logging.warning(f"Error when retrieving data from WikiData for the id={wikiid}: id does not exist")
    # wiki title stored or invalid format
    else:
        wikititle = urllib.parse.unquote_plus(wikivalue)
    return wikititle, wikiid

def extract_ne_name(content):
    names = re.findall(':op\d\s\"\S+\"', content)
    if not names:
        return
    entity_name = ''
    for i in names:
        entity_name += re.match(':op\d\s\"(\S+)\"', i).group(1) + ' '
    entity_name = urllib.parse.unquote_plus(entity_name.strip())
    return entity_name

def generate_node_single(content, amr_nodes_content, amr_nodes_acronym):
    '''
    Generate Node object for single '()'

    :param str context:
    :param dict amr_nodes_content: content as key
    :param dict amr_nodes_acronym: acronym as key
    '''
    try:
        assert content.count('(') == 1 and content.count(')') == 1
    except AssertionError:
        raise Exception('Unmatched parenthesis')

    predict_event = re.search('(\w+)\s*/\s(\S+)', content)
    if predict_event:
        acr = predict_event.group(1) # Acronym
        ful = predict_event.group(2).strip(')') # Full name
    else:
        acr, ful = '-', '-'

    # In case of :polarity -
    is_polarity = True if re.search(":polarity\s-", content) else False

    # :ARG nodes
    # keep in attrs if nodes is not an acronym
    attrs = {}
    arg_nodes = []
    nodes = re.findall(':\S+\s\S+', content)
    for i in nodes:
        i = re.search('(:\S+)\s(\S+)', i)
        role = i.group(1)
        concept = i.group(2).strip(')')
        if role == ':polarity':
            continue
        if concept in amr_nodes_acronym:
            if amr_nodes_acronym[concept] is None:
                continue
            node = copy.copy(amr_nodes_acronym[concept])
            node.next_nodes = []
        # In case of (d / date-entity :year 2012)
        else:
            attrs[role] = concept
            continue
        node.edge_label = role
        arg_nodes.append(node)

    # Node contains a wiki link
    wikititle, wikiid = extract_wiki(attrs)

    # Node is the name of a NE
    ne_name = extract_ne_name(content)

    new_node = amr_nodes_acronym[acr]
    new_node.set_all(name=acr, ful_name=ful, next_nodes=arg_nodes,
                    wikititle=wikititle, wikiid=wikiid, entity_name=ne_name,
                    polarity=is_polarity, content=content, attrs=attrs)
    amr_nodes_content[content] = new_node


def generate_nodes_multiple(content, amr_nodes_content, amr_nodes_acronym):
    '''
    Generate Node object for nested '()'

    :param str context:
    :param dict amr_nodes_content: content as key
    :param dict amr_nodes_acronym: acronym as key
    '''
    try:
        assert content.count('(') > 1 and content.count(')') > 1
        assert content.count('(') == content.count(')')
    except AssertionError:
        raise Exception('Unmatched parenthesis')

    _content = content
    arg_nodes = []
    is_named_entity = False

    # Remove existing nodes from the content, and link these nodes to the root
    # of the subtree
    for i in sorted(amr_nodes_content, key=len, reverse=True):
        if i in content:
            e = content.find(i)
            s = content[:e].rfind(':')
            role = re.search(':\S+\s*', content[s:e]).group() # Edge label
            content = content.replace(role+i, '', 1)
            amr_nodes_content[i].edge_label = role.strip()
            if ':name' in role:
                is_named_entity = True
                ne = amr_nodes_content[i]
            else:
                arg_nodes.append(amr_nodes_content[i])

    predict_event = re.search('(\w+)\s*/\s(\S+)', content)
    if predict_event:
        acr = predict_event.group(1) # Acronym
        ful = predict_event.group(2) # Full name
    else:
        acr, ful = '-', '-'

    #print(f"{acr} {ful}")

    # In case of :polarity -
    is_polarity = True if re.search(":polarity\s-", content) else False

    attrs = {}
    nodes = re.findall(':\S+\s\S+', content)
    for i in nodes:
        i = re.search('(:\S+)\s(\S+)', i)
        role = i.group(1)
        concept = i.group(2).strip(')')
        if role == ':polarity':
            continue
        if concept in amr_nodes_acronym:
            if amr_nodes_acronym[concept] is None:
                continue
            node = copy.copy(amr_nodes_acronym[concept])
            node.next_nodes = []
        # In case of (d / date-entity :year 2012)
        else:
            attrs[role] = concept
            continue
        node.edge_label = role
        arg_nodes.append(node)

    # Node contains a wiki link
    wikititle, wikiid = extract_wiki(attrs)

    # Named entity is a special node, so the subtree of a
    # named entity will be merged. For example,
    #     (p / person :wiki -
    #        :name (n / name
    #                 :op1 "Pascale"))
    # will be merged as one node.
    edge_label, entity_name, entity_type = None, None, None
    if is_named_entity:
        edge_label, entity_name, entity_type = ne.ful_name, ne.entity_name, ful

    # if a "multiple" node is not NE, it has to have some children
    assert is_named_entity or bool(arg_nodes), \
            f"Concept with embedded bracketing must be a NE or must have some children"

    new_node = amr_nodes_acronym[acr]
    amr_nodes_content[_content] = new_node
    new_node.set_all(name=acr, ful_name=ful, next_nodes=arg_nodes,
                    edge_label=edge_label,
                    wikititle=wikititle, wikiid=wikiid,
                    is_entity=is_named_entity, entity_type=entity_type, entity_name=entity_name,
                    polarity=is_polarity, content=content, attrs=attrs)


def revise_node(content, amr_nodes_content, amr_nodes_acronym):
    '''
    In case of single '()' contains multiple nodes
    e.x. (m / moment :poss p5)

    :param str context:
    :param dict amr_nodes_content: content as key
    :param dict amr_nodes_acronym: acronym as key
    '''
    m = re.search('\w+\s/\s\S+\s+(.+)', content.replace('\n', ''))
    if m and ' / name' not in content and ':polarity -' not in content:
        arg_nodes = []
        acr = re.search('\w+\s/\s\S+', content).group().split(' / ')[0]
        nodes = re.findall('\S+\s\".+\"|\S+\s\S+', m.group(1))
        attrs = {}
        for i in nodes:
            i = re.search('(:\S+)\s(.+)', i)
            role = i.group(1)
            concept = i.group(2).strip(')')
            if concept in amr_nodes_acronym:
                node = copy.copy(amr_nodes_acronym[concept])
                node.next_nodes = []
            else: # in case of (d / date-entity :year 2012)
                attrs[role] = concept
                continue
            node.edge_label = role
            arg_nodes.append(node)
        amr_nodes_acronym[acr].next_nodes = arg_nodes
        amr_nodes_content[content].next_nodes = arg_nodes


def retrieve_path(node, parent, path):
    '''
    Retrieve AMR nodes path

    :param Node_object node:
    :param str parent:
    :param list path:
    '''
    path.append((parent, node.name, node.edge_label))
    for i in node.next_nodes:
        retrieve_path(i, node.name, path)


def amr_reader(raw_amr):
    '''
    :param str raw_amr: input raw amr
    :return dict amr_nodes_acronym:
    :return list path:
    '''
    global amr_contents
    amr_contents = []
    amr_nodes_content = {} # Content as key
    amr_nodes_acronym = {} # Acronym as key
    path = [] # Nodes path

    split_amr(raw_amr, [])

    # collect acronyms
    for i in amr_contents:
        collect_acronyms(i, amr_nodes_acronym)

    for i in amr_contents:
        if i.count('(') == 1 and i.count(')') == 1:
            generate_node_single(i, amr_nodes_content, amr_nodes_acronym)
    for i in amr_contents:
        if i.count('(') > 1 and i.count(')') > 1:
            generate_nodes_multiple(i, amr_nodes_content, amr_nodes_acronym)
    for i in amr_contents:
        if i.count('(') == 1 and i.count(')') == 1:
            revise_node(i, amr_nodes_content, amr_nodes_acronym)

    # The longest node (entire AMR) should be the root
    root = amr_nodes_content[sorted(amr_nodes_content, key=len, reverse=True)[0]]
    retrieve_path(root, '@', path)

    return amr_nodes_acronym, path

def extract_sentence(line):
    sent = re.search('^\#?\s*::\s*[^\s]+\s*(.*)$', line) or \
           re.search('^\#?\s*[Ss]entence:?\s+(.*)$', line) or \
           re.search('^\#?\s*[Ww]ords:?\s+(.*)$', line) or \
           re.search('^\#?\s*tx:?\s+(.*)$', line)
    # TODO: parse sents in Arapaho
    sent = re.sub('\s+', ' ', sent.group(1)) if sent else None
    return sent

def extract_sentid(line):
    sentid = re.search('^\#?\s*::id (.*?)$', line) or \
             re.search('^\#?\s*::\s+([^\s]+)', line)
    sentid = sentid.group(1) if sentid else None
    return sentid

def detect_graph(line, stack_count):
    if stack_count is None:
        stack_count = 0
    for m in re.finditer("[()]", line):
        if m.group(0) == "(":
            stack_count += 1
        elif stack_count > 0:
            stack_count -= 1
        else:
            raise Exception("Incorrect bracketing in the UMR structure.")
    return stack_count

def main(raw_amrs):
    '''
    :param str raw_amrs: input raw amrs, separated by '\n'
    :return list res: Sentence objects
    '''
    res = []
    sentid, sent, sent_info = None, None, ''
    raw_umr, sent_umr, doc_umr = '', '', ''
    sent_stack_count, doc_stack_count = None, None
    sent_info_block = False
    for line in raw_amrs.split('\n'):

        # try to extract sentid
        # only if any bracketed graph is either not open yet (is None) or is already closed (=0)
        if not sent_stack_count and not doc_stack_count:
            l_sentid = extract_sentid(line)
            if l_sentid:
                if sentid and sent_umr:
                    amr_nodes_acronym, path = amr_reader(sent_umr)
                    sent_obj = Sentence(sentid, sent, sent_info, raw_umr, sent_umr,
                                    amr_nodes_acronym, path)
                    res.append(sent_obj)
                sentid, sent, sent_info = l_sentid, None, ''
                raw_umr, sent_umr, doc_umr = '', '', ''
                sent_stack_count, doc_stack_count = None, None
                sent_info_block = True

        # skip all lines until the first sentid is defined
        if not sentid:
            continue

        #print(sentid)

        raw_umr += line + "\n"

        # store the sentence info block
        if sent_info_block:
            if not line.rstrip():
                sent_info_block = False
                continue
            # try to extract sentence, if not already set
            if not sent:
                sent = extract_sentence(line)
            sent_info += line + "\n"

        # detect bracketed structure of a sent graph
        # skip if the sent graph hasn't started yet
        if sent_stack_count is None and not line.startswith('('):
            continue
        # sent_stack_count == 0 => full graph already parsed
        if sent_stack_count != 0:
            graph_line = re.sub('#.*', '', line)
            sent_stack_count = detect_graph(graph_line, sent_stack_count)
            sent_umr += graph_line + "\n"
            if sent_stack_count > 0:
                continue

        # detect bracketed structure of a doc graph
        # skip if the doc graph hasn't started yet
        if doc_stack_count is None and not line.startswith('('):
            continue
        # doc_stack_count == 0 => full graph already parsed
        if doc_stack_count != 0:
            graph_line = re.sub('#.*', '', line)
            doc_stack_count = detect_graph(graph_line, doc_stack_count)
            doc_umr += graph_line + "\n"
            if doc_stack_count > 0:
                continue

    if sentid and sent_umr:
        amr_nodes_acronym, path = amr_reader(sent_umr)
        sent_obj = Sentence(sentid, sent, sent_info, raw_umr, sent_umr,
                        amr_nodes_acronym, path)
        res.append(sent_obj)

    return res
