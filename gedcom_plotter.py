#!/usr/bin/env python3

""" Quick and dirty plotting of a family tree stored in a gedcom file
"""

import sys
import math
import os.path
import pygraphviz as pgv
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser

class NodeSize():
    """ calculation of node size for given text
    """
    def __init__(self, gedcom_parser, node_attributes, margin=None):

        self.node_attributes = node_attributes

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
        graph.add_node(1, label=time_string,
                       shape=node_attributes['shape'],
                       style=node_attributes['style'],
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
            graph.add_node(1, label=char,
                           shape=node_attributes['shape'],
                           style=node_attributes['style'],
                           width=0, height=0)
            graph.layout('dot')
            node = graph.get_node(1)
            one_char_width = float(node.attr['width'])
            one_char_height = float(node.attr['height'])

            graph = pgv.AGraph(rankdir='BT')
            graph.add_node(1, label=char + char + '\n' + char + char,
                           shape=node_attributes['shape'],
                           style=node_attributes['style'],
                           width=0, height=0)
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

            if len(longest_line) < 1:
                return ''

            lines[longest_line_index] = longest_line[:-1] + '...'

        text = '\n'.join(lines)

    return text

def format_name(person, max_width, max_height, ns):
    """ Format text with name/birth/death of person, so it fits inside of node
        with given size
    :param person: gedcom individual
    :param max_width: maximum width of node
    :param max_height: maximum width of node
    :param ns: NodeSize object, needed to truncate node text
    :return: formatted text
    """


    (first_name, last_name) = person.get_name()

    if first_name == '' and last_name=='':
        print(f'WARNING: Name is empty for record {person.get_pointer()} {person.get_tag()}.')

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

    # quick and dirty name + birth/death dates
    # (will overflow shapes)
    #return f'<{first_name}<BR/>{last_name}{time_string}>'.replace('&', '&amp;')

    height = max_height + 1

    while height > max_height:

        text = ''

        new_first_name = limit_text_to_width(first_name, max_width, ns)
        new_last_name  = limit_text_to_width(last_name, max_width, ns)

        if new_first_name != first_name or new_last_name != last_name:
            name_changed = True
            first_name = new_first_name
            last_name = new_last_name
        else:
            name_changed = False

        if first_name != '':
            text = first_name
        if last_name != '':
            text = text + '\n' + last_name

        new_width, new_height = ns.get_size(text, time_string!='')

        text = text + time_string
        text = text.replace('\n', '<BR/>')
        text = text.replace('&', '&amp;')
        text = '<' + text + '>'

#        # Slower but very accurate way of calculating the size
#        graph = pgv.AGraph(rankdir='BT')#, splines = 'true')
#        graph.add_node(1, label=text, shape='box', style='rounded')
#        graph.layout('dot')
#        node = graph.get_node(1)
#        #new_width = float(node.attr['width'])
#        new_height = float(node.attr['height'])

        # remove a line from the longer name part
        if last_name.count('\n') >= first_name.count('\n'):
            if last_name.rfind('\n') != -1:
                last_name = last_name[:last_name.rfind('\n')]
                last_name = last_name+'...'
        else:
            if first_name.rfind('\n') != -1:
                first_name = first_name[:first_name.rfind('\n')]
                first_name = first_name+'...'

        # if name and height does not change anymore, we entered infinite loop
        # (probably shape is not high enough for more than one line)
        if new_height == height and not name_changed:
            print(f'WARNING: Problem truncating text of {person.get_name()} for shape. Try different shape or bigger shape size.')
            break

        height = new_height

    if text == '<>' and (person.get_name()[0] != '' or
                         person.get_name()[1] != ''):
        print(f'WARNING: Problem truncating text of {person.get_name()} for shape. Try different shape or bigger shape size.')

    return text

def gedcom_to_graph(gedcom_filename,
                    node_attributes={},
                    fillcolor={'M':'#bce0f0', 'F':'#f8e3eb', 'O':'#fbfbcc'},
                    graph_attributes={}):
    """ Generate family tree graph for a given gedcom file
    :param gedcom_filename: name of input gedcom file
    :param node_attributes: node attributes like shape, style, etc.
    :param fillcolor: dictionary with color values for Male, Female, Other
    :param graph_attributes: dictionary with attributes passed to pgv.AGraph
    :return: pygraphviz graph containing family tree graph
    """

    direction = graph_attributes.get('rankdir', 'TB')

    if not os.path.exists(gedcom_filename):
        print(f'Input file {gedcom_filename} not found.')
        return None

    gedcom_parser = Parser()
    gedcom_parser.parse_file(gedcom_filename, False) # Disable strict parsing
    root_child_elements = gedcom_parser.get_root_child_elements()

    default_node_attributes = {'shape':'box',
                               'style':'rounded,filled',
                               'fixedsize':'true',
                               'width':2,
                               'height':1.15}

    for key, value in node_attributes.items():
        default_node_attributes[key] = node_attributes[key]

    print('Initializing text size estimation...')
    ns = NodeSize(gedcom_parser, default_node_attributes)

    graph = pgv.AGraph(**graph_attributes)

    # Add all indiviudals to graph
    n_people = 0
    for person in root_child_elements:
        if isinstance(person, IndividualElement):
            n_people += 1

    print(f'Family tree contains {n_people} people.')

    if n_people < 1:
        return None

    print('Creating nodes...')
    #counter = 0
    for person in root_child_elements:

        #print('\r' + str(int(counter * 100 / n_people)) + '%', end='')
        #counter += 1

        if isinstance(person, IndividualElement):

            if 'fillcolor' not in node_attributes.keys():
                default_node_attributes['fillcolor'] = \
                    fillcolor.get(person.get_gender(), fillcolor['O'])

            name = format_name(person,
                               default_node_attributes['width'],
                               default_node_attributes['height'],
                               ns)

            graph.add_node(person, label=name, **default_node_attributes)

    del ns
    #print('\r', end='')

    # sub_graph maps persons to spouse clusters
    sub_graphs = {}

    ports = {'BT': {'head': 's',
                    'tail': 'n'},
             'TB': {'head': 'n',
                    'tail': 's'},
             'LR': {'head': 'w',
                    'tail': 'e'},
             'RL': {'head': 'e',
                    'tail': 'w'}}

    print('Clustering spouses...')

    # Identify all married persons and put them in the same cluster.
    # Not trivial if more than one of the persons maried multiple times
    counter = 1
    for family in root_child_elements:

        if isinstance(family, FamilyElement):

            parents = gedcom_parser.get_family_members(family,
                                                       members_type='PARENTS')

            if len(parents) < 1:
                continue

            person = parents[0]
            person_id = person.get_pointer()

            if len(parents) > 1:

                spouse = parents[1]
                spouse_id = spouse.get_pointer()

                # add edge for spouse

                sg_name = None
                if person_id in sub_graphs:
                    sg_name = sub_graphs[person_id]

                    # if spouse is already in another subgraph, we have to
                    # merge subgraphs.
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

    print('Creating edges between spouses...')

    pairs = {}

    marriage_node_attributes = default_node_attributes.copy()
    # TODO: would be nice if marriage nodes were more customizable.
    #       Currently, they use same attributes as person labels, minus the
    #       attributes in the line below
    for key in ('label', 'xlabel', 'shape', 'width', 'height', 'margin',
                'fixedsize', 'style', 'fillcolor'):
        if key in marriage_node_attributes.keys():
            del marriage_node_attributes[key]

    for family in root_child_elements:

        if isinstance(family, FamilyElement):

            parents = gedcom_parser.get_family_members(family,
                                                       members_type='PARENTS')

            if len(parents) < 2:
                continue

            person = parents[0]
            person_id = person.get_pointer()

            spouse = parents[1]
            spouse_id = spouse.get_pointer()

            pair = spouse_id + person_id

            if pair not in pairs:
                pair = person_id + spouse_id
                pairs[pair] = True
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

                # display divorced marriages as dashed lines.
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
                # and all others a 'point'
                if marriage_label == '':
                    graph.add_node(pair, xlabel=marriage_label, shape='point',
                                   fixedsize='true', width=0.1, height=0.1,
                                   **marriage_node_attributes)
                else:
                    graph.add_node(pair, label=marriage_label,
                                   shape='plaintext', width=0,
                                   height=0, margin=0.01,
                                   **marriage_node_attributes)


                # peripheries='0' removes rectangles around subgraphs
                graph.add_subgraph((spouse, person, pair),
                                   peripheries='0', name=sub_graphs[person_id],
                                   cluster='true', label='')

                graph.add_edge(pair, person,
                               headport=ports[direction]['head'],
                               style=style, color="white:black:white",
                               penwidth=2)
                graph.add_edge(pair, spouse,
                               headport=ports[direction]['head'],
                               style=style, color="white:black:white",
                               penwidth=2)

    print(f'Graph contains {len(graph.edges())} edges.')

    del sub_graphs

    print('Creating edges to parents...')
    # Add edges to parents
    for person in root_child_elements:

        if isinstance(person, IndividualElement):

            parents = gedcom_parser.get_parents(person)

            if len(parents)<1:
                continue

            if len(parents)==2:

                pair = parents[0].get_pointer() + parents[1].get_pointer()
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
                # TODO: is the loop really necessary?
                for parent in parents:
                    graph.add_edge(person, parent,
                                   headport=ports[direction]['head'],
                                   tailport=ports[direction]['tail'],
                                   splines=None, color="white:black:white",
                                   penwidth=2)

    del root_child_elements
    del gedcom_parser

    print(f'Graph contains {len(graph.edges())} edges.')

    print('Creating layout...')
    #graph.layout('dot', args='-v4')
    graph.layout('dot')

    return graph

def run_edgepaint(G, color_scheme):
    """ Run edgepaint on graph
    :param G: input graph
    :param color_scheme: graphviz color scheme to apply to edges
    :return: graph with painted edges or None if there was a problem
    """

    import shutil
    if shutil.which('edgepaint') is None:
        print('WARNING: Cannot find edgepaint executable.')
        return None

    print('Running edgepaint...')
    import subprocess
    import tempfile

    tmpdir = tempfile.TemporaryDirectory()
    dot_filename = os.path.join(tmpdir.name, 'tmp.dot')

    G.draw(dot_filename)
    edgepaint_ret = subprocess.run(['edgepaint',
                                    '-share_endpoint',
                                    '-color_scheme='+color_scheme,
                                    dot_filename], capture_output=True)

    if edgepaint_ret.returncode != 0:
        print('edgepaint failed with error:')
        print(edgepaint_ret.stderr.decode("utf-8"))
        return None

    del dot_filename
    del tmpdir
    G.from_string(edgepaint_ret.stdout.decode("utf-8"))

    return G

def main():
    """ gedcom_plotter command line program
    """

    import argparse

    parser = argparse.ArgumentParser(prog='gedcom_plotter',
                                     description='Plot family tree defined in given gedcom file. \
                                     For many of the program arguments below (e.g. node_attributes, \
                                     graph_attributes), see the graphviz documentation for more \
                                     details.')

    parser.add_argument('gedcom_filename',
                        help='Input gedcom file.')
    parser.add_argument('-o', '--output_filename',
                        help='Output plot. See graphviz documentation for supported formats. If not specified, a PNG image is created.')
    parser.add_argument('-e', '--edgepaint', default=None,
                        help='If set, overlapping edges are painted according to given color scheme, e.g. rgb, gray, lab, dark28, etc.')
    parser.add_argument('-n', '--node_attributes', nargs='*', default=[],
                        help='Node attributes, e.g. shape=ellipse style=rounded,filled fontname="Comic Sans MS"')
    parser.add_argument('-g', '--graph_attributes', nargs='*', default=[],
                        help='Graph attributes passed on to graph initialization, e.g. rankdir=LR label="Family Tree" labelloc=t fontsize=100 fontname="Comic Sans MS"')
    parser.add_argument('-f', '--fillcolor', nargs='*', default=[],
                        help='Fill color for Male, Female, Other. Default: M=#bce0f0 F=#f8e3eb O=#fbfbcc')

    args = parser.parse_args()

    graph_attributes = {}
    for arg in args.graph_attributes:

        key, value = arg.split('=', 1)

        if value.replace('.','',1).isdigit():
            value = float(value)

        graph_attributes[key] = value

    node_attributes = {}
    for arg in args.node_attributes:

        key, value = arg.rsplit('=', 1)

        if value.replace('.','',1).isdigit():
            value = float(value)

        node_attributes[key] = value

    fillcolor={'M':'#bce0f0', 'F':'#f8e3eb', 'O':'#fbfbcc'}
    for arg in args.fillcolor:

        key, value = arg.rsplit('=', 1)

        if key[0] not in ('M', 'F', 'O'):
            print(f'Invalid fillcolor specified: {key[0]}. Must be one of M, F, O')
            sys.exit(1)

        fillcolor[key[0]] = value

    G = gedcom_to_graph(args.gedcom_filename,
                        node_attributes=node_attributes,
                        fillcolor=fillcolor,
                        graph_attributes=graph_attributes)

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
        G = run_edgepaint(G, args.edgepaint)

        if G is None:
            print('Failed to paint edges.')
            sys.exit(1)


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
