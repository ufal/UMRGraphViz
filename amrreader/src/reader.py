import sys
sys.setrecursionlimit(10000)
import os
import re
import copy
import urllib.parse
import uuid

from .models.Node import Node
from .models.Sentence import Sentence


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
        amr_nodes_acronym[acr] = None

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
        if role == ':wiki':
            continue
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

    # Node is a named entity
    names = re.findall(':op\d\s\"\S+\"', content)
    if len(names) > 0:
        entity_name = ''
        for i in names:
            entity_name += re.match(':op\d\s\"(\S+)\"', i).group(1) + ' '
        entity_name = urllib.parse.unquote_plus(entity_name.strip())
        new_node = Node(name=acr, ful_name=ful, next_nodes=arg_nodes,
                        entity_name=entity_name,
                        polarity=is_polarity, content=content, attrs=attrs)
        amr_nodes_content[content] = new_node
        amr_nodes_acronym[acr] = new_node
    else:
        new_node = Node(name=acr, ful_name=ful, next_nodes=arg_nodes,
                        polarity=is_polarity, content=content, attrs=attrs)
        amr_nodes_content[content] = new_node
        amr_nodes_acronym[acr] = new_node


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
            role = re.search(':\S+\s', content[s:e]).group() # Edge label
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
        if role == ':wiki' and is_named_entity:
            continue
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

        # Named entity is a special node, so the subtree of a
        # named entity will be merged. For example,
        #     (p / person :wiki -
        #        :name (n / name
        #                 :op1 "Pascale"))
        # will be merged as one node.
        # According to AMR Specification, "we fill the :instance
        # slot from a special list of standard AMR named entity types".
        # Thus, for named entity node, we will use entity type
        # (p / person in the example above) instead of :instance

    if is_named_entity:
        # Get Wikipedia title:
        if re.match('.+:wiki\s-.*', content):
            wikititle = '-' # Entity is NIL, Wiki title does not exist
        else:
            m = re.search(':wiki\s\"(.+?)\"', content)
            if m:
                wikititle = urllib.parse.unquote_plus(m.group(1)) # Wiki title
            else:
                wikititle = '' # There is no Wiki title information

        new_node = Node(name=acr, ful_name=ful, next_nodes=arg_nodes,
                        edge_label=ne.ful_name, is_entity=True,
                        entity_type=ful, entity_name=ne.entity_name,
                        wiki=wikititle, polarity=is_polarity, content=content, attrs=attrs)
        amr_nodes_content[_content] = new_node
        amr_nodes_acronym[acr] = new_node

    elif len(arg_nodes) > 0:
        new_node = Node(name=acr, ful_name=ful, next_nodes=arg_nodes,
                        polarity=is_polarity, content=content, attrs=attrs)
        amr_nodes_content[_content] = new_node
        amr_nodes_acronym[acr] = new_node


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
           re.search('^\#?\s*[Ss]entence:?\s+(.*)$', line)
    # TODO: parse sents in Arapaho
    sent = sent.group(1) if sent else None
    return sent

def extract_sentid(line):
    sentid = re.search('^\#?\s*::id (.*?)$', line) or \
             re.search('^\#?\s*::\s+([^\s]+)', line)
    sentid = sentid.group(1) if sentid else None
    return sentid

def detect_graph(line, stack_count):
    if stack_count is None:
        if not line.startswith('('):
            return None
        else:
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
    sentid, sent, raw_umr, sent_umr, doc_umr, comments = None, None, '', '', '', ''
    sent_stack_count, doc_stack_count = None, None
    curr_umr = ''
    for line in raw_amrs.split('\n'):

        # try to extract sentid
        # only if any bracketed graph is either not open yet (is None) or is already closed (=0)
        if not sent_stack_count and not doc_stack_count:
            l_sentid = extract_sentid(line)
            if l_sentid:
                if sentid:
                    amr_nodes_acronym, path = amr_reader(sent_umr)
                    sent_obj = Sentence(sentid, sent, raw_umr, comments, sent_umr,
                                    amr_nodes_acronym, path)
                    res.append(sent_obj)
                sentid, sent, raw_umr, sent_umr, doc_umr, comments = l_sentid, None, '', '', '', ''
                sent_stack_count, doc_stack_count = None, None

        # skip all lines until the first sentid is defined
        if not sentid:
            continue

        #print(sentid)

        raw_umr += line

        # try to extract sentence, if not already set
        # only if any bracketed graph is either not open yet (is None) or is already closed (=0)
        if not sent and not sent_stack_count and not doc_stack_count:
            sent = extract_sentence(line)

        if line.startswith('# '):
            comments += line
            continue

        # detect bracketed structure of a sent graph
        # sent_stack_count == 0 => full graph already parsed
        if sent_stack_count != 0:
            sent_stack_count = detect_graph(line, sent_stack_count)
            if sent_stack_count is None:
                continue
            sent_umr += line + "\n"
            if sent_stack_count > 0:
                continue

        # detect bracketed structure of a doc graph
        # doc_stack_count == 0 => full graph already parsed
        if doc_stack_count != 0:
            doc_stack_count = detect_graph(line, doc_stack_count)
            if doc_stack_count is None:
                continue
            doc_umr += line + "\n"
            if doc_stack_count > 0:
                continue

    if sentid:
        amr_nodes_acronym, path = amr_reader(sent_umr)
        sent_obj = Sentence(sentid, sent, raw_umr, comments, sent_umr,
                        amr_nodes_acronym, path)
        res.append(sent_obj)

    return res
