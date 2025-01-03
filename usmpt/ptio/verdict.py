"""
Verdict Module

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

__author__ = "Nicolas AMAT, ONERA/DTIS, Université de Toulouse"
__contact__ = "nicolas.amat@onera.fr"
__license__ = "GPLv3"
__version__ = "1.0"

from enum import Enum


class Verdict(Enum):
    """ Verdict enum.

        Note
        ----
        REACHABLE -> F reachable
        NOT_REACHABLE -> -F invariant (F not reachable)
        UNKNOWN
    """
    REACHABLE = 2
    NOT_REACHABLE = 1
    UNKNOWN = 3
