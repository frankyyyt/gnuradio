/* -*- c++ -*- */
/* Copyright 2012,2014 Free Software Foundation, Inc.
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

#ifndef INCLUDED_DIGITAL_PACKET_FORMATTER_OFDM_H
#define INCLUDED_DIGITAL_PACKET_FORMATTER_OFDM_H

#include <vector>
#include <gnuradio/digital/api.h>
#include <gnuradio/digital/packet_formatter_1.h>

namespace gr {
  namespace digital {

    /*!
     * \brief Header utility for OFDM signals.
     * \ingroup packet_operators_blk
     * \ingroup ofdm_blk
     */
    class DIGITAL_API packet_formatter_ofdm
      : public packet_formatter_1
    {
     public:
      packet_formatter_ofdm(const std::vector<std::vector<int> > &occupied_carriers,
                            int n_syms,
                            const std::string &len_tag_key="packet_len",
                            const std::string &frame_len_tag_key="frame_len",
                            const std::string &num_tag_key="packet_num",
                            int bits_per_header_sym=1,
                            int bits_per_payload_sym=1,
                            bool scramble_header=false);
      ~packet_formatter_ofdm();

      /*!
       * \brief Header formatter.
       *
       * Does the same as packet_header_default::header_formatter(), but
       * optionally scrambles the bits (this is more important for OFDM to avoid
       * PAPR spikes).
       */
      virtual bool format(int nbytes_in,
                          const unsigned char *input,
                          pmt::pmt_t &output,
                          pmt::pmt_t &info);

      /*!
       * \brief Inverse function to header_formatter().
       *
       * Does the same as packet_header_default::header_parser(), but
       * adds another tag that stores the number of OFDM symbols in the
       * packet.
       * Note that there is usually no linear connection between the number
       * of OFDM symbols and the packet length because a packet might
       * finish mid-OFDM-symbol.
       */
      virtual bool parse(int nbits_in,
                         const unsigned char *input,
                         std::vector<pmt::pmt_t> &info);

      /*!
       * \param occupied_carriers See carrier allocator
       * \param n_syms The number of OFDM symbols the header should be (usually 1)
       * \param len_tag_key The stream tag key used to set the length of the packet.
       * \param frame_len_tag_key The stream tag key used to set the length of the frame.
       * \param num_tag_key The tag key that carries the frame number.
       * \param bits_per_header_sym Bits per complex symbol in the header, e.g. 1 if
       *                            the header is BPSK modulated, 2 if it's QPSK
       *                            modulated etc.
       * \param bits_per_payload_sym Bits per complex symbol in the payload. This is
       *                             required to figure out how many OFDM symbols
       *                             are necessary to encode the given number of
       *                             bytes.
       * \param scramble_header Set this to true to scramble the bits. This is highly
       *                        recommended, as it reduces PAPR spikes.
       */
      static sptr make(const std::vector<std::vector<int> > &occupied_carriers,
                       int n_syms,
                       const std::string &len_tag_key="packet_len",
                       const std::string &frame_len_tag_key="frame_len",
                       const std::string &num_tag_key="packet_num",
                       int bits_per_header_sym=1,
                       int bits_per_payload_sym=1,
                       bool scramble_header=false);


    protected:
      pmt::pmt_t d_frame_len_tag_key; //!< Tag key of the additional frame length tag
      const std::vector<std::vector<int> > d_occupied_carriers; //!< Which carriers/symbols carry data
      int d_syms_per_set; //!< Helper variable: Total number of elements in d_occupied_carriers
      int d_bits_per_payload_sym;
      std::vector<unsigned char> d_scramble_mask; //!< Bits are xor'd with this before tx'ing

    private:
      int _get_header_len_from_occupied_carriers(const std::vector<std::vector<int> > &occupied_carriers, int n_syms);
    };

  } // namespace digital
} // namespace gr

#endif /* INCLUDED_DIGITAL_PACKET_FORMATTER_OFDM_H */