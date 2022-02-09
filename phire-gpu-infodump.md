# phire's M1x GPU infodump

All my work was done on my T6000 14" M1 Max with MacOS 12.2

So far, this is mostly an adventure to find how work is submitted to the GPU.


## UAT iommu (aka Unified Address Translator)

There is a reasonably complete implementation of UAT in m1n1/hw/uat.py

It is a 4 level pagetable:

 * L0: 2 entries
 * L1: 8 entries
 * L2: 2048 entries
 * L3: 2048 entries

Pages are fixed-sized at 16KB

The (slightly weird) layout allows for shared VM regions (above `0xf80_00000000`) to be in L0[1] and
all per-context allocations to be in L0[0], making for easy constriction of L0 tables for new contexts 

I have not found a TTBR register, or any registers. It seems gfx-asc is in full control of this iommu.
It does set up it's own pagetables for the private IO region

This has security implications, gfx-asc has access to every single physical page, and some (if not all)
MMIO registers. Panic messages from the MacOS kernel suggest there might be a "microPPL" running on
the gfx-asc coprocessor, similar to the PPL in MacOS, and that's hopefully the only part that can
modify page tables.

The MacOS kernel has a useful kernel option, `iouat_debug=1` that logs out all allocations and 
de-allocations in this address space.

See m1n1.hw.PTE for details on the PTE format

## GPU Virtual Address Space

MacOS (at least on my machine) uses GPU VAs in the following ranges:

`0x015_00000000`: Most userspace allocations  
`0x011_00000000`: Some additional userspace allocations  
`0x06f_ffff8000`: No idea. Only a single page
`0xf80_00000000`: ASC's private VM region, that it allocates itself. Mostly contains the ASC firmware  
This region lines up with `/arm-io/sgx/rtkit-private-vm-region-base`

`0xf80_10000000`: IO region mapped by ASC firmware. Only contains the ASC mailbox registers.  
`0xfa0_00000000`: Region where macos kernel allocates things  
`0xfa0_10000000`: IO region mapped by MacOS.  
Points to ASC regions, PMRG registers, MCC registers (and more?)

Pointers are sometimes sign extended, so you will sometimes see pointers in the range
`0xffffff80_00000000` or `0xffffffa0_00000000`, but there are only actually
40 bits of address space. Logs from the kernel usually report 44 bits, hence `0xfa_00000000` address

UAT is in control of this address space.

## gfx-asc

The ASC interface seems like it would be natural interface for submitting work.

However there is shocking little traffic on this interface, especially when
compared to what I've seen of DCP.

### Endpoints

 0x0: Standard Management, I didn't see anything weird here.  
 0x1: I called this Init. Only gets a single request/response during gfx initialization.  
0x20: I called this Pong. Receives regular "pongs"  
0x21: I called this Kick.  

#### Init

The entire traffic is:

    RX 0x0012000000000000
    TX 0x00104fa00c388000

And happens right around initialization

0xfa00c388000 is a GPU VA, and points at a single page allocation. the gfx firmware fills this with
a repeating pattern during initialization (16KB of repeating 0xef byte), and then never
touches it again.

#### Pong

I probably misnamed this, the number of Pong messages don't line up with kicks. Might be more of
a heartbeat, or might be the gfx firmware telling the cpu that it touched the pagetables.

There is also some more initialization that happens on this endpoint after the Init endpoint.

Messages:
`RX 0x0042000000000000`: The pong. Never sets the lower bits to anything other than zero.  
`TX 0x00810fa0000b0000`: Initialization, sent once  

##### Pong Initialization

 This also contains a GPU VA, pointing at a data structure that is prefilled by the cpu:

    >>> chexdump32(gfx.uat.ioread(0, 0xfa0000b0000, 0x4000))
    00000000  000b8000 ffffffa0 00000000 00000000 0c338000 ffffffa0 00020000 ffffffa0
    00000020  000c0000 ffffffa0 030e4000 240e0e08 40000008 00000001 00000000 ffffc000
    00000040  000003ff 00000000 00000070 190e0e08 40000800 00000001 00000000 ffffc000
    00000060  000003ff fe000000 0000000f 0e0e0e08 40000800 00000001 00000000 ffffc000
    00000080  000003ff 01ffc000 00000000 00000000 00000000 00000000 00000000 00000000
    000000a0  00000001 00000000 00000000 00000000 00000000 00000000 00000000 00000000
    000000c0  00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000

I called this ControlStruct in my m1n1/trace/agx.py code.

After initialization, the CPU never touches this.

unkptr_18 appears to be a heap or stack used by the asc-firmware?

#### Kick

The only message is

`TX 0x0083000000000000 | kick_type`

Where kick_type is a 5 bit number. When the MacOS isn't rendering anything, the only kicks seen are
0x00, 0x01, 0x10 and 0x11

But when the MacOS is actually rendering things, sometimes you see 0x08, 0x09 and 0x0a. Maybe more?

These Kicks might be triggering work submission, but with only 5 bits of entropy, the actual
information must be somewhere in shared memory. But at this point I have not found shared memory that
is altered between kicks. It's also possible I mislabeled this, and the kicks are actually TLB invalidation

## /arm-io/sgx's various shared memory ranges

Talking about shared memory, these are the obvious ones. Allocated by iboot and listed in ADT

**gpu-region-base:**

Single page containing the L0 tables for UAT. Controlled by CPU.

The L0 for a given context can be found at `gpu-region-base + context * 0x10`

**gfx-shared-region-base:**

Contains all the private pagetables that gfx-asc allocates itself during initialization.

Mostly controlled by gfx-asc, though the cpu controls the PPE `L0[1][2]` and points it to an L2 table
in it's own memory.

There seems to be a convention that the `L0[1]` PTE will point to the start of this region. 

**gfx-handoff-base:**

`0x10ffffb4000` : u64 - microPPL magic value of `0x4b1d000000000002`  
`0x10ffffb4008` : u64 - microPPL magic value of `0x4b1d000000000002`  

Corrupting this value results in the following panic:

    panic(cpu 4 caller 0xfffffe0013c5d848): UAT PPL 0xfffffdf030af4160 (IOUAT): 
    Invalid microPPL magic value found in the handoff region. 
    Expected: 0x4b1d000000000002, Actual: 0x0

`0x10ffffb4018` : u32 - Commonly read as u8 - initialized to 0xffffffff  
`0x10ffffb4038` : u32 - Flush state (commonly set to 0 or 2)  

The CPU has a pattern of setting this to 2, changing some of the following values, and then
setting it back to 0. I suspect this might be a mutex?

Changing this to 2 when the cpu doesn't expect it will cause it to panic with:

    panic(cpu 0 caller 0xfffffe0013b6d8c4): UAT PPL 0xfffffdf0429d0160 (IOUAT): 
        Attempted to call prepareFWUnmap() before completing previous cache flush. 
        flush_state: 2 | start_addr: 0x150e540000 | size: 0x730000 | context_id: 1

`0x10ffffb4040` : u64 - CPU sometimes writes GPU VAs here  
`0x10ffffb4048` : u64 - Size? set to nice round numbers like 0x28000 and 0x8000  
`0x10ffffb4050` : u64 - CPU sometimes writes GPU VAs here  
`0x10ffffb4058` : u64 - another size  

`0x10ffffb4098` : u64 - Treated the same way as 4038, but when touching 40a0  
`0x10ffffb40a0` : u64 - CPU sometimes writes GPU VAs here, I've only seen this when running a metal app  
`0x10ffffb40a8` : u64 - size?  

`0x10ffffb4620` : u32 - ?  
`0x10ffffb4638` : u8 - Always checked before 0x4038 is changed.  


The CPU writes interesting GPU VA pointers to this range. I spent a long time thinking this must be
how work is submitted to the GPU. But it doesn't seem to be related to the Kicks or Pongs. Sometimes
the kernel will overwrite pointers multiple times with zero Kicks or Pongs in-between.
Other times it will do hundreds of kicks without ever changing anything in this region.

My current theory is that this region is exclusive used to track the status of page table updates,
and is accessible to both MacOS and gfx-asc so they can syncronise access for pagetable updates

## sgx registers

the CPU never writes to these registers, only reads. 

These registers are read once, during initialization:

    0x4000 : u32 - version number? 0x4042000
    0x4010 : u32 - version number? 0x30808
    0x4014 : u32 - version number? 0x40404
    0x4018 : u32 - unknown 0x1320200
    0x401c : u32 - 0x204311
    0x4008 : u32 - 0x40a06
    0x1500 : u32 - 0xffffffff
    0x1514 : u32 - 0x0
    0x8024 : u32 = 0x43ffffe - (this matches sgx/ttbat-phys-addr-base from the ADT)

These status registers are continually checked by *something* on the CPU

    0x11008 : u32 - Always counts up whenever work is done
    0x1100c : u32 - Useally 0
    0x11010 : u32 - Another work counter? counts up slower
    0x11014 : u32 - Useally 0

There doesn't seem to be a good relationship of when these status registers are read, relative to
the ASC Pong and Kicks. This is part of the reason why I've been wondering if there is an alternative
communication channel that's missing from ADT

## My Theories

I currently have two theories for where work submissions are hiding.

### One: missing communication channel 

Maybe there is another mailbox that is missing from ADT. Maybe everything I've traced including the
kicks are to do with page tables, and work submissions go over another communication channel.

I've mostly disproved this theory, I've traced the entire IO range around both the sgx and gfx-asc nodes
from `0x404000000` to `0x406ffffff` and there is no CPU writes to undocumented registers. 

I also traced every single IO range that was mapped in to UAT to see if there were cpu writes to them.

### Two: Kick + shared memory

More likely, the Kicks are telling the gfx-asc firmware to look at a known shared memory address,
and I just haven't found it. I've eliminated all the memory ranges listed in the sgx node, so it's
either an address passed in via the 0x20 EP initialization message's "ControlStruct" (I've checked 
the top level pointers, but I haven't fully mapped the ControlStruct out) or it checks a hard
coded address. 