# tests ats on the prudic transport model.  With these ATS settings, the
# solver should fail on time step 19 in period 2, and should converge on the
# second try with a smaller time step.  This test will not pass if the states
# are not restored properly for the advanced transport packages when the
# failure occurs.

import os
import pytest
import shutil
import numpy as np

try:
    import pymake
except:
    msg = "Error. Pymake package is not available.\n"
    msg += "Try installing using the following command:\n"
    msg += " pip install https://github.com/modflowpy/pymake/zipball/master"
    raise Exception(msg)

try:
    import flopy
except:
    msg = "Error. FloPy package is not available.\n"
    msg += "Try installing using the following command:\n"
    msg += " pip install flopy"
    raise Exception(msg)


import targets

exe_name_mf6 = targets.target_dict["mf6"]
exe_name_mf6 = os.path.abspath(exe_name_mf6)

data_ws = os.path.abspath("./data/prudic2004test2/")
testdir = "./temp"
testgroup = "prudic2004t2fmiats"
d = os.path.join(testdir, testgroup)
if os.path.isdir(d):
    shutil.rmtree(d)

nlay = 8
nrow = 36
ncol = 23
delr = 405.665
delc = 403.717
top = 100.0
fname = os.path.join(data_ws, "bot1.dat")
bot0 = np.loadtxt(fname)
botm = [bot0] + [bot0 - (15.0 * k) for k in range(1, nlay)]
fname = os.path.join(data_ws, "idomain1.dat")
idomain0 = np.loadtxt(fname, dtype=int)
idomain = nlay * [idomain0]


def run_flow_model():
    global idomain
    name = "flow"
    gwfname = name
    wsf = os.path.join(testdir, testgroup, name)
    sim = flopy.mf6.MFSimulation(
        sim_name=name, sim_ws=wsf, exe_name=exe_name_mf6
    )
    tdis_rc = [(1.0, 1, 1.0), (365.25 * 25, 1, 1.0)]
    nper = len(tdis_rc)
    tdis = flopy.mf6.ModflowTdis(
        sim, time_units="DAYS", nper=nper, perioddata=tdis_rc
    )

    gwf = flopy.mf6.ModflowGwf(sim, modelname=gwfname, save_flows=True)

    # ims
    hclose = 0.01
    rclose = 0.1
    nouter = 1000
    ninner = 100
    relax = 0.99
    imsgwf = flopy.mf6.ModflowIms(
        sim,
        print_option="SUMMARY",
        outer_dvclose=hclose,
        outer_maximum=nouter,
        under_relaxation="NONE",
        inner_maximum=ninner,
        inner_dvclose=hclose,
        rcloserecord=rclose,
        linear_acceleration="CG",
        scaling_method="NONE",
        reordering_method="NONE",
        relaxation_factor=relax,
        filename="{}.ims".format(gwfname),
    )

    dis = flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
        idomain=idomain,
    )
    idomain = dis.idomain.array

    ic = flopy.mf6.ModflowGwfic(gwf, strt=50.0)

    npf = flopy.mf6.ModflowGwfnpf(
        gwf,
        xt3doptions=False,
        save_flows=True,
        save_specific_discharge=True,
        save_saturation=True,
        icelltype=[1] + 7 * [0],
        k=250.0,
        k33=125.0,
    )

    sto_on = False
    if sto_on:
        sto = flopy.mf6.ModflowGwfsto(
            gwf,
            save_flows=True,
            iconvert=[1] + 7 * [0],
            ss=1.0e-5,
            sy=0.3,
            steady_state={0: True},
            transient={1: False},
        )

    oc = flopy.mf6.ModflowGwfoc(
        gwf,
        budget_filerecord="{}.bud".format(gwfname),
        head_filerecord="{}.hds".format(gwfname),
        headprintrecord=[
            ("COLUMNS", ncol, "WIDTH", 15, "DIGITS", 6, "GENERAL")
        ],
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )

    rch_on = True
    if rch_on:
        rch = flopy.mf6.ModflowGwfrcha(
            gwf, recharge={0: 4.79e-3}, pname="RCH-1"
        )

    chdlist = []
    fname = os.path.join(data_ws, "chd.dat")
    for line in open(fname, "r").readlines():
        ll = line.strip().split()
        if len(ll) == 4:
            k, i, j, hd = ll
            chdlist.append(
                [
                    (
                        int(k) - 1,
                        int(i) - 1,
                        int(j) - 1,
                    ),
                    float(hd),
                ]
            )
    chd = flopy.mf6.ModflowGwfchd(
        gwf, stress_period_data=chdlist, pname="CHD-1"
    )

    rivlist = []
    fname = os.path.join(data_ws, "riv.dat")
    for line in open(fname, "r").readlines():
        ll = line.strip().split()
        if len(ll) == 7:
            k, i, j, s, c, rb, bn = ll
            rivlist.append(
                [
                    (
                        int(k) - 1,
                        int(i) - 1,
                        int(j) - 1,
                    ),
                    float(s),
                    float(c),
                    float(rb),
                    bn,
                ]
            )
    rivra = flopy.mf6.ModflowGwfriv.stress_period_data.empty(
        gwf, maxbound=len(rivlist), boundnames=True
    )[0]
    for i, t in enumerate(rivlist):
        rivra[i] = tuple(t)
    fname = os.path.join(data_ws, "sfr-packagedata.dat")
    sfrpd = np.genfromtxt(fname, names=True)
    sfrpackagedata = flopy.mf6.ModflowGwfsfr.packagedata.empty(
        gwf, boundnames=True, maxbound=sfrpd.shape[0]
    )
    for name in sfrpackagedata.dtype.names:
        if name in rivra.dtype.names:
            sfrpackagedata[name] = rivra[name]
    for name in sfrpackagedata.dtype.names:
        if name in sfrpd.dtype.names:
            sfrpackagedata[name] = sfrpd[name]
    sfrpackagedata["boundname"] = rivra["boundname"]
    fname = os.path.join(data_ws, "sfr-connectiondata.dat")
    with open(fname) as f:
        lines = f.readlines()
    sfrconnectiondata = []
    for line in lines:
        t = line.split()
        c = []
        for v in t:
            i = int(v)
            c.append(i)
        sfrconnectiondata.append(c)
    sfrperioddata = {0: [[0, "inflow", 86400], [18, "inflow", 8640.0]]}

    sfr_obs = {
        (gwfname + ".sfr.obs.csv",): [
            ("reach1leakage", "SFR", "LONGESTRIVERINTHEWORLD1"),
            ("reach2leakage", "SFR", "LONGESTRIVERINTHEWORLD2"),
            ("reach3leakage", "SFR", "LONGESTRIVERINTHEWORLD3"),
            ("reach4leakage", "SFR", "LONGESTRIVERINTHEWORLD4"),
        ],
    }
    sfr_obs["digits"] = 7
    sfr_obs["print_input"] = True
    sfr_obs["filename"] = gwfname + ".sfr.obs"

    sfr_on = True
    if sfr_on:
        sfr = flopy.mf6.ModflowGwfsfr(
            gwf,
            print_stage=True,
            print_flows=True,
            stage_filerecord=gwfname + ".sfr.bin",
            budget_filerecord=gwfname + ".sfr.bud",
            mover=True,
            pname="SFR-1",
            unit_conversion=128390.00,
            boundnames=True,
            nreaches=len(rivlist),
            packagedata=sfrpackagedata,
            connectiondata=sfrconnectiondata,
            perioddata=sfrperioddata,
            observations=sfr_obs,
        )

    fname = os.path.join(data_ws, "lakibd.dat")
    lakibd = np.loadtxt(fname, dtype=int)
    lakeconnectiondata = []
    nlakecon = [0, 0]
    lak_leakance = 1.0
    for i in range(nrow):
        for j in range(ncol):
            if lakibd[i, j] == 0:
                continue
            else:
                ilak = lakibd[i, j] - 1
                # back
                if i > 0:
                    if lakibd[i - 1, j] == 0 and idomain[0, i - 1, j]:
                        h = [
                            ilak,
                            nlakecon[ilak],
                            (0, i - 1, j),
                            "horizontal",
                            lak_leakance,
                            0.0,
                            0.0,
                            delc / 2.0,
                            delr,
                        ]
                        nlakecon[ilak] += 1
                        lakeconnectiondata.append(h)
                # left
                if j > 0:
                    if lakibd[i, j - 1] and idomain[0, i, j - 1] == 0:
                        h = [
                            ilak,
                            nlakecon[ilak],
                            (0, i, j - 1),
                            "horizontal",
                            lak_leakance,
                            0.0,
                            0.0,
                            delr / 2.0,
                            delc,
                        ]
                        nlakecon[ilak] += 1
                        lakeconnectiondata.append(h)
                # right
                if j < ncol - 1:
                    if lakibd[i, j + 1] == 0 and idomain[0, i, j + 1]:
                        h = [
                            ilak,
                            nlakecon[ilak],
                            (0, i, j + 1),
                            "horizontal",
                            lak_leakance,
                            0.0,
                            0.0,
                            delr / 2.0,
                            delc,
                        ]
                        nlakecon[ilak] += 1
                        lakeconnectiondata.append(h)
                # front
                if i < nrow - 1:
                    if lakibd[i + 1, j] == 0 and idomain[0, i + 1, j]:
                        h = [
                            ilak,
                            nlakecon[ilak],
                            (0, i + 1, j),
                            "horizontal",
                            lak_leakance,
                            0.0,
                            0.0,
                            delc / 2.0,
                            delr,
                        ]
                        nlakecon[ilak] += 1
                        lakeconnectiondata.append(h)
                # vertical
                v = [
                    ilak,
                    nlakecon[ilak],
                    (1, i, j),
                    "vertical",
                    lak_leakance,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]
                nlakecon[ilak] += 1
                lakeconnectiondata.append(v)

    lak_obs = {
        (gwfname + ".lak.obs.csv",): [
            ("lake1stage", "STAGE", "lake1"),
            ("lake2stage", "STAGE", "lake2"),
            ("lake1leakage", "LAK", "lake1"),
            ("lake2leakage", "LAK", "lake2"),
        ],
    }
    sfr_obs["digits"] = 7
    sfr_obs["print_input"] = True
    sfr_obs["filename"] = gwfname + ".sfr.obs"

    i, j = np.where(lakibd > 0)
    idomain[0, i, j] = 0
    gwf.dis.idomain.set_data(idomain[0], layer=0, multiplier=[1])

    lakpackagedata = [
        [0, 44.0, nlakecon[0], "lake1"],
        [1, 35.2, nlakecon[1], "lake2"],
    ]
    # <outletno> <lakein> <lakeout> <couttype> <invert> <width> <rough> <slope>
    outlets = [[0, 0, -1, "MANNING", 44.5, 5.000000, 0.03, 0.2187500e-02]]

    lake_on = True
    if lake_on:
        lak = flopy.mf6.ModflowGwflak(
            gwf,
            time_conversion=86400.000,
            print_stage=True,
            print_flows=True,
            stage_filerecord=gwfname + ".lak.bin",
            budget_filerecord=gwfname + ".lak.bud",
            mover=True,
            pname="LAK-1",
            boundnames=True,
            nlakes=2,
            noutlets=len(outlets),
            outlets=outlets,
            packagedata=lakpackagedata,
            connectiondata=lakeconnectiondata,
            observations=lak_obs,
        )

    mover_on = True
    if mover_on:
        maxmvr, maxpackages = 2, 2
        mvrpack = [["SFR-1"], ["LAK-1"]]
        mvrperioddata = [
            ["SFR-1", 5, "LAK-1", 0, "FACTOR", 1.0],
            ["LAK-1", 0, "SFR-1", 6, "FACTOR", 1.0],
        ]
        mvr = flopy.mf6.ModflowGwfmvr(
            gwf,
            maxmvr=maxmvr,
            print_flows=True,
            budget_filerecord=gwfname + ".mvr.bud",
            maxpackages=maxpackages,
            packages=mvrpack,
            perioddata=mvrperioddata,
        )

    sim.write_simulation()
    sim.run_simulation(silent=False)

    fname = gwfname + ".hds"
    fname = os.path.join(wsf, fname)
    hobj = flopy.utils.HeadFile(fname, precision="double")
    head = hobj.get_data()
    hobj.file.close()

    if lake_on:
        fname = gwfname + ".lak.bin"
        fname = os.path.join(wsf, fname)
        lkstage = None
        if os.path.isfile(fname):
            lksobj = flopy.utils.HeadFile(
                fname, precision="double", text="stage"
            )
            lkstage = lksobj.get_data().flatten()
            lksobj.file.close()

    if sfr_on:
        fname = gwfname + ".sfr.bin"
        fname = os.path.join(wsf, fname)
        sfstage = None
        if os.path.isfile(fname):
            bobj = flopy.utils.HeadFile(
                fname, precision="double", text="stage"
            )
            sfstage = bobj.get_data().flatten()
            bobj.file.close()

    if mover_on:
        fname = gwfname + ".mvr.bud"
        fname = os.path.join(wsf, fname)
        bobj = flopy.utils.CellBudgetFile(fname, precision="double")
        ra = bobj.recordarray
        print(ra)
        print(ra.dtype)
        for idx in range(ra.shape[0]):
            d = bobj.get_data(idx=idx)[0]
            if d.shape[0] > 0:
                p1 = ra[idx]["paknam"].decode().strip()
                p2 = ra[idx]["paknam2"].decode().strip()
                print(
                    ra[idx]["kstp"],
                    ra[idx]["kper"],
                    ra[idx]["paknam"],
                    ra[idx]["paknam2"],
                )
                for node, node2, q in d:
                    print(p1, node, p2, node2, q)

    return


def run_transport_model():
    name = "transport"
    gwtname = name
    wst = os.path.join(testdir, testgroup, name)
    sim = flopy.mf6.MFSimulation(
        sim_name=name,
        version="mf6",
        exe_name=exe_name_mf6,
        sim_ws=wst,
        continue_=False,
    )

    ats_filerecord = None
    if True:
        dt0 = 100
        dtmin = 1.0e-5
        dtmax = 10000.0
        dtadj = 2.0
        dtfailadj = 5.0
        atsperiod = [
            (1, dt0, dtmin, dtmax, dtadj, dtfailadj),
        ]
        ats = flopy.mf6.ModflowUtlats(
            sim, maxats=len(atsperiod), perioddata=atsperiod
        )
        ats_filerecord = name + ".ats"

    tdis_rc = [(1.0, 1, 1.0), (365.25 * 25, 25, 1.0)]
    nper = len(tdis_rc)
    tdis = flopy.mf6.ModflowTdis(
        sim,
        time_units="DAYS",
        nper=nper,
        perioddata=tdis_rc,
        ats_filerecord=ats_filerecord,
    )

    gwt = flopy.mf6.ModflowGwt(sim, modelname=gwtname)

    # ims
    hclose = 0.001
    rclose = 0.001
    nouter = 50
    ninner = 20
    relax = 0.97
    imsgwt = flopy.mf6.ModflowIms(
        sim,
        print_option="ALL",
        outer_dvclose=hclose,
        outer_maximum=nouter,
        under_relaxation="DBD",
        under_relaxation_theta=0.7,
        inner_maximum=ninner,
        inner_dvclose=hclose,
        rcloserecord=rclose,
        linear_acceleration="BICGSTAB",
        scaling_method="NONE",
        reordering_method="NONE",
        relaxation_factor=relax,
        filename="{}.ims".format(gwtname),
    )
    sim.register_ims_package(imsgwt, [gwt.name])

    dis = flopy.mf6.ModflowGwtdis(
        gwt,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
        idomain=idomain,
    )
    ic = flopy.mf6.ModflowGwtic(gwt, strt=0.0)
    sto = flopy.mf6.ModflowGwtmst(gwt, porosity=0.3)
    adv = flopy.mf6.ModflowGwtadv(gwt, scheme="TVD")
    dsp = flopy.mf6.ModflowGwtdsp(gwt, alh=20.0, ath1=2, atv=0.2)
    sourcerecarray = [()]
    ssm = flopy.mf6.ModflowGwtssm(gwt, sources=sourcerecarray)
    cnclist = [
        [(0, 0, 11), 500.0],
        [(0, 0, 12), 500.0],
        [(0, 0, 13), 500.0],
        [(0, 0, 14), 500.0],
        [(1, 0, 11), 500.0],
        [(1, 0, 12), 500.0],
        [(1, 0, 13), 500.0],
        [(1, 0, 14), 500.0],
    ]
    cnc = flopy.mf6.ModflowGwtcnc(
        gwt,
        maxbound=len(cnclist),
        stress_period_data=cnclist,
        save_flows=False,
        pname="CNC-1",
    )

    lktpackagedata = [
        (0, 0.0, 99.0, 999.0, "mylake1"),
        (1, 0.0, 99.0, 999.0, "mylake2"),
    ]
    lktperioddata = [
        (0, "STATUS", "ACTIVE"),
        (1, "STATUS", "ACTIVE"),
    ]
    lkt_obs = {
        (gwtname + ".lkt.obs.csv",): [
            ("lkt1conc", "CONCENTRATION", 1),
            ("lkt2conc", "CONCENTRATION", 2),
            ("lkt1frommvr", "FROM-MVR", (0,)),
            ("lkt2frommvr", "FROM-MVR", (1,)),
            ("lkt1tomvr", "TO-MVR", (0,)),
            ("lkt1bntomvr", "TO-MVR", "mylake1"),
        ],
    }
    lkt_obs["digits"] = 7
    lkt_obs["print_input"] = True
    lkt_obs["filename"] = gwtname + ".lkt.obs"

    lkt_on = True
    if lkt_on:
        lkt = flopy.mf6.modflow.ModflowGwtlkt(
            gwt,
            boundnames=True,
            save_flows=True,
            print_input=True,
            print_flows=True,
            print_concentration=True,
            concentration_filerecord=gwtname + ".lkt.bin",
            budget_filerecord=gwtname + ".lkt.bud",
            packagedata=lktpackagedata,
            lakeperioddata=lktperioddata,
            observations=lkt_obs,
            pname="LAK-1",
            auxiliary=["aux1", "aux2"],
        )

    nreach = 38
    sftpackagedata = []
    for irno in range(nreach):
        t = (irno, 0.0, 99.0, 999.0, "myreach{}".format(irno + 1))
        sftpackagedata.append(t)

    sftperioddata = [(0, "STATUS", "ACTIVE"), (0, "CONCENTRATION", 0.0)]

    sft_obs = {
        (gwtname + ".sft.obs.csv",): [
            ("sft{}conc".format(i + 1), "CONCENTRATION", i + 1)
            for i in range(nreach)
        ]
    }
    # append additional obs attributes to obs dictionary
    sft_obs["digits"] = 7
    sft_obs["print_input"] = True
    sft_obs["filename"] = gwtname + ".sft.obs"

    sft_on = True
    if sft_on:
        sft = flopy.mf6.modflow.ModflowGwtsft(
            gwt,
            boundnames=True,
            save_flows=True,
            print_input=True,
            print_flows=True,
            print_concentration=True,
            concentration_filerecord=gwtname + ".sft.bin",
            budget_filerecord=gwtname + ".sft.bud",
            packagedata=sftpackagedata,
            reachperioddata=sftperioddata,
            observations=sft_obs,
            pname="SFR-1",
            auxiliary=["aux1", "aux2"],
        )

    pd = [
        ("GWFHEAD", "../flow/flow.hds", None),
        ("GWFBUDGET", "../flow/flow.bud", None),
        ("GWFMOVER", "../flow/flow.mvr.bud", None),
        ("LAK-1", "../flow/flow.lak.bud", None),
        ("SFR-1", "../flow/flow.sfr.bud", None),
    ]
    fmi = flopy.mf6.ModflowGwtfmi(gwt, packagedata=pd)

    # mover transport package
    mvt = flopy.mf6.modflow.ModflowGwtmvt(gwt, print_flows=True)

    oc = flopy.mf6.ModflowGwtoc(
        gwt,
        budget_filerecord="{}.cbc".format(gwtname),
        concentration_filerecord="{}.ucn".format(gwtname),
        concentrationprintrecord=[
            ("COLUMNS", ncol, "WIDTH", 15, "DIGITS", 6, "GENERAL")
        ],
        saverecord=[("CONCENTRATION", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("CONCENTRATION", "ALL"), ("BUDGET", "ALL")],
    )

    sim.write_simulation()
    sim.run_simulation()

    fname = gwtname + ".lkt.bin"
    fname = os.path.join(wst, fname)
    bobj = flopy.utils.HeadFile(
        fname, precision="double", text="concentration"
    )
    lkaconc = bobj.get_alldata()[:, 0, 0, :]
    times = bobj.times
    bobj.file.close()

    fname = gwtname + ".sft.bin"
    fname = os.path.join(wst, fname)
    bobj = flopy.utils.HeadFile(
        fname, precision="double", text="concentration"
    )
    sfaconc = bobj.get_alldata()[:, 0, 0, :]
    times = bobj.times
    bobj.file.close()

    # set atol
    atol = 0.05

    # check simulated concentration in lak 1 and 2 sfr reaches
    res_lak1 = lkaconc[:, 0]
    ans_lak1 = [
        -1.73249951e-19,
        -3.18568873e-07,
        -1.93254232e-06,
        5.37979095e-07,
        5.58611972e-03,
        4.53905550e-02,
        1.92733156e-01,
        5.68672833e-01,
        2.99824969e00,
        7.10780047e00,
        1.22648840e01,
        1.76704726e01,
        2.26942092e01,
        2.70010187e01,
        3.05038540e01,
        3.32193779e01,
        3.52479250e01,
        3.67285097e01,
        3.77909702e01,
        3.79877645e01,
        3.81699209e01,
        3.83384907e01,
        3.84944857e01,
        3.86388564e01,
        3.87724831e01,
        3.88961784e01,
        3.91093083e01,
        3.92927299e01,
        3.95693787e01,
        3.99100255e01,
        4.01258276e01,
        4.02675337e01,
        4.03501250e01,
    ]
    ans_lak1 = np.array(ans_lak1)
    d = res_lak1 - ans_lak1
    msg = "{}\n{}\n{}".format(res_lak1, ans_lak1, d)
    assert np.allclose(res_lak1, ans_lak1, atol=atol), msg

    res_sfr3 = sfaconc[:, 30]
    ans_sfr3 = [
        -7.67944653e-23,
        -1.36626135e-08,
        -9.22237557e-08,
        4.99905352e-08,
        3.99099797e-04,
        3.35353676e-03,
        1.47391122e-02,
        4.50924724e-02,
        2.78746896e-01,
        7.45757915e-01,
        1.46650909e00,
        2.44405848e00,
        3.67524186e00,
        5.15790366e00,
        6.87288671e00,
        8.78052541e00,
        1.08386493e01,
        1.30048172e01,
        1.52293421e01,
        1.56761479e01,
        1.61242587e01,
        1.65730359e01,
        1.70216907e01,
        1.74706790e01,
        1.79202485e01,
        1.83702377e01,
        1.92703764e01,
        2.01670548e01,
        2.19177092e01,
        2.50962473e01,
        2.78395994e01,
        3.00921256e01,
        3.15755870e01,
    ]
    ans_sfr3 = np.array(ans_sfr3)
    d = res_sfr3 - ans_sfr3
    msg = "{}\n{}\n{}".format(res_sfr3, ans_sfr3, d)
    assert np.allclose(res_sfr3, ans_sfr3, atol=atol), msg

    res_sfr4 = sfaconc[:, 37]
    ans_sfr4 = [
        -2.00171747e-20,
        -1.31881904e-07,
        -8.75301649e-07,
        7.69101706e-07,
        3.28388144e-03,
        2.67384200e-02,
        1.13765608e-01,
        3.36399332e-01,
        1.79195755e00,
        4.28594083e00,
        7.47548917e00,
        1.09172977e01,
        1.42591448e01,
        1.73135656e01,
        2.00235978e01,
        2.23809139e01,
        2.44226417e01,
        2.62073204e01,
        2.77851731e01,
        2.80928500e01,
        2.83929590e01,
        2.86858017e01,
        2.89715918e01,
        2.92510600e01,
        2.95248063e01,
        2.97932113e01,
        3.03110243e01,
        3.08107687e01,
        3.17411221e01,
        3.33403357e01,
        3.46770708e01,
        3.57548963e01,
        3.64587547e01,
    ]
    ans_sfr4 = np.array(ans_sfr4)
    d = res_sfr4 - ans_sfr4
    msg = "{}\n{}\n{}".format(res_sfr4, ans_sfr4, d)
    assert np.allclose(res_sfr4, ans_sfr4, atol=atol), msg

    # make some checks on lake obs csv file
    fname = gwtname + ".lkt.obs.csv"
    fname = os.path.join(wst, fname)
    try:
        tc = np.genfromtxt(fname, names=True, delimiter=",")
    except:
        assert False, 'could not load data from "{}"'.format(fname)
    errmsg = "to-mvr boundname and outlet number do not match for {}".format(
        fname
    )
    assert np.allclose(tc["LKT1TOMVR"], tc["LKT1BNTOMVR"]), errmsg

    # check simulation list file for ats information
    fname = os.path.join(wst, "mfsim.lst")
    with open(fname, "r") as f:
        lines = f.readlines()

    txtlist = [
        (
            "Failed solution for step 19 and period 2 will be retried using "
            "time step of    80.00000"
        ),
        "ATS IS OVERRIDING TIME STEPPING FOR THIS PERIOD",
        "INITIAL TIME STEP SIZE                 (DT0) =    100.0000",
        "MINIMUM TIME STEP SIZE               (DTMIN) =   0.1000000E-04",
        "MAXIMUM TIME STEP SIZE               (DTMAX) =    10000.00",
        "MULTIPLIER/DIVIDER FOR TIME STEP     (DTADJ) =    2.000000",
        "DIVIDER FOR FAILED TIME STEP     (DTFAILADJ) =    5.000000",
    ]
    all_found = True
    for stxt in txtlist:
        msg = "Checking for string in mfsim.lst: {}".format(stxt)
        found = False
        for line in lines:
            if stxt in line:
                found = True
                break
        if not found:
            msg += " -- NOT FOUND!"
            all_found = False
            print("text not found in mfsim.lst: {}".format(stxt))
        print(msg)
    assert (
        all_found
    ), "One or more required text strings not found in mfsim.lst"

    return


def test_prudic2004t2fmiats():
    run_flow_model()
    run_transport_model()
    d = os.path.join(testdir, testgroup)
    #    if os.path.isdir(d):
    #        shutil.rmtree(d)
    return


if __name__ == "__main__":
    # print message
    print("standalone run of {}".format(os.path.basename(__file__)))

    # run tests
    test_prudic2004t2fmiats()
