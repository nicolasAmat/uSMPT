"""
Formula Module

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

__author__ = "Nicolas AMAT, ONERA/DTIS, Université de Toulouse"
__contact__ = "nicolas.amat@onera.fr"
__license__ = "GPLv3"
__version__ = "1.0"

from abc import ABC, abstractmethod
from collections import deque
from re import search, split
from typing import Optional, Sequence

from usmpt.ptio.verdict import Verdict

LTL_TO_BOOLEAN_OPERATORS = {
    '-': 'not',
    '/\\': 'and',
    '\\/': 'or'
}

LTL_TO_BOOLEAN_CONSTANTS = {
    'T': True,
    'F': False
}


class Formula:
    """ Properties.

    Attributes
    ----------
    F : Expression
        Reachability formula.
    """

    def __init__(self, formula: Optional[str] = None, path_formula: Optional[str] = None) -> None:
        """ Initializer.

        Parameters
        ----------
        formula : str, optional
            Reachability formula.
        path_formula : str, optional
            Path to reachability formula.
        """
        if formula is None:
            if path_formula is not None:
                with open(path_formula, 'r') as fp:
                    formula = fp.read().strip()
            else:
                raise ValueError

        self.F: Expression = self.parse_formula(formula)

    def __str__(self) -> str:
        """ Properties to textual format.

        Returns
        -------
        str
            Debugging format.
        """
        return str(self.F)

    def smtlib(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        """ Assert the property.

        Parameters
        ----------
        k : int, optional
            Iteration number.
        assertion : bool, optional
            Assertion flag.
        negation : bool, optional
            Negation flag.

        Returns
        -------
        str
            SMT-LIB format.
        """
        return self.F.smtlib(k, assertion=assertion, negation=negation)

    def smtlib_sat(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        """ Assert the property.

        Parameters
        ----------
        k : int, optional
            Iteration number.
        assertion : bool, optional
            Assertion flag.
        negation : bool, optional
            Negation flag.

        Returns
        -------
        str
            SMT-LIB format.
        """
        return self.F.smtlib_sat(k, assertion=assertion, negation=negation)

    def parse_formula(self, formula: str) -> Expression:
        """ Formula parser.

        Parameters
        ----------
        formula : str
            Formula (.ltl format).

        Returns
        -------
        Expression
            Parsed formula.
        """
        def _tokenize(s):
            tokens = []
            buffer, last = "", ""
            open_brace = False

            for c in s:

                if c == ' ':
                    continue

                elif (c == '/' and last == '\\') or (c == '\\' and last == '/'):
                    if buffer:
                        tokens.append(buffer)
                    tokens.append(last + c)
                    buffer, last = "", ""

                elif (c == '-' and not open_brace) or c in ['(', ')']:
                    if last:
                        tokens.append(buffer + last)
                    tokens.append(c)
                    buffer, last = "", ""

                elif c == '{':
                    open_brace = True

                elif c == '}':
                    open_brace = False

                else:
                    buffer += last
                    last = c

            if buffer or last:
                tokens.append(buffer + last)

            return tokens

        def _member_constructor(member):
            places, integer_constant, multipliers = [], 0, {}

            for element in member.split('+'):
                if element.isnumeric():
                    integer_constant += int(element)
                else:
                    split_element = element.split('*')
                    variable = split_element[-1]
                    places.append(variable)

                    if len(split_element) > 1:
                        multipliers[variable] = int(split_element[0])

            if places:
                return TokenCount(places, multipliers)
            else:
                return IntegerConstant(integer_constant)

        # Number of opened parenthesis (not close)
        open_parenthesis = 0

        # Stacks: operators and operands
        stack_operator: deque[tuple[str, int]] = deque()
        stack_operands: deque[list[Expression]] = deque([[]])

        # Current operator
        current_operator = None

        # Parse atom
        parse_atom = False

        for token in _tokenize(formula):

            if token in ['', ' ']:
                continue

            if token in ['-', '/\\', '\\/']:
                # Get the current operator
                token_operator = LTL_TO_BOOLEAN_OPERATORS[token]

                if current_operator:
                    # If the current operator is different from the previous one, construct the previous sub-formula
                    if current_operator != token_operator:
                        stack_operands[-1] = [StateFormula(stack_operands[-1], stack_operator.pop()[0])]
                else:
                    # Add the current operator to the stack
                    stack_operator.append((token_operator, open_parenthesis))
                    current_operator = token_operator

            elif token == '(':
                # Increment the number of parenthesis
                open_parenthesis += 1

                # Add new current operands list
                stack_operands.append([])

                # Reset the last operator
                current_operator = None

            elif token == ')':
                # Fail if no open parenthesis previously
                if not open_parenthesis:
                    raise ValueError("Unbalanced parentheses")

                # Decrease the number of open parenthesis
                open_parenthesis -= 1

                # Add to the previous list
                operands = stack_operands.pop()
                if current_operator:
                    stack_operands[-1].append(StateFormula(operands, stack_operator.pop()[0]))
                else:
                    stack_operands[-1].append(operands[0])

                current_operator = stack_operator[-1][0] if stack_operator and stack_operator[-1][-1] == open_parenthesis else None

            elif token in ['T', 'F']:
                # Construct BooleanConstant
                stack_operands[-1].append(BooleanConstant(token == 'T'))

            else:
                # Construct Atom
                if search("(<=|>=|!=|<|>|=)", token):
                    if parse_atom:
                        _, operator, right = split("(<=|>=|<|>|=)", token)
                        stack_operands[-1].append(Atom(stack_operands[-1].pop(), _member_constructor(right), operator))
                        parse_atom = False

                    else:
                        left, operator, right = split("(<=|>=|!=|<|>|=)", token)
                        stack_operands[-1].append(Atom(_member_constructor(left), _member_constructor(right), operator))
                else:
                    stack_operands[-1].append(_member_constructor(token))
                    parse_atom = True

        if open_parenthesis:
            raise ValueError("Unbalances parentheses")

        if stack_operator:
            operands = stack_operands.pop()
            operator = stack_operator.pop()[0]
            return StateFormula(operands, operator)
        else:
            return stack_operands.pop()[0]


    def result(self, verdict: Verdict) -> str:
        """ Return the result according to the reachability of the feared events R.

        Parameters
        ----------
        verdict : Verdict
            Verdict of the formula.

        Returns
        -------
        str
            "REACHABLE", "NOT REACHABLE" or "UNKNOWN".
        """
        if verdict == Verdict.REACHABLE:
            return "REACHABLE"
        elif verdict == Verdict.NOT_REACHABLE:
            return "NOT REACHABLE"

        return "UNKNOWN"


class SimpleExpression(ABC):
    """ Simple Expression.

    Note
    ----
    Cannot be evaluated to 'TRUE' or 'FALSE'.
    """

    @abstractmethod
    def __str__(self) -> str:
        """ SimpleExpression to textual format.

        Returns
        -------
        str
            Debugging format.
        """
        pass

    @abstractmethod
    def smtlib(self, k: Optional[int] = None) -> str:
        """ Assert the SimpleExpression.

        Parameters
        ----------
        k : int, optional
            Iteration number.

        Returns
        -------
        str
            SMT-LIB format.
        """
        pass

    @abstractmethod
    def smtlib_sat(self, k: Optional[int] = None) -> str:
        """ Assert the SimpleExpression.

        Parameters
        ----------
        k : int, optional
            Iteration number.

        Returns
        -------
        str
            SMT-LIB format.
        """
        pass

class Expression(SimpleExpression):
    """ Expression.

    Note
    ----
    Can be evaluated to 'TRUE' or 'FALSE'.
    """

    @abstractmethod
    def smtlib(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        """ Assert the Expression.

        Parameters
        ----------
        k : int, optional
            Iteration number.
        assertion : bool
            Assertion flag.
        negation : bool
            Negation flag.

        Returns
        -------
        str
            SMT-LIB format.
        """
        pass

    @abstractmethod
    def smtlib_sat(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        """ Assert the Expression.

        Parameters
        ----------
        k : int, optional
            Iteration number.
        assertion : bool
            Assertion flag.
        negation : bool
            Negation flag.

        Returns
        -------
        str
            SMT-LIB format.
        """
        pass


class StateFormula(Expression):
    """ StateFormula.

    Attributes
    ----------
    operands : list of Expression
        A list of operands.
    operator : str
        A boolean operator (not, and, or).
    """

    def __init__(self, operands: Sequence[Expression], operator: str) -> None:
        """ Initializer.

        Parameters
        ----------
        operands : Sequence[Expression]
            List of operands.
        operator : str
            Operator (not, and, or).

        Raises
        ------
        ValueError
            Invalid operator for a StateFormula.
        """
        self.operands: Sequence[Expression] = operands

        self.operator: str = ''
        if operator in ['not', 'and', 'or']:
            self.operator = operator
        else:
            raise ValueError("Invalid operator for a state formula")

    def __str__(self) -> str:
        if self.operator == 'not':
            return "(not {})".format(self.operands[0])

        text = " {} ".format(self.operator).join(map(str, self.operands))

        if len(self.operands) > 1:
            text = "({})".format(text)

        return text

    def smtlib(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        smt_input = ' '.join(map(lambda operand: operand.smtlib(k), self.operands))

        if len(self.operands) > 1 or self.operator == 'not':
            smt_input = "({} {})".format(self.operator, smt_input)

        if negation:
            smt_input = "(not {})".format(smt_input)

        if assertion:
            smt_input = "(assert {})\n".format(smt_input)

        return smt_input

    def smtlib_sat(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        smt_input = ' '.join(map(lambda operand: operand.smtlib_sat(k), self.operands))

        if len(self.operands) > 1 or self.operator == 'not':
            smt_input = "({} {})".format(self.operator, smt_input)

        if negation:
            smt_input = "(not {})".format(smt_input)

        if assertion:
            smt_input = "(assert {})\n".format(smt_input)

        return smt_input


class Atom(Expression):
    """ Atom.

    Attributes
    ----------
    left_operand : Expression
        Left operand.
    right_operand : Expression
        Right operand.
    operator : str
        Operator (=, <=, >=, <, >, distinct).
    """

    def __init__(self, left_operand: SimpleExpression, right_operand: SimpleExpression, operator: str) -> None:
        """ Initializer.

        Parameters
        ----------
        left_operand : SimpleExpression
            Left operand.
        right_operand : SimpleExpression
            Right operand.
        operator : str
            Operator (=, <=, >=, <, >, distinct).

        Raises
        ------
        ValueError
            Invalid operator for an Atom.
        """
        if operator not in ['=', '<=', '>=', '<', '>', '!=']:
            raise ValueError("Invalid operator for an atom")

        self.left_operand: SimpleExpression = left_operand
        self.right_operand: SimpleExpression = right_operand

        self.operator: str = operator if operator != '!=' else 'distinct'

    def __str__(self) -> str:
        return "({} {} {})".format(self.left_operand, self.operator, self.right_operand)

    def smtlib(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        smt_input = "({} {} {})".format(self.operator, self.left_operand.smtlib(k), self.right_operand.smtlib(k))

        if negation:
            smt_input = "(not {})".format(smt_input)

        if assertion:
            smt_input = "(assert {})\n".format(smt_input)

        return smt_input

    def smtlib_sat(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        assert self.operator in ['=', 'distinct']
        smt_input = "({} {} {})".format(self.operator, self.left_operand.smtlib_sat(k), self.right_operand.smtlib_sat(k))

        if negation:
            smt_input = "(not {})".format(smt_input)

        if assertion:
            smt_input = "(assert {})\n".format(smt_input)

        return smt_input


class BooleanConstant(Expression):
    """ Boolean constant.

    Attributes
    ----------
    value : bool
        A boolean constant.
    """

    def __init__(self, value: bool) -> None:
        """ Initializer.

        Parameters
        ----------
        value : bool
            A boolean constant.
        """
        self.value: bool = value

    def __str__(self) -> str:
        return str(self.value)

    def smtlib(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        smt_input = str(self).lower()

        if negation:
            smt_input = "(not {})".format(smt_input)

        if assertion:
            smt_input = "(assert {})\n".format(smt_input)

        return smt_input

    def smtlib_sat(self, k: Optional[int] = None, assertion: bool = False, negation: bool = False) -> str:
        return self.smtlib(k=k, assertion=assertion, negation=negation)


class TokenCount(SimpleExpression):
    """ Token count.

    k_1 * p_1 + ... + k_n * p_n + K

    Attributes
    ----------
    places : list of Places
        A list of places to sum.
    multipliers : dict of Place: int, optional
        Place multipliers (missing if 1).
    integer_constant : int, optional
        Constant.
    """

    def __init__(self, places: list[str], multipliers: Optional[dict[str, int]] = None, integer_constant: Optional[int] = None):
        """ Initializer.

        Parameters
        ----------
        places : list of str
            A list of places to sum.
        multipliers : dict of Place: int, optional
            Place multipliers (missing if 1 or 0).
        integer_constant : int, optional
            Constant.
        """
        self.places: list[str] = places
        self.multipliers: Optional[dict[str, int]] = multipliers
        self.integer_constant: Optional[int] = integer_constant

    def __str__(self) -> str:
        text = ' + '.join(map(lambda pl: pl if self.multipliers is None or pl not in self.multipliers else "({}.{})".format(self.multipliers[pl], pl), self.places))

        if self.integer_constant:
            text += " + " + str(self.integer_constant)

        return text

    def smtlib(self, k: Optional[int] = None) -> str:
        def place_smtlib(pl, k):
            pl_iteration = pl if k is None else "{}@{}".format(pl, k)
            return pl_iteration if self.multipliers is None or pl not in self.multipliers else "(* {} {})".format(pl_iteration, self.multipliers[pl])

        smt_input = ' '.join(map(lambda pl: place_smtlib(pl, k), self.places))

        if self.integer_constant:
            smt_input += ' ' + str(self.integer_constant)

        if len(self.places) > 1 or self.integer_constant:
            smt_input = "(+ {})".format(smt_input)

        return smt_input

    def smtlib_sat(self, k: Optional[int] = None) -> str:
        assert not self.integer_constant
        assert not self.multipliers
        smt_input = ' '.join(map(lambda pl: pl if k is None else "{}@{}".format(pl, k), self.places))

        if len(self.places) > 1 or self.integer_constant:
            smt_input = "(or {})".format(smt_input)

        return smt_input

class IntegerConstant(SimpleExpression):
    """ Integer constant.

    Attributes
    ----------
    value : int
        Constant.
    """

    def __init__(self, value: int) -> None:
        """ Initializer.

        Parameters
        ----------
        value : int
            Constant.
        """
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def smtlib(self, k: Optional[int] = None) -> str:
        return str(self)

    def smtlib_sat(self, k: Optional[int] = None) -> str:
        assert self.value in [0, 1]
        if self.value:
            return "true"
        else:
            return "false"
