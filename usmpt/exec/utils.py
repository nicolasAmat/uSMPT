"""
Utils to Manage Processes

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

import os
import signal
import logging as log

STOP = signal.SIGTERM
KILL = signal.SIGTERM if os.name == 'nt' else signal.SIGKILL


def send_signal_pids(pids: list[int], signal_to_send: signal.Signals):
    """ Send a signal to a list of processes
        (except the current process).

    Parameters
    ----------
    pids : list of int
        List of processes.
    signal_to_send : Signals
        Signal to send.
    """
    current_pid = os.getpid()

    for pid in pids:
        # Do not send a signal to the current process
        if pid == current_pid:
            continue

        try:
            os.kill(pid, signal_to_send)
        except OSError:
            pass


def send_signal_group_pid(pid: int, signal_to_send: signal.Signals):
    """ Send a signal to the group pid of a given process.
 
    Parameters
    ----------
    pid : int
        Process.
    signal_to_send : Signals
        Signal to send.
    """
    try:
        os.killpg(os.getpgid(pid), signal_to_send)
    except ProcessLookupError:
        pass

def set_verbose(verbose: bool) -> None:
    # Set the verbose level
    if verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(message)s")