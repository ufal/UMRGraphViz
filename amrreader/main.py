import os
import sys
import re
import argparse
import logging
from src import reader
from src import ne
from src import producer
from src import path


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'AMR Reader'
    parser.add_argument('indir', help='directory to AMR input files')
    parser.add_argument('outdir', help='outpu directory')
    parser.add_argument('-g', '--graph',
                        help='generate AMR graphs -g=n: standard graphs \
                        -g=s: simplified graphs ', type=str)
    parser.add_argument('-n', '--node',
                        help='generate AMR nodes', action='store_true')
    parser.add_argument('-p', '--path',
                        help='generate AMR paths', action='store_true')
    parser.add_argument('-e', '--entity',
                        help='generate named entities', action='store_true')
    parser.add_argument('-v', '--visualization',
                        help='generate html visualization \
                        -v=n standard graphs -v=s: simplified graphs', type=str)

    args = parser.parse_args()
    indir = args.indir
    outdir = args.outdir

    for i in os.listdir(indir):
        if not i.endswith(".txt") and not i.endswith(".umr"):
            continue
        logger.info('processing %s' % i)
        raw_amrs = open('%s/%s' % (indir, i), 'r').read()

        # Read raw AMR and add named entities
        sents = reader.main(raw_amrs)
        ne.add_named_entity(sents)

        outdir_i = f'{outdir}/{i}'
        os.makedirs(outdir_i, exist_ok=True)

        if args.graph == 'n':
            producer.get_graph(sents, outdir_i)

        if args.graph == 's':
            producer.get_graph(sents, outdir_i, curt=True)

        if args.node:
            producer.get_node(sents, outdir_i)

        if args.entity:
            producer.get_namedentity(sents, outdir_i)

        if args.path:
            path.main(sents)
            producer.get_path(sents, outdir_i)

        if args.visualization == 'n':
            producer.get_html(sents, 'visualization', outdir_i)

        if args.visualization == 's':
            producer.get_html(sents, 'visualization', outdir_i, curt=True)
