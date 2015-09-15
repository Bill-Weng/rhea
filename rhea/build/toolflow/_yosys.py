#
# Copyright (c) 2015 Christopher Felton
#

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sys
import os

import sys
import os

from ._toolflow import _toolflow
from ._convert import convert


class Yosys(_toolflow):
    _name = "yosys"

    def __init__(self, brd, top=None, path='./yosys/'):
        """ use yosys synthesis (mainly for testing)

        This toolflow creates more than the actual tool supports.
        This is done for automated testing.  Many of the vendor
        FPGA tools are not convienently installable on the CI
        environments.
        """
        super(Yosys, self).__init__(brd, top=top, path=path)
        self.sdc_file = ''
        self._core_file_list = set()
        self._default_project_file = None

    def add_cores(self, filename):
        self._core_file_list.update(set(filename))

    def create_project(self, use='verilog', **pattr):
        # yosys only synthesizes verilog
        assert use.lower() == 'verilog'

        self.syn_file = os.path.join(self.path, self.name+'.ys')
        syn  = "# -------------------------------------------------------------------------- #\n"
        syn += "# Autogenerated by rhea.build \n"
        syn += "# -------------------------------------------------------------------------- #\n\n"

        for f in self._hdl_file_list:
            syn += "read_verilog {}/{} \n".format(self.path, f)

        # create "dummy" pin assignments (testing only)
        for port_name, port in self.brd.ports.items():
            if port.inuse:
                _pins = port.pins
                for ii, pn in enumerate(_pins):
                    syn += "#set_location_assignment PIN_{} -to ".format(str(pn))
                    if len(_pins) == 1:
                        syn += "\"{}\" ".format(port_name)
                    else:
                        syn += "\"{}\[{:d}\]\" ".format(port_name, ii)
                    syn += "\n"
        syn += "#\n"

        syn += "# elaborate design hierarchy\n"
        syn += "hierarchy -check -top {}\n".format(self.name)
        syn += "\n"
        syn += "# high-level stuff\n"
        syn += "proc; opt; fsm; opt; memory; opt\n"
        syn += "\n"
        syn += "# mapping to internal cell lib\n"
        syn += "techmap; opt\n"
        syn += "clean \n"
        syn += "write_verilog {}/{}_synth.v \n".format(self.path, self.name)

        if pattr is not None and 'write_blif' in pattr:
            syn += "write_blif {}/{}".format(self.path, self.name+'.blif')
            
        with open(self.syn_file, 'w') as f:
            f.write(syn)
        return

    def run(self, use='verilog', name=None):
        self.pathexist(self.path)
        cfiles = convert(self.brd, name=self.name,
                         use=use, path=self.path)
        self.add_files(cfiles)
        self.create_project(use=use)
        # @todo: self.create_constraints()

        cmd = ['yosys', self.syn_file]
        self.logfn = "build_yosys.log"
        self._execute_flow(cmd)

        return self.logfn
