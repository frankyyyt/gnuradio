#!/usr/bin/env python
#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy
from gnuradio import gr, gr_unittest, blocks

class py_hier_add_const_ff(gr.hier_block2):
    def __init__(self, k):
        gr.hier_block2.__init__(
            self,
            "hier_add_const_ff",
            gr.io_signature(1, 1, gr.sizeof_float),
            gr.io_signature(1, 1, gr.sizeof_float)
        )
        self.add = blocks.add_const_ff(k)
        self.connect(self, self.add, self)

class test_top_block(gr_unittest.TestCase):

    def setUp(self):
        self.tb0 = gr.top_block()
        self.tb1 = gr.top_block()

    def tearDown(self):
        self.tb0 = None
        self.tb1 = None

    def test_000(self):
        # Test that everything works fine with two independent top_blocks

        data0 = 10*[0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  10]
        data1 = 10*[0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10]
        src0 = blocks.vector_source_f(data0, False)
        src1 = blocks.vector_source_f(data1, False)
        add0 = blocks.add_const_ff(1)
        add1 = blocks.add_const_ff(1)
        snk0 = blocks.null_sink(gr.sizeof_float)
        snk1 = blocks.null_sink(gr.sizeof_float)

        self.tb0.connect(src0, add0, snk0)
        self.tb1.connect(src1, add1, snk1)
        self.tb0.start()
        self.assertRaises(None, self.tb1.start())

    def test_001(self):
        # Test that it raises RuntimeError when sharing a block
        # between two top_blocks

        data0 = 10*[0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  10]
        data1 = 10*[0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10]
        src0 = blocks.vector_source_f(data0, False)
        src1 = blocks.vector_source_f(data1, False)
        add  = blocks.add_const_ff(1)
        snk0 = blocks.null_sink(gr.sizeof_float)
        snk1 = blocks.null_sink(gr.sizeof_float)

        self.tb0.connect(src0, add, snk0)
        self.tb1.connect(src1, add, snk1)
        self.tb0.start()
        self.assertRaises(RuntimeError, self.tb1.start)

    def test_002(self):
        # Test that it raises RuntimeError when sharing a Python
        # hier_block2 between two top_blocks

        data0 = 10*[0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  10]
        data1 = 10*[0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10]
        src0 = blocks.vector_source_f(data0, False)
        src1 = blocks.vector_source_f(data1, False)
        add  = py_hier_add_const_ff(1)
        snk0 = blocks.null_sink(gr.sizeof_float)
        snk1 = blocks.null_sink(gr.sizeof_float)

        self.tb0.connect(src0, add, snk0)
        self.tb1.connect(src1, add, snk1)
        self.tb0.start()
        self.assertRaises(RuntimeError, self.tb1.start)

if __name__ == '__main__':
    gr_unittest.run(test_top_block, "test_top_block.xml")
