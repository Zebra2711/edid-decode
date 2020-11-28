// SPDX-License-Identifier: MIT
/*
 * Copyright 2019-2020 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
 *
 * Author: Hans Verkuil <hverkuil-cisco@xs4all.nl>
 */

#include "edid-decode.h"

void edid_state::parse_vtb_ext_block(const unsigned char *x)
{
	printf("  Version: %u\n", x[1]);
	if (x[1] != 1)
		fail("Invalid version %u.\n", x[1]);

	unsigned num_dtd = x[2];
	unsigned num_cvt = x[3];
	unsigned num_st = x[4];

	x += 5;
	if (num_dtd) {
		printf("  Detailed Timing Descriptors:\n");
		for (unsigned i = 0; i < num_dtd; i++, x += 18)
			detailed_timings("    ", x, false);
	}
	if (num_cvt) {
		printf("  Coordinated Video Timings:\n");
		for (unsigned i = 0; i < num_cvt; i++, x += 3)
			detailed_cvt_descriptor("    ", x, false);
	}
	if (num_st) {
		// Note: the VTB-EXT standard has a mistake in the example EDID
		// that it provides: there the refresh rate (bits 5-0 of the
		// second byte) is set to 60 for 60 Hz, but this should be 0
		// since the actual refresh rate is the value + 60.
		//
		// The documentation itself is correct, though.
		printf("  Standard Timings:\n");
		for (unsigned i = 0; i < num_st; i++, x += 2)
			print_standard_timing("    ", x[0], x[1], true);
	}
}
