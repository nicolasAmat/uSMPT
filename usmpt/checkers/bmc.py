"""
BMC (Bounded Model Checking) Method

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


from logging import info
from multiprocessing import Queue
from typing import Optional

from usmpt.checkers.abstractchecker import AbstractChecker
from usmpt.exec.utils import STOP, send_signal_pids, set_verbose
from usmpt.interfaces.z3 import Z3
from usmpt.ptio.formula import Formula
from usmpt.ptio.ptnet import PetriNet
from usmpt.ptio.verdict import Verdict


class BMC(AbstractChecker):
    """ Bounded Model Checking (BMC) method.

    Attributes
    ----------
    ptnet : PetriNet
        Initial Petri net.
    formula : Formula
        Reachability formula.
    debug : bool
        Debugging flag.
    induction_queue : Queue of int, optional
        Queue for the exchange with k-induction.
    show_model : bool
        Show model flag.
    solver : Z3
        SMT solver (Z3).
    """

    def __init__(self, ptnet: PetriNet, formula: Formula, verbose: bool = False, debug: bool = False, induction_queue: Optional[Queue[int]] = None, solver_pids: Optional[Queue[int]] = None) -> None:
        """ Initializer.

        Parameters
        ----------
        ptnet : PetriNet
            Initial Petri net.
        formula : Formula
            Reachability formula.
        debug : bool, optional
            Debugging flag.
        induction_queue : Queue of int, optional
            Queue for the exchange with k-induction.
        solver_pids : Queue of int, optional
            Queue to share the current PID.
        """
        # Initial Petri net
        self.ptnet: PetriNet = ptnet

        # Formula to study
        self.formula: Formula = formula

        # Verbosity
        self.verbose: bool = verbose
        
        # Debugging flag
        self.debug: bool = debug

        # Queue shared with K-Induction
        self.induction_queue: Optional[Queue[int]] = induction_queue

        # SMT solver
        self.solver: Z3 = Z3(debug=debug, solver_pids=solver_pids)

    def prove(self, result: Queue[Verdict], concurrent_pids: Queue[list[int]]) -> None:
        """ Prover.

        Parameters
        ----------
        result : Queue of Verdict
            Queue to exchange the verdict.
        concurrent_pids : Queue of int
            Queue to get the PIDs of the concurrent methods.
        """
        set_verbose(self.verbose)

        info("[BMC] RUNNING")

        order = self.prove_helper()

        # Quit if the solver has aborted
        if order is None or self.solver.aborted:
            return

        # Put the result in the queue
        if order == -1:
            result.put(Verdict.NOT_REACHABLE)
        else:
            result.put(Verdict.REACHABLE)

        # Kill the solver
        self.solver.kill()

        # Terminate concurrent methods
        if not concurrent_pids.empty():
            send_signal_pids(concurrent_pids.get(), STOP)

    def prove_helper(self) -> int:
        """ Prover to complete.

        Returns
        -------
        int
            Order of the sat query.
        """
        # Correction <<<
        i = 0

        self.solver.write(self.ptnet.smtlib_declare_places(i))
        self.solver.write(self.ptnet.smtlib_initial_marking(i))

        self.solver.push()
        self.solver.write(self.formula.smtlib_sat(i, assertion=True))

        while not self.solver.check_sat():
            self.solver.pop()

            i += 1
            self.solver.write(self.ptnet.smtlib_declare_places(i))

            # TODO 1: write the transition relation from i-1 to i
            # TODO 2: push
            # TODO 3: assert the formula with k = i

        return i
        # >>> Correction