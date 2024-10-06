import sys
import os
import unittest
import tempfile
import gedcom_plotter

gedcom_sample = \
'''0 HEAD
0 @SUBM@ SUBM


0 @I1@ INDI
1 NAME Jane /Smith/
1 SEX F
1 BIRT
2 DATE 1 JAN 1950
2 PLAC Blackacre
1 FAMS @F1@
1 FAMS @F2@

0 @I2@ INDI
1 NAME Jayden /Doe/
1 BIRT
2 DATE 2 FEB 1951
2 PLAC Whiteacre
1 FAMS @F1@

0 @I3@ INDI
1 NAME Janie /Doe/
1 SEX F
1 BIRT
2 DATE 11 MAR 1975
2 PLAC Greenacre
1 FAMC @F1@

0 @I4@ INDI
1 NAME Johnny /Doe/
1 SEX M
1 BIRT
2 DATE 15 OCT 1977
2 PLAC Greenacre
1 FAMC @F1@

0 @I5@ INDI
1 NAME Joe /Schmoe/
1 SEX M
1 BIRT
2 DATE 30 DEC 1945
2 PLAC Brownacre
1 FAMS @F2@

0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
1 CHIL @I3@
1 CHIL @I4@
1 MARR
2 DATE 22 JUN 1970
2 PLAC Greenacre
1 DIV
2 TYPE Y
2 DATE 25 AUG 1980

0 @F2@ FAM
1 HUSB @I5@
1 WIFE @I1@
1 MARR
2 DATE 15 SEP 1985
2 PLAC Brownacre
'''

class GedcomPlotterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.gedcom_file = tempfile.NamedTemporaryFile('w+', delete=False)

        cls.gedcom_file.write(gedcom_sample)
        cls.gedcom_file.flush()
        cls.gedcom_file.close()

    @classmethod
    def tearDownClass(cls):

        if os.path.exists(cls.gedcom_file.name):
            os.unlink(cls.gedcom_file.name)
    
    def test_init(self):

        g2g = gedcom_plotter.GedcomPlotter(self.gedcom_file.name)
        self.assertEqual(len(g2g.gedcom_parser.get_root_child_elements()), 9)

    def test_set_node_attributes(self):

        g2g = gedcom_plotter.GedcomPlotter(self.gedcom_file.name)
        g2g.set_node_attributes()

        self.assertAlmostEqual(g2g.ns.widths['.'], 0.06944)
        self.assertAlmostEqual(g2g.ns.widths['m'], 0.19444)
        self.assertAlmostEqual(g2g.ns.heights['n'], 0.20834)
        
        g2g.set_node_attributes({'fontsize': 20})

        self.assertAlmostEqual(g2g.ns.widths['.'], 0.08334)
        self.assertAlmostEqual(g2g.ns.widths['m'], 0.26389)
        self.assertAlmostEqual(g2g.ns.heights['n'], 0.30555)

    def test_create_graph(self):

        g2g = gedcom_plotter.GedcomPlotter(self.gedcom_file.name)
        g2g.set_node_attributes()
        G = g2g.create_graph()

        #G.draw('test.png')

        self.assertEqual(len(G.nodes()), 7)
        self.assertEqual(len(G.edges()), 6)

        jayden_doe = G.get_node('0 @I2@ INDI\n')
        self.assertEqual(G.edges((jayden_doe,))[0].attr.get('style'), 'dashed')
        
        joe_schmo = G.get_node('0 @I5@ INDI\n')
        self.assertEqual(G.edges((joe_schmo,))[0].attr.get('style'), 'solid')

# python -m unittest tests.test_gedcom_plotter
