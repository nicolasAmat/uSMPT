"""
Parallelizer module

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

from multiprocessing import Process, Queue
from time import time
from typing import Optional

from usmpt.checkers.bmc import BMC
from usmpt.checkers.induction import Induction
from usmpt.checkers.kinduction import KInduction
from usmpt.checkers.statequation import StateEquation
from usmpt.exec.utils import KILL, send_signal_group_pid, send_signal_pids
from usmpt.ptio.formula import Formula
from usmpt.ptio.ptnet import PetriNet
from usmpt.ptio.verdict import Verdict


class Parallelizer:
    """ Helper to manage methods in parallel.

    Attributes
    ----------
    ptnet : Petri net
        Petri net to analyze.
    formula : Formula
        Reachability formula to verify.
    methods : list of str
        List of methods to be run in parallel.
    processes : list of Process
        List of processes corresponding to the methods.
    results : list of Queue of tuple of Verdict, Marking
        List of Queue to store the verdicts corresponding to the methods.
    solver_pids : Queue of int
        Queue of solver pids.
    """

    def __init__(self, ptnet: PetriNet, formula: Formula, methods: list[str], verbose: bool = False, debug: bool = False):
        """ Initializer.

        Parameters
        ----------
        ptnet : PetriNet
            Initial Petri net.
        formula : Formula
            Reachability formula.
        methods : list of str
            List of methods to be run in parallel.
        debug : bool, optional
            Debugging flag.
        """
        # Query: Petri net and formula
        self.ptnet: PetriNet = ptnet
        self.formula: Formula = formula

        # Flags
        self.verbose: bool = verbose
        self.debug: bool = debug
        
        # Methods to run
        self.methods: list[str] = methods
        if 'K-INDUCTION' in methods and 'BMC' not in methods:
            self.methods.append("BMC")

        # Process information
        self.processes: list[Process] = []

        # Create queues to store the results
        self.results: list[Queue[Verdict]] = [Queue() for _ in methods]

        # Create queue to store solver pids
        self.solver_pids: Queue[int] = Queue()

        # If k-induction enabled create a queue to store the current iteration of BMC
        self.induction_queue: Optional[Queue[int]] = None
        if 'K-INDUCTION' in methods:
            self.induction_queue = Queue()

    def __getstate__(self):
        # Capture what is normally pickled
        state = self.__dict__.copy()

        # Remove unpicklable variable 
        state['processes'] = None
        return state

    def prove(self, method, result, concurrent_pids):
        """ Instantiate methods.
        """
        if method == 'INDUCTION':
            prover = Induction(self.ptnet, self.formula, verbose=self.verbose, debug=self.debug, solver_pids=self.solver_pids)

        if method == 'BMC':
            prover = BMC(self.ptnet, self.formula, verbose=self.verbose, debug=self.debug, induction_queue=self.induction_queue, solver_pids=self.solver_pids)

        if method == 'K-INDUCTION':
            prover = KInduction(self.ptnet, self.formula, verbose=self.verbose, debug=self.debug, induction_queue=self.induction_queue)

        if method == 'STATE-EQUATION':
            prover = StateEquation(self.ptnet, self.formula, verbose=self.verbose, debug=self.debug, solver_pids=self.solver_pids)

        prover.prove(result, concurrent_pids=concurrent_pids)

    def run(self, timeout=225) -> None:
        """ Run analysis in parallel.

        Parameters
        ----------
        timeout : int, optional
            Time limit.
        """
        # Exit if no methods to run
        if not self.methods:
            return None

        # Create a queue to share the pids of the concurrent methods
        concurrent_pids: Queue[list[int]] = Queue()

        # Create processes
        self.processes = [Process(target=self.prove, args=(method, result, concurrent_pids,)) for method, result in zip(self.methods, self.results)]

        # Start processes
        pids = []
        for proc in self.processes:
            proc.start()
            if proc.pid is not None:
                pids.append(proc.pid)
        concurrent_pids.put(pids)

        self.handle(timeout)

    def handle(self, timeout: int) -> None:
        """ Handle the methods.

        Parameters
        ----------
        timeout : int
            Time limit.
        """
        # Get the starting time
        start_time = time()

        # Join processes
        # Wait for the first process
        self.processes[0].join(timeout=timeout)
        # Wait for the other processes (in case of aborted method)
        if len(self.processes) > 1:
            for proc in self.processes[1:]:
                proc.join(timeout=timeout - (time() - start_time))

        # Return result data if one method finished
        for result_method in self.results:
            if not result_method.empty():

                verdict = result_method.get()
                print("FORMULA " + self.formula.result(verdict))

                self.stop()

        # Otherwise stop the methods
        self.stop()

        return None

    def stop(self) -> None:
        """ Stop the methods.
        """
        # Kill methods
        send_signal_pids([proc.pid for proc in self.processes if proc.pid is not None], KILL)

        # Kill solvers
        while not self.solver_pids.empty():
            send_signal_group_pid(self.solver_pids.get(), KILL)
