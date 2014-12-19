/* -*- c++ -*- */
/* Copyright 2014 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <iostream>
#include <iomanip>
#include <string.h>
#include <volk/volk.h>
#include <gnuradio/digital/packet_formatter_counter.h>
#include <gnuradio/math.h>

namespace gr {
  namespace digital {

    packet_formatter_counter::sptr
    packet_formatter_counter::make(const std::string &access_code, int bps)
    {
      return packet_formatter_counter::sptr
        (new packet_formatter_counter(access_code, bps));
    }

    packet_formatter_counter::packet_formatter_counter(const std::string &access_code, int bps)
      : packet_formatter_default(access_code)
    {
      d_bps = bps;
      d_counter = 0;
    }

    packet_formatter_counter::~packet_formatter_counter()
    {
    }

    bool
    packet_formatter_counter::format(int nbytes_in,
                                     const unsigned char *input,
                                     pmt::pmt_t &output,
                                     pmt::pmt_t &info)

    {
      size_t header_size = header_nbytes();
      uint8_t* bytes_out = (uint8_t*)volk_malloc(header_size*sizeof(uint8_t),
                                                 volk_get_alignment());

      uint16_t len = static_cast<uint16_t>(nbytes_in);
      volk_16u_byteswap(&len, 1);

      uint64_t ac = d_access_code;
      size_t ac_bytes = d_access_code_len/8;
      volk_64u_byteswap(&ac, 1);
      ac = ac >> (64-d_access_code_len);

      uint16_t bps = d_bps;
      volk_16u_byteswap(&bps, 1);

      uint16_t counter = d_counter;;
      volk_16u_byteswap(&counter, 1);

      // Copy access code, header info, and input to the output buffer
      int offset = 0;
      memcpy(bytes_out, &ac, ac_bytes);
      offset += ac_bytes;
      memcpy(&bytes_out[offset], &len, sizeof(uint16_t));
      offset += sizeof(uint16_t);
      memcpy(&bytes_out[offset], &len, sizeof(uint16_t));
      offset += sizeof(uint16_t);
      memcpy(&bytes_out[offset], &bps, sizeof(uint16_t));
      offset += sizeof(uint16_t);
      memcpy(&bytes_out[offset], &counter, sizeof(uint16_t));

      // Package output data into a PMT vector
      output = pmt::init_u8vector(header_size, bytes_out);

      // Creating the output pmt copies data; free our own here.
      volk_free(bytes_out);

      d_counter++;

      return true;
    }

    size_t
    packet_formatter_counter::header_nbits() const
    {
      return d_access_code_len + 8*4*sizeof(uint16_t);
    }

    size_t
    packet_formatter_counter::header_nbytes() const
    {
      return d_access_code_len/8 + 4*sizeof(uint16_t);
    }

    bool
    packet_formatter_counter::header_ok()
    {
      // confirm that two copies of header info are identical
      return (((d_hdr_reg >> 48) & 0xffff) ^ ((d_hdr_reg >> 32) & 0xffff)) == 0;
    }

    int
    packet_formatter_counter::header_payload()
    {
      uint16_t counter = (d_hdr_reg) & 0xffff;
      uint16_t bps = (d_hdr_reg >> 16) & 0xffff;
      uint16_t len = (d_hdr_reg >> 32) & 0xffff;

      d_bps = bps;

      d_info = pmt::make_dict();
      d_info = pmt::dict_add(d_info, pmt::intern("skip samps"),
                             pmt::from_long(d_count));
      d_info = pmt::dict_add(d_info, pmt::intern("payload bits"),
                             pmt::from_long(8*len));
      d_info = pmt::dict_add(d_info, pmt::intern("bps"),
                             pmt::from_long(bps));
      d_info = pmt::dict_add(d_info, pmt::intern("counter"),
                             pmt::from_long(counter));
      return len;
    }

  } /* namespace digital */
} /* namespace gr */
