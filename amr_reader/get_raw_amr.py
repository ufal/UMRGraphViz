'''
 dispose raw AMR
'''
import re
import os
import urllib

'''
 generate raw AMR from ISI AMR release files
 output:
        # ::id
        # ::snt
        ( ... 
             AMR ... )
'''
def read(path, file_name, output):
    f = open(path + file_name)
    for line in f:
        m = re.search('#\s::id\s(\S+)', line)
        if m != None:
            sen_id = m.group(1)
            print sen_id
            output.write('# ::id %s\n' %sen_id)
            sen = re.search('#\s::snt\s(.+)', next(f)).group(1)
            output.write('%s\n' %sen)
            next(f)
            line = next(f)
            while line != '\n':
                ### '()' in wiki title
                m = re.search(':wiki\s\"(.+?)\"', line)
                if m != None:
                    line = line.replace(m.group(1),
                                        urllib.quote_plus(m.group(1)))
                ### '()' in :name
                m = re.search('\"(\w*\(\S+\)\w*)\"', line)
                if m != None:
                    line = line.replace(m.group(1),
                    urllib.quote_plus(m.group(1)))

                output.write(line)

                try:
                    line = next(f)
                except StopIteration:
                    print 'END OF FILE: %s' % file_name
                    break
            output.write('\n')

'''
 generate raw amr from isi amr release files
 keep everthing 
 except convert '()' to '%28 %29' only
'''
def read_all(path, file_name, output):
    f = open(path + file_name)
    for line in f:
        ### file title
        if re.match('# AMR release .+', line) != None:
            continue
        ### lpp Chinese translation
        if re.match('# ::zh .+', line) != None:
            continue

        ### convert '()' in wiki title
        m = re.search(':wiki\s\"(.+?)\"', line)
        if m != None:
            line = line.replace(m.group(1),
                                urllib.quote_plus(m.group(1)))
        # ### convet '()' in :name
        # m = re.search('\"(\w*\(\S+\)\w*)\"', line)
        # if m != None:
        #     line = line.replace(m.group(1),
        #                         urllib.quote_plus(m.group(1)))

        ### convert '()' in :name
        m = re.findall('\"(\S+)\"', line)
        for i in m:
            if '(' in i or ')' in i:
                line = line.replace(i,
                                    urllib.quote_plus(i))

        output.write(line)
    print 'END OF FILE: %s' % file_name

'''
 generate plain docs from isi amr release files
'''
def generate_raw_docs(path, file_name):
    f = open(path + file_name)
    for line in f:
        m = re.search('#\s::id\s(\S+)', line)
        if m != None:
            sen_id = m.group(1)
            doc_id = sen_id[:sen_id.rfind('.')]
            try: os.mkdir('../output/raw_docs/')
            except OSError: pass
            out = open('../output/raw_docs/%s' % doc_id, 'aw')
            print sen_id
            sen = re.search('#\s::snt\s(.+)', next(f)).group(1)
            out.write('%s\t%s\n' % (sen_id, sen))
            next(f)
            line = next(f)
            while line != '\n':
                pass
                try:
                    line = next(f)
                except StopIteration:
                    print 'END OF FILE'
                    break


                
if __name__ == '__main__':
    path = '../doc/amr/Dec23/'
    file_list = os.listdir(path)
    output = open('../output/banked_amr', 'w')
    for i in file_list:
        read_all(path, i, output)
        # generate_raw_docs(path, i)
