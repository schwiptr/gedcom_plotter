#!/usr/bin/env python3

""" Quick and dirty plotting of a family tree stored in a gedcom file
"""

import math
import os.path
import pygraphviz as pgv
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser

class NodeSize():
    """ calculation of node size for given text
    """
    def __init__(self, gedcom_parser, margin=None):

        all_names = []
        all_names.append(' .')

        root_child_elements = gedcom_parser.get_root_child_elements()

        for person in root_child_elements:
            if isinstance(person, IndividualElement):
                (first_name, last_name) = person.get_name()
                all_names.append(first_name)
                all_names.append(last_name)

        all_names = ''.join(all_names)
        # all the characters present in the names of this tree:
        all_chars = ''.join(set(all_names))

        print(f'Number of characters: {len(all_chars)}')
        del all_names

        # default margins = 0.11,0.055, see
        # https://graphviz.org/docs/attrs/margin/
        if margin is None:
            self.margins_x = 0.11  * 2
            self.margins_y = 0.055 * 2
        else:
            self.margins_x = margin[0] * 2
            self.margins_y = margin[1] * 2

        time_string = '<<FONT COLOR="gray15" POINT-SIZE="10.0">1234567890-</FONT>>'

        graph = pgv.AGraph(rankdir='BT')
        graph.add_node(1, label=time_string, shape='box', style='rounded',
                       width=0, height=0)
        graph.layout('dot')
        node = graph.get_node(1)
        self.margins_y_with_time = float(node.attr['height'])

        self.widths = {}
        self.heights = {}

        # counter = 0
        # n_chars = len(all_chars)

        for char in all_chars:
            graph = pgv.AGraph(rankdir='BT')#, splines = 'true')
            graph.add_node(1, label=char, shape='box', style='rounded',
                           width=0, height=0)
            graph.layout('dot')
            node = graph.get_node(1)
            one_char_width = float(node.attr['width'])
            one_char_height = float(node.attr['height'])

            graph = pgv.AGraph(rankdir='BT')
            graph.add_node(1, label=char + char + '\n' + char + char,
                           shape='box', style='rounded', width=0, height=0)
            graph.layout('dot')
            node = graph.get_node(1)
            two_chars_width = float(node.attr['width'])
            two_chars_height= float(node.attr['width'])

            width_of_one_char = two_chars_width - one_char_width
            height_of_one_char = two_chars_height - one_char_height
            self.widths[char] = width_of_one_char
            self.heights[char] = height_of_one_char
            # print('\r' + str(counter * 100. / n_chars) + '%', end='')
            # counter += 1
        # print('\r', end='')

    def get_size(self, text, with_time):
        """ estimate node size for given text
        :param text: text to be displayed inside the node
        :param with_time: True if an additional time string (smaller font size)
                          should be displayed in the node
        :return: width and height of the node
        """

        if with_time:
            ret_height = self.margins_y_with_time
        else:
            ret_height = self.margins_y
        ret_width = 0

        for line in text.splitlines():
            line_width = 0
            line_height = 0

            for char in line:
                line_width += self.widths[char]
                line_height = max(line_height, self.heights[char])

            ret_width = max(ret_width, line_width + self.margins_x)
            ret_height += line_height

        return ret_width, ret_height


def limit_text_to_width(text, max_width, ns):
    """ Reduce text until it fits into node with given maximum
    :param text: input text to reduce
    :param max_width: maximum width of node
    :return: reduced text
    """

    width = max_width + 1

    while width > max_width:

        # determine size of node by creating graph
#        # Slower but very accurate way of calculating the size
#        graph = pgv.AGraph(rankdir='BT')#, splines = 'true')
#        graph.add_node(1, label=text, shape='box', style='rounded')
#        graph.layout('dot')
#        node = graph.get_node(1)
#        width = float(node.attr['width'])
        width, height = ns.get_size(text, False)

        if width <= max_width:
            return text

        lines = text.splitlines()
        longest_line = max(lines, key=len)
        longest_line_index = lines.index(longest_line)

        if ' ' in longest_line:
            # split longest line at whitespace

            max_length = math.inf
            max_n = -1
            for i in range(len(text.split(' '))):
                first_part  = ' '.join(longest_line.split(' ', i)[:i])
                second_part = ' '.join(longest_line.split(' ', i)[i:])

                # actually it would be more precise to calculate length using
                # pgv here, but also much slower...
                max_for_i = max(len(first_part), len(second_part))

                if max_for_i < max_length:
                    max_n = i
                    max_length = max_for_i

            first_part  = ' '.join(longest_line.split(' ', max_n)[:max_n])
            second_part = ' '.join(longest_line.split(' ', max_n)[max_n:])

            lines[longest_line_index] = first_part + '\n' + second_part

        else:
            if longest_line[-3:] == '...':
                longest_line = longest_line[:-3]

            lines[longest_line_index] = longest_line[:-1] + '...'

        text = '\n'.join(lines)

    return text

def format_name(person, max_width, max_height, ns):
    """ Format text with name/birth/death of person, so it fits inside of node
        with given size
    :param person: gedcom individual
    :param max_width: maximum width of node
    :param max_height: maximum width of node
    :return: formatted text
    """


    (first_name, last_name) = person.get_name()

    if first_name == '' and last_name=='':
        print(f'WARNING: Name is empty for {person}.')

    birth_year = person.get_birth_year()
    death_year = person.get_death_year()

    if birth_year==-1 and death_year==-1:
        time_string=''
    elif birth_year==-1:
        time_string=f'? - {death_year}'
    elif death_year==-1:
        if person.is_deceased():
            time_string=f'{birth_year} - ?'
        else:
            time_string=f'{birth_year}'
    else:
        time_string=f'{birth_year} - {death_year}'


    if time_string != '':
        time_string = f'<BR/><FONT COLOR="gray15" POINT-SIZE="10.0">{time_string}</FONT>'

    # quick and dirty name, + birth/death dates
    #return f'<{first_name}<BR/>{last_name}{time_string}>'.replace('&', '&amp;')

    text = ''

    height = max_height + 1
    while height > max_height:

        first_name = limit_text_to_width(first_name, max_width, ns)
        last_name  = limit_text_to_width(last_name, max_width, ns)

        if first_name != '':
            text = first_name
        if last_name != '':
            text = text + '\n' + last_name

        width, height = ns.get_size(text, time_string!='')
        text = text + time_string
        text = text.replace('\n', '<BR/>')
        text = text.replace('&', '&amp;')
        text = '<' + text + '>'

#        # Slower but very accurate way of calculating the size
#        graph = pgv.AGraph(rankdir='BT')#, splines = 'true')
#        graph.add_node(1, label=text, shape='box', style='rounded')
#        graph.layout('dot')
#        node = graph.get_node(1)
#        #width = float(node.attr['width'])
#        height = float(node.attr['height'])

        # remove a line from the longer name part
        if last_name.count('\n') >= first_name.count('\n'):
            last_name = last_name[:last_name.rfind('\n')]
            last_name = last_name+'...'
        else:
            first_name = first_name[:first_name.rfind('\n')]
            first_name = first_name+'...'

    return text

def gedcom_to_graph(gedcom_filename, label='', labelloc="t", labelsize=100,
                    direction='BT'):
    """ Generate family tree graph for a given gedcom file
    :param gedcom_filename: name of input gedcom file
    :return: pygraphviz graph containing family tree graph
    """

    if not os.path.exists(gedcom_filename):
        print(f'Input file {gedcom_filename} not found.')
        return None

    node_width = 2
    node_height = 1.15

    gedcom_parser = Parser()
    gedcom_parser.parse_file(gedcom_filename, False) # Disable strict parsing
    root_child_elements = gedcom_parser.get_root_child_elements()

    print('Initializing text size estimation...')
    ns = NodeSize(gedcom_parser)

    graph = pgv.AGraph(rankdir=direction, label=label, labelloc=labelloc,
                       fontsize=labelsize)

    # Add all indiviudals to graph
    n_people = 0
    for person in root_child_elements:
        if isinstance(person, IndividualElement):
            n_people += 1

    print(f'Family tree contains {n_people} people.')

    print('Creating nodes...')
    #counter = 0
    for person in root_child_elements:

        #print('\r' + str(int(counter * 100 / n_people)) + '%', end='')
        #counter += 1

        if isinstance(person, IndividualElement):

            if person.get_gender() == 'M':
                color = '#bce0f0'
            elif person.get_gender() == 'F':
                color = '#f8e3eb'
            else:
                color = '#fbfbcc'

            name = format_name(person, node_width, node_height, ns)

            graph.add_node(person, label=name, shape='box', style='rounded,filled',
                           fixedsize='true', width=node_width, height=node_height,
                           fillcolor=color)

    #print('\r', end='')
    print('Creating edges to spouses...')

    sub_graphs = {}
    pairs = {}

    ports = {'BT': {'head': 's',
                    'tail': 'n'},
             'TB': {'head': 'n',
                    'tail': 's'},
             'LR': {'head': 'w',
                    'tail': 'e'},
             'RL': {'head': 'e',
                    'tail': 'w'}}

    # Identify all married persons and put them in the same cluster.
    # Not trivial if more than one of the persons maried multiple times
    counter = 1
    for family in root_child_elements:

        if isinstance(family, FamilyElement):

            parents = gedcom_parser.get_family_members(family, members_type='PARENTS')

            if len(parents) < 1:
                continue

            person = parents[0]
            person_id = str(person).strip()

            for spouse in parents[1:]:

                spouse_id = str(spouse).strip()

                # add edge for spouse

                sg_name = None
                if person_id in sub_graphs:
                    sg_name = sub_graphs[person_id]

                    # if spouse is already in another subgraph, we have to merge subgraphs.
                    if spouse_id in sub_graphs:
                        spouse_sg_name = sub_graphs[spouse_id]
                        for key, value in sub_graphs.items():
                            if value == spouse_sg_name:
                                sub_graphs[key] = sg_name


                if spouse_id in sub_graphs:
                    sg_name = sub_graphs[spouse_id]

                if sg_name is None:
                    sg_name = f'cluster_{counter}'
                    counter += 1
                sub_graphs[spouse_id] = sg_name
                sub_graphs[person_id] = sg_name

    # Add edges and subgraphs for spouses
    for family in root_child_elements:

        if isinstance(family, FamilyElement):

            parents = gedcom_parser.get_family_members(family, members_type='PARENTS')

            if len(parents) < 1:
                continue

            person = parents[0]
            person_id = str(person).strip()

            for spouse in parents[1:]:
                sg_name = sub_graphs[person_id]

                spouse_id = str(spouse).strip()

                pair = spouse_id + person_id

                if pair not in pairs:
                    pair = person_id + spouse_id
                    pairs[pair] = True
                    # display divorced marriages as dashed lines.
                    style = 'solid'
                    marriage_label = ''
                    divorced = False
                    for c in family.get_child_elements():

                        # check if couple is divorced
                        if c.get_tag() == 'DIV':

                            if c.get_value() == 'Y':
                                marriage_label = '⚮'
                                divorced = True

                            # not sure why, but sometimes the divorce value
                            # is stored in extra child person
                            for c2 in c.get_child_elements():
                                if c2.get_tag() == 'TYPE':
                                    if c2.get_value() == 'Y':
                                        marriage_label = '⚮'
                                        divorced = True
                                if c2.get_tag() == 'DATE':
                                    year = c2.get_value().split()[-1]
                                    if len(year) == 4 and year.isdigit():
                                        marriage_label = f'<⚮<BR/><FONT POINT-SIZE="10.0">{year}</FONT>>'

                            break

                    if divorced:
                        style = 'dashed'
                    # only check for marriage record if there was no divorce
                    else:
                        for c in family.get_child_elements():
                            # check if couple is married
                            if c.get_tag() == 'MARR':
                                marriage_label = '⚭'

                                for c2 in c.get_child_elements():
                                    if c2.get_tag() == 'DATE':
                                        year = c2.get_value().split()[-1]
                                        if len(year) == 4 and year.isdigit():
                                            marriage_label = f'<⚭<BR/><FONT POINT-SIZE="10.0">{year}</FONT>>'

                    # Couples are always connected by a "pair" node. Married
                    # couples get a ⚭ symbol, divorced couples a ⚮ symbol
                    # and all other just a 'point'
                    if marriage_label == '':
                        graph.add_node(pair, xlabel=marriage_label, shape='point',
                                       fixedsize='true', width=0.1, height=0.1)
                    else:
                        graph.add_node(pair, label=marriage_label,
                                       shape='plaintext', width=0,
                                       height=0, margin=0.01)


                    # peripheries='0' removes rectangles around subgraphs
                    graph.add_subgraph((spouse, person, pair),
                                       peripheries='0', name=sg_name,
                                       cluster='true', label='')

                    graph.add_edge(pair, person,
                                   headport=ports[direction]['head'],
                                   style=style, color="white:black:white",
                                   penwidth=2)
                    graph.add_edge(pair, spouse,
                                   headport=ports[direction]['head'],
                                   style=style, color="white:black:white",
                                   penwidth=2)



    print('Creating edges to parents...')
    # Add edges to parents
    for person in root_child_elements:

        if isinstance(person, IndividualElement):

            parents = gedcom_parser.get_parents(person)

            if len(parents)<1:
                continue

            if len(parents)==2:

                pair = str(parents[0]).strip() + str(parents[1]).strip()
                if pair in pairs:
                    graph.add_edge(person, pair,
                                   headport=ports[direction]['head'],
                                   tailport=ports[direction]['tail'],
                                   splines=None, color="white:black:white",
                                   penwidth=2)
                    continue

                pair = str(parents[1]).strip() + str(parents[0]).strip()
                if pair in pairs:
                    graph.add_edge(person, pair,
                                   headport=ports[direction]['head'],
                                   tailport=ports[direction]['tail'],
                                   splines=None, color="white:black:white",
                                   penwidth=2)
                    continue

            else:
                for parent in parents:
                    graph.add_edge(person, parent,
                                   headport=ports[direction]['head'],
                                   tailport=ports[direction]['tail'],
                                   splines=None, color="white:black:white",
                                   penwidth=2)

    del root_child_elements
    del gedcom_parser

    print('Creating layout...')
    #graph.layout('dot', args='-v4')
    graph.layout('dot')

    return graph

def main():

    import sys
    import argparse

    parser = argparse.ArgumentParser(prog='gedcom_plotter',
                                     description='Plot family tree defined in given gedcom file.')

    parser.add_argument('gedcom_filename',
                        help='Input gedcom file.')
    parser.add_argument('-o', '--output_filename',
                        help='Output plot. See graphviz documentation for supported formats. If not specified, a PNG image is created.')
    parser.add_argument('-t', '--title', default='',
                        help='Title of the output plot.')
    parser.add_argument('-e', '--edgepaint', default=None,
                        help='If set, overlapping edges are painted according to given color scheme, e.g. rgb, gray, lab, dark28, etc.')
    parser.add_argument('-r', '--rankdir', default='BT', choices=['BT', 'TB', 'LR', 'RL'],
                        help='Direction of plot, e.g. "LR" for Left to Right. Default is "BT" for Bottom to Top.')
    parser.add_argument('-tl', '--titleloc', default='t',
                        help='Location of title. Possible values: t, b')
    parser.add_argument('-ts', '--titlesize', default=100,
                        help='Font size of title.')

    args = parser.parse_args()

    G = gedcom_to_graph(args.gedcom_filename, label=args.title,
                        labelloc=args.titleloc, labelsize=args.titlesize,
                        direction=args.rankdir)

    if G is None:
        print('Failed to generate graph.')
        sys.exit(1)

    if args.output_filename:
        output_filename = args.output_filename
    else:
        output_filename = os.path.basename(args.gedcom_filename)
        output_filename = output_filename.rsplit('.', 1)[0]
        output_filename = output_filename + '.png'

    if args.edgepaint:

        import shutil
        if shutil.which('edgepaint') is None:
            print('WARNING: Cannot find edgepaint executable.')

        else:

            print('Running edgepaint...')
            import subprocess
            import tempfile

            tmpdir = tempfile.TemporaryDirectory()
            dot_filename = os.path.join(tmpdir.name, 'tmp.dot')

            G.draw(dot_filename)
            edgepaint_ret = subprocess.run(['edgepaint',
                                            '-share_endpoint',
                                            '-color_scheme='+args.edgepaint,
                                            dot_filename], capture_output=True)

            if edgepaint_ret.returncode != 0:
                print('edgepaint failed with error:')
                print(edgepaint_ret.stderr.decode("utf-8"))
                sys.exit(1)

            del dot_filename
            del tmpdir
            G.from_string(edgepaint_ret.stdout.decode("utf-8"))


    print('Plotting output...')

    # for svg, use svg:cairo to get centered labels, see
    # https://gitlab.com/graphviz/graphviz/-/issues/1426
    if output_filename[-4:].upper() == '.SVG':
        G.draw(output_filename, format='svg:cairo')
    else:
        G.draw(output_filename)

    print(f'Created {output_filename}')

if __name__ == '__main__':
    main()
