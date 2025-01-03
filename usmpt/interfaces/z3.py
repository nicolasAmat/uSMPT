
"""
z3 Interface

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

from logging import warning
from multiprocessing import Queue
from os import name
from subprocess import PIPE, Popen
from sys import exit
from typing import Optional

from usmpt.interfaces.solver import Solver


class Z3(Solver):
    """ z3 interface.

    Note
    ----
    Uses SMT-LIB v2 format
    Standard: http://smtlib.cs.uiowa.edu/papers/smt-lib-reference-v2.6-r2017-07-18.pdf

    Dependency: https://github.com/Z3Prover/z3

    This class can easily be hacked to replace Z3
    by another SMT solver supporting the SMT-LIB format.

    Attributes
    ----------
    solver : Popen
        A z3 process.
    aborted : bool
        Aborted flag.
    debug : bool
        Debugging flag.
    """

    def __init__(self, debug: bool = False, timeout: int = 0, solver_pids: Optional[Queue] = None) -> None:
        """ Initializer.

        Parameters
        ----------
        debug : bool, optional
            Debugging flag.
        timeout : int, optional
            Timeout of the solver.
        solver_pids : Queue of int, optional
            Queue of solver pids.
        """
        # Solver
        if name == 'nt':
            process = ['z3.exe', '-in']
        else:
            process = ['z3', '-in']
        if timeout:
            process.append('-T:{}'.format(timeout))
        self.solver: Popen = Popen(' '.join(process), stdin=PIPE, stdout=PIPE, shell=True)

        if solver_pids is not None:
            solver_pids.put(self.solver.pid)

        # Flags
        self.aborted: bool = False
        self.debug: bool = debug

    def kill(self) -> None:
        """" Kill the process.
        """
        self.solver.kill()

    def abort(self) -> None:
        """ Abort the solver.
        """
        warning("z3 process has been aborted")
        self.solver.kill()
        self.aborted = True
        exit()

    def write(self, input: str, debug: bool = False) -> None:
        """ Write instructions to the standard input.

        Parameters
        ----------
        input : str 
            Input instructions.
        debug : bool
            Debugging flag.
        """
        if self.debug or debug:
            print(input)

        if input != "":
            try:
                if self.solver.stdin is None:
                    self.abort()
                else:
                    self.solver.stdin.write(bytes(input, 'utf-8'))
            except BrokenPipeError:
                self.abort()

    def flush(self) -> None:
        """ Flush the standard input.
        """
        try:
            if self.solver.stdin is None:
                self.abort()
            else:
                self.solver.stdin.flush()
        except BrokenPipeError:
            self.abort()

    def readline(self, debug: bool = False):
        """ Read a line from the standard output.

        Parameters
        ----------
        debug : bool, optional
            Debugging flag.

        Returns
        -------
        str
            Line read.
        """
        try:
            if self.solver.stdout is None:
                self.abort()
            else:
                smt_output = self.solver.stdout.readline().decode('utf-8').strip()
        except BrokenPipeError:
            self.abort()

        if self.debug or debug:
            print(smt_output)

        return smt_output

    def reset(self) -> None:
        """ Reset.

        Note
        ----
        Erase all assertions and declarations.
        """
        self.write("(reset)\n")

    def push(self):
        """ Push.

        Note
        ----
        Creates a new scope by saving the current stack size.
        """
        self.write("(push)\n")

    def pop(self) -> None:
        """ Pop.

        Note
        ----
        Removes any assertion or declaration performed between it and the last push.
        """
        self.write("(pop)\n")

    def check_sat(self, no_check: bool = False) -> Optional[bool]:
        """ Check the satisfiability of the current stack of z3.

        Parameters
        ----------
        no_check : bool
            Do not abort the solver in case of unknown verdict.

        Returns
        -------
        bool, optional
            Satisfiability of the current stack.
        """
        self.write("(check-sat)\n")
        self.flush()

        sat = self.readline()

        if sat == 'sat':
            return True
        elif sat == 'unsat':
            return False
        elif not no_check:
            self.abort()

        return None
