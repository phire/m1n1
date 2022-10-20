# SPDX-License-Identifier: MIT
from ..fw.agx.initdata import *
from ..fw.agx.channels import ChannelInfo
from ..hw.uat import MemoryAttr

def build_iomappings(agx):
    def iomap(phys, size, range_size, rw):
        off = phys & 0x3fff
        virt = agx.io_allocator.malloc(size + 0x4000 + off)
        agx.uat.iomap_at(0, virt, phys - off, size + off, AttrIndex=MemoryAttr.Device)
        return IOMapping(phys, virt + off, size, range_size, rw)

    def reg(name, idx):
        return agx.u.adt["/arm-io/" + name].reg[idx]

    adt = agx.u.adt

#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010000000 -> sgx[1]+0x0 (0x1c000 / 0x1c000),
#    ID.ID_RB.AGXDB.IO Mapping: RO 0xffffffa010020000 -> unknown+0x20e100000 (0x4000 / 0x4000),
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010028000 -> aic[0]+0x4000 (0x4000 / 0x4000),
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010030000 -> sgx[0]+0x0 (0x20000 / 0x20000),

#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.IO Mapping: RO 0xffffffa010058000 -> pmgr[34]+0x94000 (0x4000 / 0x4000),

#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010060000 -> unknown+0x404d80000 (0x8000 / 0x8000),
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010071000 -> mcc[4]+0xd61000 (0x1000 / 0x1000),
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010078000 -> mcc[0]+0x0 (0x6c0000 / 0xd8000),

#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010740000 -> unknown+0x2643c4000 (0x1000 / 0x1000),
#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,

#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.<IOMapping: Invalid>,
#    ID.ID_RB.AGXDB.IO Mapping: RW 0xffffffa010748000 -> pmgr[41]+0x10000 (0x1000 / 0x1000),
#    ID.ID_RB.AGXDB.IO Mapping: RO 0xffffffa010750000 -> pmgr[41]+0x0 (0x2000 / 0x2000),

    # for t6000

    memBankCount = 8

    io = [None] * 20
    io[0] = iomap(reg("sgx", 1), 0x1c000, 0x1c000, 1), # Fender
    io[1] = iomap(0x20e100000, 0x4000, 0x4000, 0), # AICTimer
    io[2] = iomap(reg("aic", 0) + 0x4000, 0x4000, 0x4000, 1), # AICSWInt
    io[3] = iomap(reg["sgx", 0), 0x20000, 0x20000, 1), # RGX

    io[4] = IOMapping(), # UVD
    io[5] = IOMapping(), # unused
    io[6] = IOMapping(), # DisplayUnderrunWA
    io[7] = iomap(reg("pmgr", 34) + 0x94000, 0x1000, 0x1000, 0), # AnalogTempSensorControllerRegs

    if Ver.hw() == "t6000":
        io[8] = IOMapping(), # PMPDoorbell
        io[9] = iomap(0x404d80000, 0x8000, 0x8000, 1), # MetrologySensorRegs?
    else:
        io[8] = iomap(0x23bc00000, 0x1000, 0x1000, 1), # PMPDoorbell
        io[9] = iomap(0x204d80000, 0x5000, 0x5000, 1), # MetrologySensorRegs
    io[10] = iomap(reg("mcc", 4) + 0xd61000, 0x1000, 0x1000, 1), # GMGIFAFRegs
    io[11] = iomap(reg("mcc", 0), 0xd6400 * memBankCount, 0xd6400, 1), # MCache registers
    io[12] = IOMapping(), # AICBankedRegisters
    io[13] = iomap(0x23b738000, 0x1000, 0x1000, 1), # PMGRScratch
    io[14] = IOMapping(), # NIA Special agent idle register die 0
    io[15] = IOMapping(), # NIA Special agent idle register die 1
    io[16] = IOMapping(), # CRE registers
    io[17] = IOMapping(), # Streaming codec registers
    io[18] = IOMapping(), #
    io[19] = IOMapping(), #

    return io

    # for t8103
    return [
        iomap(0x204d00000, 0x1c000, 0x1c000, 1), # Fender
        iomap(0x20e100000, 0x4000, 0x4000, 0), # AICTimer
        iomap(0x23b104000, 0x4000, 0x4000, 1), # AICSWInt
        iomap(0x204000000, 0x20000, 0x20000, 1), # RGX
        IOMapping(), # UVD
        IOMapping(), # unused
        IOMapping(), # DisplayUnderrunWA
        iomap(0x23b2e8000, 0x1000, 0x1000, 0), # AnalogTempSensorControllerRegs
        iomap(0x23bc00000, 0x1000, 0x1000, 1), # PMPDoorbell
        iomap(0x204d80000, 0x5000, 0x5000, 1), # MetrologySensorRegs
        iomap(0x204d61000, 0x1000, 0x1000, 1), # GMGIFAFRegs
        iomap(0x200000000, 0xd6400, 0xd6400, 1), # MCache registers
        IOMapping(), # AICBankedRegisters
        iomap(0x23b738000, 0x1000, 0x1000, 1), # PMGRScratch
        IOMapping(), # NIA Special agent idle register die 0
        IOMapping(), # NIA Special agent idle register die 1
        IOMapping(), # CRE registers
        IOMapping(), # Streaming codec registers
        IOMapping(), #
        IOMapping(), #
    ]

def build_initdata(agx):
    sgx = agx.u.adt["/arm-io/sgx"]
    chosen = agx.u.adt["/chosen"]

    initdata = agx.kshared.new(InitData)

    initdata.ver_info = (1, 1, 16, 1)

    initdata.regionA = agx.kshared.new_buf(0x4000, "InitData_RegionA").push()

    regionB = agx.kobj.new(InitData_RegionB)

    regionB.channels = agx.ch_info

    regionB.stats_ta = agx.kobj.new(InitData_GPUGlobalStatsTA).push()
    regionB.stats_3d = agx.kobj.new(InitData_GPUGlobalStats3D).push()

    # size: 0x180, Empty
    # 13.0: grew
    #regionB.stats_cp = agx.kobj.new_buf(0x180, "RegionB.unkptr_180").push()
    regionB.stats_cp = agx.kobj.new_buf(0x980, "RegionB.unkptr_180").push()

    # size: 0x3b80, few floats, few ints, needed for init
    regionB.hwdata_a = agx.kobj.new(AGXHWDataA, track=False).push()

    # size: 0x80, empty
    regionB.unk_190 = agx.kobj.new_buf(0x80, "RegionB.unkptr_190").push()

    # size: 0xc0, fw writes timestamps into this
    regionB.unk_198 = agx.kobj.new_buf(0xc0, "RegionB.unkptr_198").push()

    # size: 0xb80, io stuff
    hwdata = agx.kobj.new(AGXHWDataB, track=False)
    hwdata.io_mappings = build_iomappings(agx)
    hwdata.chip_id = chosen.chip_id

    hwdata.max_pstate = sgx.gpu_num_perf_states
    hwdata.num_pstates = sgx.perf_state_count
    hwdata.min_volt = 850
    # how is this computed?
    perf_levels = [0, 19, 26, 38, 60, 87, 100]
    k = 1.02 #?
    for i, ps in enumerate(sgx.perf_states):
        hwdata.frequencies[i] = ps.freq // 1000000
        hwdata.voltages[i] = [ps.volt] * 8
        vm = max(hwdata.min_volt, ps.volt)
        hwdata.voltages_sram[i] = [vm] + [0] * 7
        regionB.hwdata_a.unk_74[i] = k
        hwdata.unk_9b4[i] = k
        hwdata.perf_levels[i] = perf_levels[i]

    regionB.hwdata_b = hwdata.push()
    regionB.hwdata_b_addr2 = hwdata._addr

    regionB.fwlog_ring2 = agx.fwlog_ring

    # Unallocated, Size 0x1000
    regionB.unk_1b8 = agx.kobj.new_buf(0x1000, "RegionB.unkptr_1b8").push()

    # Unallocated, size 0x300
    regionB.unk_1c0 = agx.kobj.new_buf(0x300, "RegionB.unkptr_1c0").push()

    # Unallocated, unknown size
    regionB.unk_1c8 = agx.kobj.new_buf(0x1000, "RegionB.unkptr_1c8").push()

    # Size: 0x4000
    regionB.buffer_mgr_ctl = agx.kshared2.new(InitData_BufferMgrCtl).push()
    regionB.buffer_mgr_ctl_addr2 = regionB.buffer_mgr_ctl._addr

    regionB.unk_6a80 = 0
    regionB.gpu_idle = 0
    regionB.unk_6a9c = 0
    regionB.unk_ctr0 = 0
    regionB.unk_ctr1 = 0
    regionB.unk_6aa8 = 0
    regionB.unk_6aac = 0
    regionB.unk_ctr2 = 0
    regionB.unk_6ab4 = 0
    regionB.unk_6ab8 = 0
    regionB.unk_6abc = 0
    regionB.unk_6ac0 = 0
    regionB.unk_6ac4 = 0
    regionB.unk_ctr3 = 0
    regionB.unk_6acc = 0
    regionB.unk_6ad0 = 0
    regionB.unk_6ad4 = 0
    regionB.unk_6ad8 = 0
    regionB.unk_6adc = 0
    regionB.unk_6ae0 = 0
    regionB.unk_6ae4 = 0
    regionB.unk_6ae8 = 0
    regionB.unk_6aec = 0
    regionB.unk_6af0 = 0
    regionB.unk_ctr4 = 0
    regionB.unk_ctr5 = 0
    regionB.unk_6afc = 0

    initdata.regionB = regionB.push()

    initdata.regionC = agx.kshared.new(InitData_RegionC, track=False).push()

    #self.regionC_addr = agx.ksharedshared_heap.malloc(0x88000)

    initdata.fw_status = agx.kobj.new(InitData_FWStatus)
    initdata.fw_status.fwctl_channel = agx.fwctl_chinfo
    initdata.fw_status.push()

    ## This section seems to be data that would be used by firmware side page allocation
    ## But the current firmware doesn't have this functionality enabled, so it's not used?
    initdata.uat_num_levels = 3
    initdata.uat_page_bits = 14
    initdata.uat_page_size = 0x4000

    initdata.uat_level_info = [
        UatLevelInfo(36, 8),
        UatLevelInfo(25, 2048),
        UatLevelInfo(14, 2048),
    ]

    # Host handles FW allocations for existing firmware versions
    initdata.host_mapped_fw_allocations = 1


    #initdata.regionC.idle_ts = agx.u.mrs("CNTPCT_EL0") + 24000000
    #initdata.regionC.idle_unk = 0x5b2e8
    #initdata.regionC.idle_to_off_timeout_ms = 20000

    initdata.regionC.push()
    initdata.push()

    #print(initdata.val)
    return initdata
