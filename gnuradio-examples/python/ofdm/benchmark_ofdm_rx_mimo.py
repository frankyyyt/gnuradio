#!/usr/bin/env python
#
# Copyright 2006, 2007 Free Software Foundation, Inc.
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

from gnuradio import gr, blks2
from gnuradio import usrp
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import struct, sys

# from current dir
from receive_path_mimo import receive_path_mimo
import fusb_options

class my_top_block(gr.top_block):
    def __init__(self, callback, options):
        gr.top_block.__init__(self)

        self._rx_freq            = options.rx_freq         # receiver's center frequency
        self._rx_gain            = options.rx_gain         # receiver's gain
        self._rx_subdev_spec     = options.rx_subdev_spec  # daughterboard to use
        self._decim              = options.decim           # Decimating rate for the USRP (prelim)
        self._fusb_block_size    = options.fusb_block_size # usb info for USRP
        self._fusb_nblocks       = options.fusb_nblocks    # usb info for USRP
        self._rx_ant             = options.rx_ant
        if self._rx_freq is None:
            sys.stderr.write("-f FREQ or --freq FREQ or --rx-freq FREQ must be specified\n")
            raise SystemExit

        # Set up USRP source
        self._setup_usrp_source()
        ok = self.set_freq(self._rx_freq)
        if not ok:
            print "Failed to set Rx frequency to %s" % (eng_notation.num_to_str(self._rx_freq))
            raise ValueError, eng_notation.num_to_str(self._rx_freq)
        g = self.subdevA.gain_range()
        if options.show_rx_gain_range:
            print "Rx Gain Range: minimum = %g, maximum = %g, step size = %g" \
                  % (g[0], g[1], g[2])
        self.set_gain(options.rx_gain)
        self.set_auto_tr(True)                 # enable Auto Transmit/Receive switching

        # Set up receive path
        self.rxpath = receive_path_mimo(callback, options)

        self.connect(self.u, self.rxpath)

        
    def _setup_usrp_source(self):
        if(self._rx_ant == 2):
            self.u = usrp.source_c (which=0, nchan=2,
                                    fusb_block_size=self._fusb_block_size,
                                    fusb_nblocks=self._fusb_nblocks)
            adc_rate = self.u.adc_rate()

            self.u.set_decim_rate(self._decim)
            
            # determine the daughterboard subdevice we're using
            subdev_spec_a = (0, 0)
            subdev_spec_b = (1, 0)
            self.subdevA = self.u.selected_subdev(subdev_spec_a)
            self.subdevB = self.u.selected_subdev(subdev_spec_b)
            
            mux = self.u.determine_rx_mux_value(subdev_spec_a, subdev_spec_b)
            self.u.set_mux(mux)

        else:
            self.u = usrp.source_c (which=0,
                                    fusb_block_size=self._fusb_block_size,
                                    fusb_nblocks=self._fusb_nblocks)
            adc_rate = self.u.adc_rate()

            self.u.set_decim_rate(self._decim)
            
            # determine the daughterboard subdevice we're using
            subdev_spec_a = (0, 0)
            self.subdevA = self.u.selected_subdev(subdev_spec_a)
            
            mux = self.u.determine_rx_mux_value(subdev_spec_a)
            self.u.set_mux(mux)

            

    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.

        @param target_freq: frequency in Hz
        @rypte: bool

        Tuning is a two step process.  First we ask the front-end to
        tune as close to the desired frequency as it can.  Then we use
        the result of that operation and our target_frequency to
        determine the value for the digital up converter.
        """

        if(self._rx_ant == 2):
            ra = self.u.tune(0, self.subdevA, target_freq)
            rb = self.u.tune(1, self.subdevB, target_freq)
            if ra and rb:
                return True
            
            return False
        else:
            ra = self.u.tune(0, self.subdevA, target_freq)
            if ra:
                return True
            
            return False
            

    def set_gain(self, gain):
        """
        Sets the analog gain in the USRP
        """
        if(self._rx_ant == 2):
            if gain is None:
                r = self.subdevA.gain_range()
                gain = (r[0] + r[1])/2               # set gain to midpoint
            self.gain = gain
            ra = self.subdevA.set_gain(gain)
            rb = self.subdevB.set_gain(gain)
            return ra and rb

        else:
            if gain is None:
                r = self.subdevA.gain_range()
                gain = (r[0] + r[1])/2               # set gain to midpoint
            self.gain = gain
            ra = self.subdevA.set_gain(gain)
            return ra

    def set_auto_tr(self, enable):
        if(self._rx_ant == 2):
            ra = self.subdevA.set_auto_tr(enable)
            rb = self.subdevB.set_auto_tr(enable)
            return ra and rb
        else:
            ra = self.subdevA.set_auto_tr(enable)
            return ra


    def decim(self):
        return self._decim

    def add_options(normal, expert):
        """
        Adds usrp-specific options to the Options Parser
        """
        add_freq_option(normal)
        normal.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                          help="select USRP Rx side A or B")
        normal.add_option("", "--rx-gain", type="eng_float", default=None, metavar="GAIN",
                          help="set receiver gain in dB [default=midpoint].  See also --show-rx-gain-range")
        normal.add_option("", "--show-rx-gain-range", action="store_true", default=False, 
                          help="print min and max Rx gain available on selected daughterboard")
        normal.add_option("-v", "--verbose", action="store_true", default=False)

        expert.add_option("", "--rx-freq", type="eng_float", default=None,
                          help="set Rx frequency to FREQ [default=%default]", metavar="FREQ")
        expert.add_option("-d", "--decim", type="intx", default=64,
                          help="set fpga decimation rate to DECIM [default=%default]")
        expert.add_option("", "--snr", type="eng_float", default=30,
                          help="set the SNR of the channel in dB [default=%default]")
   

    # Make a static method to call before instantiation
    add_options = staticmethod(add_options)

def add_freq_option(parser):
    """
    Hackery that has the -f / --freq option set both tx_freq and rx_freq
    """
    def freq_callback(option, opt_str, value, parser):
        parser.values.rx_freq = value
        parser.values.tx_freq = value

    if not parser.has_option('--freq'):
        parser.add_option('-f', '--freq', type="eng_float",
                          action="callback", callback=freq_callback,
                          help="set Tx and/or Rx frequency to FREQ [default=%default]",
                          metavar="FREQ")

# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

def main():

    global n_rcvd, n_right
        
    n_rcvd = 0
    n_right = 0

    def rx_callback(ok, payload):
        global n_rcvd, n_right
        n_rcvd += 1
        (pktno,) = struct.unpack('!H', payload[0:2])
        if ok:
            n_right += 1
        print "ok: %r \t pktno: %d \t n_rcvd: %d \t n_right: %d" % (ok, pktno, n_rcvd, n_right)

        if 0:
            printlst = list()
            for x in payload[2:]:
                t = hex(ord(x)).replace('0x', '')
                if(len(t) == 1):
                    t = '0' + t
                printlst.append(t)
            printable = ''.join(printlst)

            print printable
            print "\n"

    parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")
    parser.add_option("","--discontinuous", action="store_true", default=False,
                      help="enable discontinuous")

    my_top_block.add_options(parser, expert_grp)
    receive_path_mimo.add_options(parser, expert_grp)
    blks2.ofdm_mimo_mod.add_options(parser, expert_grp)
    blks2.ofdm_mimo_demod.add_options(parser, expert_grp)
    fusb_options.add_options(expert_grp)

    (options, args) = parser.parse_args ()

    # build the graph
    tb = my_top_block(rx_callback, options)

    r = gr.enable_realtime_scheduling()
    if r != gr.RT_OK:
        print "Warning: failed to enable realtime scheduling"

    tb.start()                      # start flow graph
    tb.wait()                       # wait for it to finish

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
