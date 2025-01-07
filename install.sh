#!/bin/bash

############################################################
# Script for installing dependencies (z3 and Tina toolbox) #
############################################################

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

cd $SCRIPT_DIR

wget https://github.com/Z3Prover/z3/releases/download/z3-4.13.4/z3-4.13.4-x64-glibc-2.35.zip
unzip z3-4.13.4-x64-glibc-2.35.zip
rm z3-4.13.4-x64-glibc-2.35.zip

wget https://projects.laas.fr/tina/binaries/tina-3.8.5-amd64-linux.tgz
tar xvf tina-3.8.5-amd64-linux.tgz
rm tina-3.8.5-amd64-linux.tgz

echo "export PATH=$SCRIPT_DIR/z3-4.13.4-x64-glibc-2.35/bin:$SCRIPT_DIR/tina-3.8.5/bin:\$PATH" >> ~/.bashrc
