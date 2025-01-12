#!/usr/bin/env python
#
# This file is referred and derived from project NetworkX
#
# which has the following license:
#
# Copyright (C) 2004-2020, NetworkX Developers
# Aric Hagberg <hagberg@lanl.gov>
# Dan Schult <dschult@colgate.edu>
# Pieter Swart <swart@lanl.gov>
# All rights reserved.
#
# This file is part of NetworkX.
#
# NetworkX is distributed under a BSD license; see LICENSE.txt for more
# information.
#
import math

import pytest

np = pytest.importorskip("numpy")
scipy = pytest.importorskip("scipy")

from graphscope import nx
from graphscope.nx.tests.utils import almost_equal


def weighted_G():
    G = nx.Graph()
    G.add_edge(0, 1, weight=3)
    G.add_edge(0, 2, weight=2)
    G.add_edge(0, 3, weight=6)
    G.add_edge(0, 4, weight=4)
    G.add_edge(1, 3, weight=5)
    G.add_edge(1, 5, weight=5)
    G.add_edge(2, 4, weight=1)
    G.add_edge(3, 4, weight=2)
    G.add_edge(3, 5, weight=1)
    G.add_edge(4, 5, weight=4)
    return G


@pytest.mark.usefixtures("graphscope_session")
class TestBetweennessCentrality:
    def test_K5(self):
        """Betweenness centrality: K5"""
        G = nx.complete_graph(5)
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        b_answer = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_K5_endpoints(self):
        """Betweenness centrality: K5 endpoints"""
        G = nx.complete_graph(5)
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=False, endpoints=True
        )
        b_answer = {0: 4.0, 1: 4.0, 2: 4.0, 3: 4.0, 4: 4.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])
        # normalized = True case
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=True, endpoints=True
        )
        b_answer = {0: 0.4, 1: 0.4, 2: 0.4, 3: 0.4, 4: 0.4}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_P3_normalized(self):
        """Betweenness centrality: P3 normalized"""
        G = nx.path_graph(3)
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=True)
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_P3(self):
        """Betweenness centrality: P3"""
        G = nx.path_graph(3)
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    @pytest.mark.skip(reason="not support sampling")
    def test_sample_from_P3(self):
        G = nx.path_graph(3)
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        b = nx.builtin.betweenness_centrality(
            G, k=3, weight=None, normalized=False, seed=1
        )
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])
        b = nx.builtin.betweenness_centrality(
            G, k=2, weight=None, normalized=False, seed=1
        )
        # python versions give different results with same seed
        b_approx1 = {0: 0.0, 1: 1.5, 2: 0.0}
        b_approx2 = {0: 0.0, 1: 0.75, 2: 0.0}
        for n in sorted(G):
            assert b[n] in (b_approx1[n], b_approx2[n])

    def test_P3_endpoints(self):
        """Betweenness centrality: P3 endpoints"""
        G = nx.path_graph(3)
        b_answer = {0: 2.0, 1: 3.0, 2: 2.0}
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=False, endpoints=True
        )
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])
        # normalized = True case
        b_answer = {0: 2 / 3, 1: 1.0, 2: 2 / 3}
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=True, endpoints=True
        )
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_krackhardt_kite_graph(self):
        """Betweenness centrality: Krackhardt kite graph"""
        G = nx.krackhardt_kite_graph()
        G = nx.Graph(G)
        b_answer = {
            0: 1.667,
            1: 1.667,
            2: 0.000,
            3: 7.333,
            4: 0.000,
            5: 16.667,
            6: 16.667,
            7: 28.000,
            8: 16.000,
            9: 0.000,
        }
        for b in b_answer:
            b_answer[b] /= 2
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_krackhardt_kite_graph_normalized(self):
        """Betweenness centrality: Krackhardt kite graph normalized"""
        G = nx.krackhardt_kite_graph()
        G = nx.Graph(G)
        b_answer = {
            0: 0.023,
            1: 0.023,
            2: 0.000,
            3: 0.102,
            4: 0.000,
            5: 0.231,
            6: 0.231,
            7: 0.389,
            8: 0.222,
            9: 0.000,
        }
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=True)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_florentine_families_graph(self):
        """Betweenness centrality: Florentine families graph"""
        G = nx.florentine_families_graph()
        b_answer = {
            "Acciaiuoli": 0.000,
            "Albizzi": 0.212,
            "Barbadori": 0.093,
            "Bischeri": 0.104,
            "Castellani": 0.055,
            "Ginori": 0.000,
            "Guadagni": 0.255,
            "Lamberteschi": 0.000,
            "Medici": 0.522,
            "Pazzi": 0.000,
            "Peruzzi": 0.022,
            "Ridolfi": 0.114,
            "Salviati": 0.143,
            "Strozzi": 0.103,
            "Tornabuoni": 0.092,
        }

        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=True)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_les_miserables_graph(self):
        """Betweenness centrality: Les Miserables graph"""
        G = nx.les_miserables_graph()
        b_answer = {
            "Napoleon": 0.000,
            "Myriel": 0.177,
            "MlleBaptistine": 0.000,
            "MmeMagloire": 0.000,
            "CountessDeLo": 0.000,
            "Geborand": 0.000,
            "Champtercier": 0.000,
            "Cravatte": 0.000,
            "Count": 0.000,
            "OldMan": 0.000,
            "Valjean": 0.570,
            "Labarre": 0.000,
            "Marguerite": 0.000,
            "MmeDeR": 0.000,
            "Isabeau": 0.000,
            "Gervais": 0.000,
            "Listolier": 0.000,
            "Tholomyes": 0.041,
            "Fameuil": 0.000,
            "Blacheville": 0.000,
            "Favourite": 0.000,
            "Dahlia": 0.000,
            "Zephine": 0.000,
            "Fantine": 0.130,
            "MmeThenardier": 0.029,
            "Thenardier": 0.075,
            "Cosette": 0.024,
            "Javert": 0.054,
            "Fauchelevent": 0.026,
            "Bamatabois": 0.008,
            "Perpetue": 0.000,
            "Simplice": 0.009,
            "Scaufflaire": 0.000,
            "Woman1": 0.000,
            "Judge": 0.000,
            "Champmathieu": 0.000,
            "Brevet": 0.000,
            "Chenildieu": 0.000,
            "Cochepaille": 0.000,
            "Pontmercy": 0.007,
            "Boulatruelle": 0.000,
            "Eponine": 0.011,
            "Anzelma": 0.000,
            "Woman2": 0.000,
            "MotherInnocent": 0.000,
            "Gribier": 0.000,
            "MmeBurgon": 0.026,
            "Jondrette": 0.000,
            "Gavroche": 0.165,
            "Gillenormand": 0.020,
            "Magnon": 0.000,
            "MlleGillenormand": 0.048,
            "MmePontmercy": 0.000,
            "MlleVaubois": 0.000,
            "LtGillenormand": 0.000,
            "Marius": 0.132,
            "BaronessT": 0.000,
            "Mabeuf": 0.028,
            "Enjolras": 0.043,
            "Combeferre": 0.001,
            "Prouvaire": 0.000,
            "Feuilly": 0.001,
            "Courfeyrac": 0.005,
            "Bahorel": 0.002,
            "Bossuet": 0.031,
            "Joly": 0.002,
            "Grantaire": 0.000,
            "MotherPlutarch": 0.000,
            "Gueulemer": 0.005,
            "Babet": 0.005,
            "Claquesous": 0.005,
            "Montparnasse": 0.004,
            "Toussaint": 0.000,
            "Child1": 0.000,
            "Child2": 0.000,
            "Brujon": 0.000,
            "MmeHucheloup": 0.000,
        }

        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=True)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_ladder_graph(self):
        """Betweenness centrality: Ladder graph"""
        G = nx.Graph()  # ladder_graph(3)
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (4, 5), (3, 5)])
        b_answer = {0: 1.667, 1: 1.667, 2: 6.667, 3: 6.667, 4: 1.667, 5: 1.667}
        for b in b_answer:
            b_answer[b] /= 2
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_disconnected_path(self):
        """Betweenness centrality: disconnected path"""
        G = nx.Graph()
        nx.add_path(G, [0, 1, 2])
        nx.add_path(G, [3, 4, 5, 6])
        b_answer = {0: 0, 1: 1, 2: 0, 3: 0, 4: 2, 5: 2, 6: 0}
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_disconnected_path_endpoints(self):
        """Betweenness centrality: disconnected path endpoints"""
        G = nx.Graph()
        nx.add_path(G, [0, 1, 2])
        nx.add_path(G, [3, 4, 5, 6])
        b_answer = {0: 2, 1: 3, 2: 2, 3: 3, 4: 5, 5: 5, 6: 3}
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=False, endpoints=True
        )
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])
        # normalized = True case
        b = nx.builtin.betweenness_centrality(
            G, weight=None, normalized=True, endpoints=True
        )
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n] / 21)

    def test_directed_path(self):
        """Betweenness centrality: directed path"""
        G = nx.DiGraph()
        nx.add_path(G, [0, 1, 2])
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=False)
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_directed_path_normalized(self):
        """Betweenness centrality: directed path normalized"""
        G = nx.DiGraph()
        nx.add_path(G, [0, 1, 2])
        b = nx.builtin.betweenness_centrality(G, weight=None, normalized=True)
        b_answer = {0: 0.0, 1: 0.5, 2: 0.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])


@pytest.mark.usefixtures("graphscope_session")
class TestWeightedBetweennessCentrality:
    def test_K5(self):
        """Weighted betweenness centrality: K5"""
        G = nx.complete_graph(5)
        for e in G.edges:
            G.edges[e]["weight"] = 1
        G[1][2]["weight"] = 10
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = {0: 0.333, 1: 0.0, 2: 0.0, 3: 0.333, 4: 0.333}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_P3_normalized(self):
        """Weighted betweenness centrality: P3 normalized"""
        G = nx.path_graph(3)
        for e in G.edges:
            G.edges[e]["weight"] = 1
        G[1][2]["weight"] = 10
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=True)
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_P3(self):
        """Weighted betweenness centrality: P3"""
        G = nx.path_graph(3)
        for e in G.edges:
            G.edges[e]["weight"] = 1
        G[1][2]["weight"] = 10
        b_answer = {0: 0.0, 1: 1.0, 2: 0.0}
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_krackhardt_kite_graph(self):
        """Weighted betweenness centrality: Krackhardt kite graph"""
        G = nx.krackhardt_kite_graph()
        G = nx.Graph(G)
        for e in G.edges:
            G.edges[e]["weight"] = 1
        b_answer = {
            0: 1.667,
            1: 1.667,
            2: 0.000,
            3: 7.333,
            4: 0.000,
            5: 16.667,
            6: 16.667,
            7: 28.000,
            8: 16.000,
            9: 0.000,
        }
        for b in b_answer:
            b_answer[b] /= 2

        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)

        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_krackhardt_kite_graph_normalized(self):
        """Weighted betweenness centrality:
        Krackhardt kite graph normalized
        """
        G = nx.krackhardt_kite_graph()
        G = nx.Graph(G)
        for e in G.edges:
            G.edges[e]["weight"] = 1
        b_answer = {
            0: 0.023,
            1: 0.023,
            2: 0.000,
            3: 0.102,
            4: 0.000,
            5: 0.231,
            6: 0.231,
            7: 0.389,
            8: 0.222,
            9: 0.000,
        }
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=True)

        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_florentine_families_graph(self):
        """Weighted betweenness centrality:
        Florentine families graph"""
        G = nx.florentine_families_graph()
        for e in G.edges:
            G.edges[e]["weight"] = 1
        b_answer = {
            "Acciaiuoli": 0.000,
            "Albizzi": 0.212,
            "Barbadori": 0.093,
            "Bischeri": 0.104,
            "Castellani": 0.055,
            "Ginori": 0.000,
            "Guadagni": 0.255,
            "Lamberteschi": 0.000,
            "Medici": 0.522,
            "Pazzi": 0.000,
            "Peruzzi": 0.022,
            "Ridolfi": 0.114,
            "Salviati": 0.143,
            "Strozzi": 0.103,
            "Tornabuoni": 0.092,
        }

        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=True)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_les_miserables_graph(self):
        """Weighted betweenness centrality: Les Miserables graph"""
        G = nx.les_miserables_graph()
        for e in G.edges:
            G.edges[e]["weight"] = 1
        b_answer = {
            "Anzelma": 0.000,
            "Babet": 14.137,
            "Bahorel": 6.229,
            "Bamatabois": 22.917,
            "BaronessT": 0.000,
            "Blacheville": 0.000,
            "Bossuet": 87.648,
            "Boulatruelle": 0.000,
            "Brevet": 0.000,
            "Brujon": 1.250,
            "Champmathieu": 0.000,
            "Champtercier": 0.000,
            "Chenildieu": 0.000,
            "Child1": 0.000,
            "Child2": 0.000,
            "Claquesous": 13.856,
            "Cochepaille": 0.000,
            "Combeferre": 3.563,
            "Cosette": 67.819,
            "Count": 0.000,
            "CountessDeLo": 0.000,
            "Courfeyrac": 15.011,
            "Cravatte": 0.000,
            "Dahlia": 0.000,
            "Enjolras": 121.277,
            "Eponine": 32.740,
            "Fameuil": 0.000,
            "Fantine": 369.487,
            "Fauchelevent": 75.500,
            "Favourite": 0.000,
            "Feuilly": 3.563,
            "Gavroche": 470.571,
            "Geborand": 0.000,
            "Gervais": 0.000,
            "Gillenormand": 57.600,
            "Grantaire": 0.429,
            "Gribier": 0.000,
            "Gueulemer": 14.137,
            "Isabeau": 0.000,
            "Javert": 154.845,
            "Joly": 6.229,
            "Jondrette": 0.000,
            "Judge": 0.000,
            "Labarre": 0.000,
            "Listolier": 0.000,
            "LtGillenormand": 0.000,
            "Mabeuf": 78.835,
            "Magnon": 0.619,
            "Marguerite": 0.000,
            "Marius": 376.293,
            "MlleBaptistine": 0.000,
            "MlleGillenormand": 135.657,
            "MlleVaubois": 0.000,
            "MmeBurgon": 75.000,
            "MmeDeR": 0.000,
            "MmeHucheloup": 0.000,
            "MmeMagloire": 0.000,
            "MmePontmercy": 1.000,
            "MmeThenardier": 82.657,
            "Montparnasse": 11.040,
            "MotherInnocent": 0.000,
            "MotherPlutarch": 0.000,
            "Myriel": 504.000,
            "Napoleon": 0.000,
            "OldMan": 0.000,
            "Perpetue": 0.000,
            "Pontmercy": 19.7375,
            "Prouvaire": 0.000,
            "Scaufflaire": 0.000,
            "Simplice": 24.625,
            "Thenardier": 213.468,
            "Tholomyes": 115.794,
            "Toussaint": 0.000,
            "Valjean": 1624.469,
            "Woman1": 0.000,
            "Woman2": 0.000,
            "Zephine": 0.000,
        }

        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_ladder_graph(self):
        """Weighted betweenness centrality: Ladder graph"""
        G = nx.Graph()  # ladder_graph(3)
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (4, 5), (3, 5)])
        for e in G.edges:
            G.edges[e]["weight"] = 1
        b_answer = {0: 1.667, 1: 1.667, 2: 6.667, 3: 6.667, 4: 1.667, 5: 1.667}
        for b in b_answer:
            b_answer[b] /= 2
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n], 3)

    def test_G(self):
        """Weighted betweenness centrality: G"""
        G = weighted_G()
        b_answer = {0: 2.0, 1: 0.0, 2: 4.0, 3: 3.0, 4: 4.0, 5: 0.0}
        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])

    def test_G2(self):
        """Weighted betweenness centrality: G2"""
        G = nx.DiGraph()
        G.add_weighted_edges_from(
            [
                ("s", "u", 10),
                ("s", "x", 5),
                ("u", "v", 1),
                ("u", "x", 2),
                ("v", "y", 1),
                ("x", "u", 3),
                ("x", "v", 5),
                ("x", "y", 2),
                ("y", "s", 7),
                ("y", "v", 6),
            ]
        )

        b_answer = {"y": 5.0, "x": 5.0, "s": 4.0, "u": 2.0, "v": 2.0}

        b = nx.builtin.betweenness_centrality(G, weight="weight", normalized=False)
        for n in sorted(G):
            assert almost_equal(b[n], b_answer[n])


@pytest.mark.usefixtures("graphscope_session")
@pytest.mark.skip(reason="not supported")
class TestEdgeBetweennessCentrality:
    def test_K5(self):
        """Edge betweenness centrality: K5"""
        G = nx.complete_graph(5)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=False)
        b_answer = dict.fromkeys(G.edges(), 1)
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_normalized_K5(self):
        """Edge betweenness centrality: K5"""
        G = nx.complete_graph(5)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=True)
        b_answer = dict.fromkeys(G.edges(), 1 / 10)
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_C4(self):
        """Edge betweenness centrality: C4"""
        G = nx.cycle_graph(4)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=True)
        b_answer = {(0, 1): 2, (0, 3): 2, (1, 2): 2, (2, 3): 2}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_P4(self):
        """Edge betweenness centrality: P4"""
        G = nx.path_graph(4)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=False)
        b_answer = {(0, 1): 3, (1, 2): 4, (2, 3): 3}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_normalized_P4(self):
        """Edge betweenness centrality: P4"""
        G = nx.path_graph(4)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=True)
        b_answer = {(0, 1): 3, (1, 2): 4, (2, 3): 3}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_balanced_tree(self):
        """Edge betweenness centrality: balanced tree"""
        G = nx.balanced_tree(r=2, h=2)
        b = nx.edge_betweenness_centrality(G, weight=None, normalized=False)
        b_answer = {(0, 1): 12, (0, 2): 12, (1, 3): 6, (1, 4): 6, (2, 5): 6, (2, 6): 6}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])


@pytest.mark.usefixtures("graphscope_session")
@pytest.mark.skip(reason="not supported")
class TestWeightedEdgeBetweennessCentrality:
    def test_K5(self):
        """Edge betweenness centrality: K5"""
        G = nx.complete_graph(5)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = dict.fromkeys(G.edges(), 1)
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_C4(self):
        """Edge betweenness centrality: C4"""
        G = nx.cycle_graph(4)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = {(0, 1): 2, (0, 3): 2, (1, 2): 2, (2, 3): 2}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_P4(self):
        """Edge betweenness centrality: P4"""
        G = nx.path_graph(4)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = {(0, 1): 3, (1, 2): 4, (2, 3): 3}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_balanced_tree(self):
        """Edge betweenness centrality: balanced tree"""
        G = nx.balanced_tree(r=2, h=2)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = {(0, 1): 12, (0, 2): 12, (1, 3): 6, (1, 4): 6, (2, 5): 6, (2, 6): 6}
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_weighted_graph(self):
        eList = [
            (0, 1, 5),
            (0, 2, 4),
            (0, 3, 3),
            (0, 4, 2),
            (1, 2, 4),
            (1, 3, 1),
            (1, 4, 3),
            (2, 4, 5),
            (3, 4, 4),
        ]
        G = nx.Graph()
        G.add_weighted_edges_from(eList)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=False)
        b_answer = {
            (0, 1): 0.0,
            (0, 2): 1.0,
            (0, 3): 2.0,
            (0, 4): 1.0,
            (1, 2): 2.0,
            (1, 3): 3.5,
            (1, 4): 1.5,
            (2, 4): 1.0,
            (3, 4): 0.5,
        }
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])

    def test_normalized_weighted_graph(self):
        eList = [
            (0, 1, 5),
            (0, 2, 4),
            (0, 3, 3),
            (0, 4, 2),
            (1, 2, 4),
            (1, 3, 1),
            (1, 4, 3),
            (2, 4, 5),
            (3, 4, 4),
        ]
        G = nx.Graph()
        G.add_weighted_edges_from(eList)
        b = nx.edge_betweenness_centrality(G, weight="weight", normalized=True)
        b_answer = {
            (0, 1): 0.0,
            (0, 2): 1.0,
            (0, 3): 2.0,
            (0, 4): 1.0,
            (1, 2): 2.0,
            (1, 3): 3.5,
            (1, 4): 1.5,
            (2, 4): 1.0,
            (3, 4): 0.5,
        }
        norm = len(G) * (len(G) - 1) / 2
        for n in sorted(G.edges()):
            assert almost_equal(b[n], b_answer[n])
