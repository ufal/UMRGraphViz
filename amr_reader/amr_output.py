import os

'''
 html
'''
def get_path(paths):
    # result = '<b>%s</b>\n<br>\n' % name
    result = ''
    p = ''
    for i in paths:
        for j in i:
            role = j[0]
            concept = j[1]
            if role == '@root' or role == '@entity':
                p += '<font face="arial">%s</font>' % concept
            else:
                p += ' --> <font face="verdana" color="orange">%s</font> <font face="arial">%s</font>' % (role, concept)
        p += '<br>'
    return result + p + '\n'

def get_html(senid, sen, amr, amr_paths, output):
    graph = '<img src="./graphs/%s.png">' % senid # default graphs path: ./graphs/
    senid = '<h2>%s</h2>\n' % senid
    sen = '<p><b>%s</b></p>\n' % sen
    amr = '<p>%s</p>\n' % amr.replace('\n', '<br>').replace(' ', '&nbsp;')
    paths = '<p><b>Paths:</b><br>'
    for p in amr_paths:
        paths += get_path(p)
    output.write('<body>\n%s%s%s%s%s</body>\n' % (senid, sen, amr, paths, graph))

def html(amr_table, output=open('../output/test.html', 'w'), graph_path='../output/graphs/'):
    import amr_visualizer

    try: os.mkdir(graph_path)
    except OSError: pass

    output.write('<meta charset=\'utf-8\'>\n')

    for docid in sorted(amr_table):
        for senid in sorted(amr_table[docid]):
            sen = amr_table[docid][senid]
            amr_visualizer.visualizer(sen.amr_nodes_, sen.paths_[0], output_name=sen.senid_)
            get_html(sen.senid_, sen.sen_, sen.amr_, sen.paths_[1:], output)

'''
 named entities
'''
def namedentity(amr_table, output=open('../output/amr_ne', 'w')):
    for docid in sorted(amr_table):
        for senid in sorted(amr_table[docid]):
            sen = amr_table[docid][senid]
            assert sen.senid_ == senid
            amr_nodes = sen.amr_nodes_
            for n in amr_nodes:
                node = amr_nodes[n]
                if node.is_entity_ and node.entity_type_ != '':
                    output.write('%s\t%s / %s\t%s\t%s\n' % (senid,
                                                            node.name_,
                                                            node.ful_name_,
                                                            node.entity_name_,
                                                            node.wiki_))
