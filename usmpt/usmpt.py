"""
uSMPT: An environnement to experiment with SMT-based model checking for Petri nets

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

from argparse import ArgumentParser
from time import time

from usmpt.exec.parallelizer import Parallelizer
from usmpt.ptio.formula import Formula
from usmpt.ptio.ptnet import PetriNet
from usmpt.exec.utils import set_verbose

def main():
    """ Main function.
    """
    # Start time
    start_time = time()

    # Arguments parser
    parser = ArgumentParser(description='uSMPT: An environnement to experiment with SMT-based model checking for Petri nets')

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0',
                        help="show the version number and exit")

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help="increase output verbosity")

    parser.add_argument('--debug',
                        action='store_true',
                        help="print the SMT-LIB input/output")

    parser.add_argument('-n', '--net',
                        metavar='ptnet',
                        type=str,
                        required=True,
                        help='path to Petri Net (.net format)')

    group_properties = parser.add_mutually_exclusive_group(required=True)

    group_properties.add_argument('-ff', '--formula-file',
                                  action='store',
                                  dest='path_formula',
                                  type=str,
                                  help='path to reachability formula')

    group_properties.add_argument('-f', '--formula',
                                  action='store',
                                  dest='formula',
                                  type=str,
                                  help='reachability formula')

    group_methods = parser.add_mutually_exclusive_group(required=True)

    methods = ['STATE-EQUATION', 'INDUCTION', 'BMC', 'K-INDUCTION', 'DUMMY']

    group_methods.add_argument('--methods',
                               default=methods,
                               nargs='*',
                               choices=methods,
                               help='enable methods among {}'.format(' '.join(methods)))

    group_timeout = parser.add_mutually_exclusive_group()

    group_timeout.add_argument('--timeout',
                               action='store',
                               dest='timeout',
                               type=int,
                               default=225,
                               help='a limit on execution time')

    parser.add_argument('--show-time',
                        action='store_true',
                        help="show the execution time")

    results = parser.parse_args()

    # Set the verbose level
    set_verbose(results.verbose)

    # Read the input Petri net and formula
    ptnet = PetriNet(results.net)
    formula = Formula(formula=results.formula) if results.formula else Formula(path_formula=results.path_formula)
    if results.verbose:
        print(ptnet)
        print(formula)

    if 'DUMMY' in results.methods:
        exit()

    # Run methods in parallel and get results
    parallelizer = Parallelizer(ptnet, formula, results.methods, verbose=results.verbose, debug=results.debug)
    parallelizer.run(results.timeout)

    if results.show_time:
        print("# Time:", time() - start_time)


if __name__ == '__main__':
    main()
