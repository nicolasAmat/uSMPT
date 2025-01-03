#!/usr/bin/env python3

"""
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

from cx_Freeze import setup, Executable


setup(
    name="uSMPT",
    version="1.0",
    description="uSMPT - An environnement to experiment with SMT-based model checking for Petri nets",
    author="Nicolas Amat, ONERA/DTIS, Université de Toulouse",
    author_email="nicolas.amat@onera.fr",
    executables=[Executable("usmpt/__main__.py", targetName="usmpt.exe")]
)
