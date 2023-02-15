"""
Petri Net Module

Input file format: .net
Standard: http://projects.laas.fr/tina//manuals/formats.html

This file is part of uSMPT.

uSMPT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

uSMPT is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with uSMPT. If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

__author__ = "Nicolas AMAT, LAAS-CNRS"
__contact__ = "nicolas.amat@laas.fr"
__license__ = "GPLv3"
__version__ = "1.0"

from re import split
from sys import exit
from typing import Optional

MULTIPLIER_TO_INT = {
    'K': 1000,
    'M': 1000000,
    'G': 1000000000,
    'T': 1000000000000,
    'P': 1000000000000000,
    'E': 1000000000000000000
}


class PetriNet:
    """ Petri net.

    Attributes
    ----------
    id : str
        Identifier.
    places : dict of str: Place
        Finite set of places (identified by names).
    transitions : dict of str: Transition
        Finite set of transitions (identified by names).
    initial_marking : Marking
        Initial marking.
    """

    def __init__(self, filename: str) -> None:
        """ Initializer.

        Parameters
        ----------
        filename : str
            Petri net filename.
        """
        self.id: str = ""

        self.places: dict[str, Place] = {}
        self.transitions: dict[str, Transition] = {}

        self.initial_marking: Marking = Marking()

        # Parse the `.net` file
        self.parse_net(filename)

    def __str__(self) -> str:
        """ Petri net to .net format.

        Returns
        -------
        str
            .net format.
        """
        text = "net {}\n".format(self.id)
        text += ''.join(map(str, self.places.values()))
        text += ''.join(map(str, self.transitions.values()))

        return text

    def parse_net(self, filename: str) -> None:
        """ Petri net parser.

        Parameters
        ----------
        filename : str
            Petri net filename (.net format).

        Raises
        ------
        FileNotFoundError
            Petri net file not found.
        """
        try:
            with open(filename, 'r') as fp:
                for line in fp.readlines():

                    # '#' and ',' forbidden in SMT-LIB
                    content = split(r'\s+', line.strip().replace('#', '.').replace(',', '.'))

                    # Skip empty lines and get the first identifier
                    if not content:
                        continue
                    else:
                        element = content.pop(0)

                    # Net id
                    if element == "net":
                        self.id = content[0]

                    # Transition arcs
                    if element == "tr":
                        self.parse_transition(content)

                    # Place
                    if element == "pl":
                        self.parse_place(content)
            fp.close()
        except FileNotFoundError as e:
            exit(e)

    def parse_transition(self, content: list[str]) -> None:
        """ Transition parser.

        Parameters
        ----------
        content : list of string
            Content to parse (.net format).
        """
        transition_id = content.pop(0)

        if transition_id in self.transitions:
            tr = self.transitions[transition_id]
        else:
            tr = Transition(transition_id, self)
            self.transitions[transition_id] = tr

        content = self.parse_label(content)

        arrow = content.index("->")
        inputs = content[0:arrow]
        outputs = content[arrow + 1:]

        for arc in inputs:
            tr.connected_places.append(self.parse_arc(arc, tr.pre))

        for arc in outputs:
            tr.connected_places.append(self.parse_arc(arc, tr.post))

    def parse_arc(self, content: str, arcs: dict[Place, int]) -> Place:
        """ Arc parser.

        Parameters
        ----------
        content : 
            Content to parse (.net format).
        arcs : dict of Place: int
            Current arcs.

        Returns
        -------
        Place
            Arc place.
        """
        content = content

        if '*' in content:
            place_id, _, weight_str = content.partition('*')
            weight = self.parse_value(weight_str)
        else:
            place_id = content
            weight = 1

        if place_id not in self.places:
            new_place = Place(place_id)
            self.places[place_id] = new_place
            self.initial_marking.tokens[new_place] = 0

        pl = self.places.get(place_id)
        arcs[pl] = weight

        return pl

    def parse_place(self, content: list[str]) -> None:
        """ Place parser.

        Parameters
        ----------
        content : list of str
            Place to parse (.net format).
        """
        place_id = content.pop(0)

        content = self.parse_label(content)

        if content:
            initial_marking = self.parse_value(
                content[0].replace('(', '').replace(')', ''))
        else:
            initial_marking = 0

        if place_id not in self.places:
            place = Place(place_id, initial_marking)
            self.places[place_id] = place
        else:
            place = self.places.get(place_id)
            place.initial_marking = initial_marking

        self.initial_marking.tokens[place] = initial_marking

    def parse_label(self, content: list[str]) -> list[str]:
        """ Label parser.

        Parameters
        ----------
        content : list of str
            Content to parse (.net format).

        Returns
        -------
        list of str
            Content without labels.

        """
        index = 0
        if content and content[index] == ':':
            label_skipped = content[index + 1][0] != '{'
            index = 2
            while not label_skipped:
                label_skipped = content[index][-1] == '}'
                index += 1
        return content[index:]

    def parse_value(self, content: str) -> int:
        """ Parse integer value.

        Parameters
        ----------
        content : str
            Content to parse (.net format).

        Returns
        -------
        int
            Corresponding integer value.

        Raises
        ------
        ValueError
            Incorrect integer value.

        """
        if content.isnumeric():
            return int(content)

        multiplier = content[-1]

        if multiplier not in MULTIPLIER_TO_INT:
            raise ValueError("Incorrect integer value")

        return int(content[:-1]) * MULTIPLIER_TO_INT[multiplier]

    def smtlib_declare_places(self, k: Optional[int] = None) -> str:
        # Correction <<<
        smt_input = ""

        for place in self.places.keys():
            place_str = place if k is None else place + "@" + str(k)
            smt_input += "(declare-fun {} () Bool)\n".format(place_str)

        return smt_input
        # >>> Correction

    def smtlib_initial_marking(self, k: Optional[int] = None) -> str:
        # Correction <<<
        return self.initial_marking.smtlib(k)
        # >>> Correction

    def smtlib_transition_relation(self, k: int, k_prime: int) -> str:
        pass


class Place:
    """ Place.

    Attributes
    ----------
    id : str
        An identifier.
    initial_marking : Marking
        Initial marking of the place.
    """

    def __init__(self, place_id: str, initial_marking: int = 0) -> None:
        """ Initializer.

        Parameters
        ----------
        place_id : str
            An identifier.
        initial_marking : int, optional
            Initial marking of the place.
        """
        self.id: str = place_id
        self.initial_marking: int = initial_marking

    def __str__(self) -> str:
        """ Place to .net format.

        Returns
        -------
        str
            .net format.
        """
        if self.initial_marking:
            return "pl {} ({})\n".format(self.id, self.initial_marking)
        else:
            return ""

    def smtlib(self, k: Optional[int] = None) -> str:
        pass

    def smtlib_declare(self, k: Optional[int] = None) -> str:
        pass


class Transition:
    """ Transition.

    Attributes
    ----------
    id : str
        An identifier.
    pre: dict of Place: int
        Pre vector.
    post: dict of Place: int
        Post vector.
    connected_places: list of Place
        List of the places connected to the transition.
    ptnet: PetriNet
        Associated Petri net.
    """

    def __init__(self, transition_id: str, ptnet: PetriNet) -> None:
        """ Initializer.

        Parameters
        ----------
        transition_id : str
            An identifier.
        ptnet : PetriNet
            Associated Petri net.
        """
        self.id: str = transition_id

        self.pre: dict[Place, int] = {}
        self.post: dict[Place, int] = {}

        self.connected_places: list[Place] = []
    
        self.ptnet: PetriNet = ptnet

    def __str__(self) -> str:
        """ Transition to textual format.
        
        Returns
        -------
        str
            .net format.
        """
        text = "tr {} ".format(self.id)

        for src, weight in self.pre.items():
            text += ' ' + self.str_arc(src, weight)

        text += ' ->'

        for dest, weight in self.post.items():
            text += ' ' + self.str_arc(dest, weight)
        
        text += '\n'
        return text

    def str_arc(self, place: Place, weight: int) -> str:
        """ Arc to textual format.

        Parameters
        ----------
        place : place
            Input place.
        weight : int
            Weight of the arc (negative if inhibitor).

        Returns
        -------
        str
            .net format.
        """
        text = place.id

        if weight:
            text += '*' + str(weight)

        return text

    def smtlib(self, k: int) -> str:
        pass

    def smtlib_declare(self) -> str:
        pass


class Marking:
    """ Marking.

    Attributes
    ----------
    tokens : dict of Place: int
        Number of tokens associated to the places.
    """

    def __init__(self, tokens: Optional[dict[Place, int]] = None) -> None:
        """ Initializer.

        Parameters
        ----------
        tokens : dict of Place: int, optional
            Number of tokens associated to the places.
        """
        self.tokens: dict[Place, int] = tokens if tokens is not None else {}

    def __str__(self) -> str:
        """ Marking to textual format.

        Returns
        -------
        str
            .net format.
        """
        text = ""

        for place, marking in self.tokens.items():
            if marking > 0:
                text += " {}({})".format(str(place.id), marking)

        if text == "":
            text = " empty marking"

        return text

    def smtlib(self, k: int = None) -> str:
        # Correction <<<
        smt_input = ""

        # Iterate over the dictionary
        for place, marking in self.tokens.items():

            # Create variable identifiers (suffix '@k')
            helper = place.id if k is None else place.id + "@" + str(k)

            # Assert variable if marking is 1
            if marking == 1:
                smt_input += "(assert {})\n".format(helper)

            # Assert negation of the variable if marking is 0
            elif marking == 0:
                smt_input += "(assert (not {}))\n".format(helper)
            else:
                raise ValueError

        return smt_input
        # >>> Correction