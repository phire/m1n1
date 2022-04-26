# SPDX-License-Identifier: MIT

from m1n1.utils import *

trace_device("/arm-io/sgx", False)
trace_device("/arm-io/pmp", False)
trace_device("/arm-io/gfx-asc", False)

from m1n1.trace.asc import ASCTracer

ASCTracer = ASCTracer._reloadcls()

# gfx_tracer = ASCTracer(hv, "/arm-io/gfx-asc", verbose=True)
# gfx_tracer.start()

from m1n1.trace.agx import AGXTracer
AGXTracer = AGXTracer._reloadcls()

gfx_tracer = AGXTracer(hv, "/arm-io/gfx-asc", verbose=False)
gfx_tracer.start()

trace_range(irange(gfx_tracer.gpu_region, gfx_tracer.gpu_region_size), mode=TraceMode.SYNC)
trace_range(irange(gfx_tracer.gfx_shared_region, gfx_tracer.gfx_shared_region_size), mode=TraceMode.SYNC)
trace_range(irange(gfx_tracer.gfx_handoff, gfx_tracer.gfx_handoff_size), mode=TraceMode.SYNC)


# Trace the entire mmio range around the GPU
# node = hv.adt["/arm-io/sgx"]
# addr, size = node.get_reg(0)
# hv.trace_range(irange(addr, 0x1000000), TraceMode.SYNC)

def trace_all_gfx_io():
    # These are all the IO ranges that get mapped into the UAT iommu pagetable
    # Trace them so we can see if any of them are being written by the CPU

    # page (8): fa010020000 ... fa010023fff -> 000000020e100000 [8000020e100447]
    hv.trace_range(irange(0x20e100000, 0x4000), mode=TraceMode.SYNC)

    # page (10): fa010028000 ... fa01002bfff -> 000000028e104000 [c000028e104447]
    hv.trace_range(irange(0x20e100000, 0x4000), mode=TraceMode.SYNC)

    # page (22): fa010058000 ... fa01005bfff -> 000000028e494000 [8000028e494447]
    hv.trace_range(irange(0x28e494000, 0x4000), mode=TraceMode.SYNC)

    # page (28): fa010070000 ... fa010073fff -> 0000000204d60000 [c0000204d60447]
    hv.trace_range(irange(0x204d60000, 0x4000), mode=TraceMode.SYNC)

    # page (30): fa010078000 ... fa01007bfff -> 0000000200000000 [c0000200000447]
    #    to
    # page (83): fa01014c000 ... fa01014ffff -> 00000002000d4000 [c00002000d4447]
    hv.trace_range(irange(0x200000000, 0xd5000), mode=TraceMode.SYNC)

    # page (84): fa010150000 ... fa010153fff -> 0000000201000000 [c0000201000447]
    #page (137): fa010224000 ... fa010227fff -> 00000002010d4000 [c00002010d4447]
    hv.trace_range(irange(0x201000000, 0xd5000), mode=TraceMode.SYNC)

    # page (138): fa010228000 ... fa01022bfff -> 0000000202000000 [c0000202000447]
    # page (191): fa0102fc000 ... fa0102fffff -> 00000002020d4000 [c00002020d4447]
    hv.trace_range(irange(0x202000000, 0xd5000), mode=TraceMode.SYNC)

    # page (192): fa010300000 ... fa010303fff -> 0000000203000000 [c0000203000447]
    hv.trace_range(irange(0x203000000, 0xd5000), mode=TraceMode.SYNC)
    hv.trace_range(irange(0x204000000, 0xd5000), mode=TraceMode.SYNC)
    hv.trace_range(irange(0x205000000, 0xd5000), mode=TraceMode.SYNC)
    hv.trace_range(irange(0x206000000, 0xd5000), mode=TraceMode.SYNC)
    hv.trace_range(irange(0x207000000, 0xd5000), mode=TraceMode.SYNC)

    # page (464): fa010740000 ... fa010743fff -> 00000002643c4000 [c00002643c4447]
    hv.trace_range(irange(0x2643c4000, 0x4000), mode=TraceMode.SYNC)
    # page (466): fa010748000 ... fa01074bfff -> 000000028e3d0000 [c000028e3d0447]
    hv.trace_range(irange(0x28e3d0000, 0x4000), mode=TraceMode.SYNC)
    # page (468): fa010750000 ... fa010753fff -> 000000028e3c0000 [8000028e3c0447]
    hv.trace_range(irange(0x28e3c0000, 0x4000), mode=TraceMode.SYNC)

    # page (8): f9100020000 ... f9100023fff -> 0000000406000000 [60000406000447]
    # page (263): f910041c000 ... f910041ffff -> 00000004063fc000 [600004063fc447]
    hv.trace_range(irange(0x2643c4000, 0x63fc000), mode=TraceMode.SYNC)

def trace_gpu_irqs():
    # Trace sgx interrupts
    node = hv.adt["/arm-io/sgx"]
    for irq in getattr(node, "interrupts"):
        hv.trace_irq(f"{node.name} {irq}", irq, 1, hv.IRQTRACE_IRQ)

    # Trace gfx-asc interrupts
    node = hv.adt["/arm-io/gfx-asc"]
    for irq in getattr(node, "interrupts"):
        hv.trace_irq(f"{node.name} {irq}", irq, 1, hv.IRQTRACE_IRQ)
