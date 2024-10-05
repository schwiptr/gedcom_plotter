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
    def __init__(self, gedcom_parser, node_attributes,
                 time_format, margin=None):

        self.time_format = time_format
        self.node_attributes = node_attributes.copy()

        # remove width and height, since these should be set automatically
        if 'width' in self.node_attributes.keys():
            del self.node_attributes['width']
        if 'height' in self.node_attributes.keys():
            del self.node_attributes['height']
        self.node_attributes['fixedsize'] = False

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

        time_string = f'<<FONT {time_format}>1234567890-</FONT>>'

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
                           width=0, height=0, **self.node_attributes)
            graph.layout('dot')
            node = graph.get_node(1)
            one_char_width = float(node.attr['width'])
            one_char_height = float(node.attr['height'])

            graph = pgv.AGraph(rankdir='BT')
            graph.add_node(1, label=char + char + '\n' + char + char,
                           width=0, height=0, **self.node_attributes)
            graph.layout('dot')
            node = graph.get_node(1)
            two_chars_width = float(node.attr['width'])
            two_chars_height= float(node.attr['height'])

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
    :param max_height: maximum height of node
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
        time_string = f'<BR/><FONT {ns.time_format}>{time_string}</FONT>'

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
            print(f'WARNING1: Problem truncating text of {person.get_name()} for shape. Try different shape, bigger shape size or smaller font size.')
            break

        height = new_height

    if text == '<>' and (person.get_name()[0] != '' or
                         person.get_name()[1] != ''):
        print(f'WARNING2: Problem truncating text of {person.get_name()} for shape. Try different shape, bigger shape size or smaller font size.')

    return text

def follow_link(e, gedcom_parser):
    """ Follow a link in a gedcom entry
    :param e: gedcom element which links to another element
    :param gedcom_parser: parser of current gedcom file
    :return: Target of link
    """

    link = e.get_value()

    if len(link) < 1:
        return e

    if link[0] == '@' and link[-1] == '@':
        ele_dict = gedcom_parser.get_element_dictionary()
        if link in ele_dict.keys():
            return ele_dict[link]

    return e

def note_to_string(e, gedcom_parser):
    """ Convert gedcom note entry to string
    :param e: gedcom note element
    :param gedcom_parser: parser of current gedcom file
    :return: Converted string
    """

    e = follow_link(e, gedcom_parser)

    ret_string = e.get_value()

    if len(ret_string) < 1:
        return ''

#    # follow reference
#    if ret_string[0] == '@' and ret_string[-1] == '@':
#        e = gedcom_parser.get_element_dictionary()[ret_string]
#        ret_string = e.get_value()

    for c in e.get_child_elements():
        if c.get_tag() == 'CONT':
            ret_string = ret_string + '\n' + c.get_value()
        if c.get_tag() == 'CONC':
            ret_string = ret_string + c.get_value()

    return ret_string

def source_to_string(e, gedcom_parser):
    """ Convert gedcom source entry to string
    :param e: gedcom note element
    :param gedcom_parser: parser of current gedcom file
    :return: Converted string
    """

    ret_string = 'Source:\n'

    for c in e.get_child_elements():
        c = follow_link(c, gedcom_parser)

        if c.get_tag() == 'TITL':
            ret_string = ret_string + c.get_value() + ':\n'

    for c in e.get_child_elements():
        c = follow_link(c, gedcom_parser)

        if c.get_tag() == 'NOTE':
            ret_string = ret_string + note_to_string(c, gedcom_parser)

    return ret_string

def get_tooltip(e, gedcom_parser):
    """ Create a tooltip for given element
    (not fully implemented/tested)
    :param e: gedcom note element
    :param gedcom_parser: parser of current gedcom file
    :return: Tooltip as string
    """

    # Tooltip always starts with name:
    (first_name, last_name) = e.get_name()
    if first_name == '':
        ret_string = '?'
    else:
        ret_string = first_name

    if last_name != '':
        ret_string = ret_string + ' ' + last_name

    ret_string = ret_string + '\n'

    # TODO: birth, death, dates and places, etc.

    # check if there is a note at first level:
    for c in e.get_child_elements():

        c = follow_link(c, gedcom_parser)

        if c.get_tag() == 'NOTE':
            ret_string = ret_string + note_to_string(c, gedcom_parser)

    # check if there is a note at second level:
    for c in e.get_child_elements():

        c = follow_link(c, gedcom_parser)

        for c2 in c.get_child_elements():

            c2 = follow_link(c2, gedcom_parser)

            if c2.get_tag() == 'NOTE':
                if c.get_tag() == 'SOUR':
                    ret_string = ret_string + source_to_string(c, gedcom_parser)
                else:
                    ret_string = ret_string + c.get_tag() + ':\n'   # TODO: this looks ugly (BIRT, DEAT, etc.)
                    ret_string = ret_string + note_to_string(c2, gedcom_parser)

    return ret_string

class GedcomPlotter():
    """ Create plot from gedcom file
    """

    def __init__(self, gedcom_filename):
        """
        :param gedcom_filename: name of input gedcom file
        """

        self.gedcom_parser = None
        self.ns = None

        self.default_node_attributes = {'shape':'box',
                                        'style':'rounded,filled',
                                        'fixedsize':'true',
                                        'width':2,
                                        'height':1.15}

        self.time_format = 'COLOR="gray15" POINT-SIZE="10.0"'

        if not os.path.exists(gedcom_filename):
            print(f'Input file {gedcom_filename} not found.')
            return None

        self.gedcom_parser = Parser()
        self.gedcom_parser.parse_file(gedcom_filename, False) # Disable strict parsing
        self.root_child_elements = self.gedcom_parser.get_root_child_elements()

        n_people = 0
        for person in self.root_child_elements:
            if isinstance(person, IndividualElement):
                n_people += 1

        print(f'Family tree contains {n_people} people.')

        if n_people < 1:
            return None

    def set_node_attributes(self, node_attributes):
        """ set node attributes. This method has to be run once before running
            create_graph. Every time the node attributes or font sizes change,
            the NodeSize has to be re-estimated.
        :param node_attributes: node attributes like shape, style, etc.
        """

        if self.gedcom_parser is None:
            print('Gedcom parser not initialized.')
            return None

        for key, value in node_attributes.items():
            self.default_node_attributes[key] = node_attributes[key]

        # whenever node attributes change, the text size has to be re-estimated
        print('Initializing text size estimation...')
        self.ns = NodeSize(self.gedcom_parser,
                           self.default_node_attributes,
                           self.time_format)

        return self.ns

    def create_graph(self,
                     fillcolor={'M':'#bce0f0', 'F':'#f8e3eb', 'O':'#fbfbcc'},
                     graph_attributes={}):
        """ Generate family tree graph for a given gedcom file.
        Only works if set_node_attributes was run first.
        :param fillcolor: dictionary with color values for Male, Female, Other
        :param graph_attributes: dictionary with attributes passed to pgv.AGraph
        :return: pygraphviz graph containing family tree graph
        """

        if self.gedcom_parser is None:
            print('Gedcom parser not initialized.')
            return None

        if self.ns is None:
            print('Node sizes not initialized.')
            return None

        direction = graph_attributes.get('rankdir', 'TB')

        if direction not in ('TB', 'BT', 'LR', 'RL'):
            print(f'Invalid rankdir of {direction} specified. Must be one of: BT, TB, LR, RL')
            return None

        graph = pgv.AGraph(**graph_attributes)

        if 'bgcolor' not in graph_attributes.keys():
            graph_attributes['bgcolor'] = '#ffffffff'

        # Add all indiviudals to graph

        print('Creating nodes...')
        #counter = 0
        for person in self.root_child_elements:

            #print('\r' + str(int(counter * 100 / n_people)) + '%', end='')
            #counter += 1

            if isinstance(person, IndividualElement):

                #if 'fillcolor' not in node_attributes.keys():
                self.default_node_attributes['fillcolor'] = \
                    fillcolor.get(person.get_gender(), fillcolor['O'])

                name = format_name(person,
                                   self.default_node_attributes['width'],
                                   self.default_node_attributes['height'],
                                   self.ns)

                graph.add_node(person,
                               label=name,
                               #tooltip=get_tooltip(person, self.gedcom_parser),
                               **self.default_node_attributes)

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
        for family in self.root_child_elements:

            if isinstance(family, FamilyElement):

                parents = self.gedcom_parser.get_family_members(family,
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

        marriage_node_attributes = self.default_node_attributes.copy()
        # TODO: would be nice if marriage nodes were more customizable.
        #       Currently, they use same attributes as person labels, minus the
        #       attributes in the line below
        for key in ('label', 'xlabel', 'shape', 'width', 'height', 'margin',
                    'fixedsize', 'style', 'fillcolor'):
            if key in marriage_node_attributes.keys():
                del marriage_node_attributes[key]

        for family in self.root_child_elements:

            if isinstance(family, FamilyElement):

                parents = self.gedcom_parser.get_family_members(family,
                                                           members_type='PARENTS')

                if len(parents) < 2:
                    continue

                person = parents[0]
                person_id = person.get_pointer()

                spouse = parents[1]

                if family not in pairs:
                    pairs[family] = True
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
                        graph.add_node(family, xlabel=marriage_label, shape='point',
                                       fixedsize='true', width=0.1, height=0.1,
                                       **marriage_node_attributes)
                    else:
                        graph.add_node(family, label=marriage_label,
                                       shape='plaintext', width=0,
                                       height=0, margin=0.01,
                                       **marriage_node_attributes)


                    # peripheries='0' removes rectangles around subgraphs
                    graph.add_subgraph((spouse, person, family),
                                       peripheries='0', name=sub_graphs[person_id],
                                       cluster='true', label='')

                    graph.add_edge(family, person,
                                   headport=ports[direction]['head'],
                                   style=style, color="%s:black:%s" % (graph_attributes['bgcolor'], graph_attributes['bgcolor']),
                                   penwidth=2)
                    graph.add_edge(family, spouse,
                                   headport=ports[direction]['head'],
                                   style=style, color="%s:black:%s" % (graph_attributes['bgcolor'], graph_attributes['bgcolor']),
                                   penwidth=2)

        print(f'Graph contains {len(graph.edges())} edges.')

        del sub_graphs

        print('Creating edges to parents...')
        # Add edges to parents
        for person in self.root_child_elements:

            if isinstance(person, IndividualElement):

                families = self.gedcom_parser.get_families(person, family_type='FAMC')

                # child can belong to more than one family if it was adopted:
                for family in families:

    #                # check if child is adopted:
    #                # TODO: edge of child adopted by both parents could be
    #                #       displayed dotted/dashed or with special symbol.
    #                #       No idea how to display edge for child adopted by one
    #                #       of the parents only though.
    #                for c in person.get_child_elements():
    #                    if c.get_tag() == 'FAMC':
    #
    #                        if c.get_value() != family.get_pointer():
    #                            continue
    #
    #                        for c2 in c.get_child_elements():
    #                            if c2.get_tag() == 'PEDI':
    #                                if c2.get_value() == 'ADOPTED':
    #                                    print(f'Adopted by {family.get_pointer()}')
    #                                    # TODO: identify who adopted child, using
    #                                    #       ADOP tag: BOTH|HUSB|WIFE

                    if family in pairs:
                        graph.add_edge(person, family,
                                       headport=ports[direction]['head'],
                                       tailport=ports[direction]['tail'],
                                       splines=None, color="%s:black:%s" % (graph_attributes['bgcolor'], graph_attributes['bgcolor']),
                                       penwidth=2)

                    # if only one of the parents is known, the child is linked to
                    # that directly, instead of the (non-existent) pair node
                    else:
                        parents = self.gedcom_parser.get_family_members(family,
                                    members_type='PARENTS')

                        for parent in parents:
                            graph.add_edge(person, parent,
                                           headport=ports[direction]['head'],
                                           tailport=ports[direction]['tail'],
                                           splines=None, color="%s:black:%s" % (graph_attributes['bgcolor'], graph_attributes['bgcolor']),
                                           penwidth=2)


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
                        help='Graph attributes, e.g. rankdir=LR label="Family Tree" labelloc=t fontsize=100 fontname="Comic Sans MS"')
    parser.add_argument('-f', '--fillcolor', nargs='*', default=[],
                        help='Fill color for Male, Female, Other. Default: M=#bce0f0 F=#f8e3eb O=#fbfbcc')

    args = parser.parse_args()

    graph_attributes = {'bgcolor': '#ffffffff'}
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

    g2g = GedcomPlotter(args.gedcom_filename)

    if g2g.set_node_attributes(node_attributes) is None:
        print('Failed to set node attributes.')
        sys.exit(1)

    G = g2g.create_graph(fillcolor=fillcolor,
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
        #G.draw(output_filename)
    else:
        G.draw(output_filename)

    print(f'Created {output_filename}')

if __name__ == '__main__':
    main()
