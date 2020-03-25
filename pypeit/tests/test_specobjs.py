"""
Module to run tests on SpecObjs
"""
import os

import numpy as np
import pytest

from astropy.io import fits

from pypeit import msgs
from pypeit import specobjs
from pypeit import specobj
from pypeit.tests import tstutils

msgs.reset(verbosity=2)

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'files')
    return os.path.join(data_dir, filename)

@pytest.fixture
def sobj1():
    return specobj.SpecObj('MultiSlit', 1, SLITID=0)
@pytest.fixture
def sobj2():
    return specobj.SpecObj('MultiSlit', 2, SLITID=1)
@pytest.fixture
def sobj3():
    return specobj.SpecObj('MultiSlit', 3, SLITID=0)
@pytest.fixture
def sobj4():
    return specobj.SpecObj('MultiSlit', 1, SLITID=10)


def test_init(sobj1, sobj2):
    """ Run the parameter setup script
    """
    # Null
    sobjs1 = specobjs.SpecObjs()

    # With a few objs
    sobjs2 = specobjs.SpecObjs([sobj1,sobj2])
    assert sobjs2.nobj == 2


def test_access(sobj1, sobj2):
    sobjs = specobjs.SpecObjs([sobj1,sobj2])
    #
    assert sobjs[0]['PYPELINE'] == 'MultiSlit'
    assert len(sobjs['PYPELINE']) == 2

def test_add_rm(sobj1, sobj2, sobj3):
    sobjs = specobjs.SpecObjs([sobj1,sobj2])
    sobjs.add_sobj(sobj3)
    assert sobjs.nobj == 3
    # Remove
    sobjs.remove_sobj(2)
    assert len(sobjs.specobjs) == 2

    # Numpy 18
    sobjs1 = specobjs.SpecObjs()
    sobjs2 = specobjs.SpecObjs()
    sobjs2.add_sobj(sobjs1)


def test_set(sobj1, sobj2, sobj3):
    sobjs = specobjs.SpecObjs([sobj1,sobj2,sobj3])
    # All
    sobjs.DET = 3
    assert np.all(sobjs[:].DET == np.array([3,3,3]))
    sobjs[:].DET = 4
    assert np.all(sobjs[:].DET == np.array([4,4,4]))
    # Slice
    sobjs[1:2].DET = 2
    assert sobjs.DET[1] == 2
    # With logic
    det2 = sobjs.DET == 2
    sobjs[det2].PYPELINE = 'BLAH'
    assert sobjs.PYPELINE[1] == 'BLAH'
    assert sobjs.PYPELINE[0] == 'MultiSlit'


def test_io(sobj1, sobj2, sobj3, sobj4):
    sobjs = specobjs.SpecObjs([sobj1,sobj2,sobj3,sobj4])
    sobjs[0]['BOX_WAVE'] = np.arange(1000).astype(float)
    sobjs[1]['BOX_WAVE'] = np.arange(1000).astype(float)
    sobjs[2]['BOX_WAVE'] = np.arange(1000).astype(float)
    #sobjs[0]['BOX_COUNTS'] = np.ones_like(sobjs[0].BOX_WAVE)  # This tests single array
    sobjs[1]['BOX_COUNTS'] = np.ones_like(sobjs[0].BOX_WAVE)
    sobjs[2]['BOX_COUNTS'] = np.ones_like(sobjs[0].BOX_WAVE)
    # Detector
    sobjs[0]['DETECTOR'] = tstutils.get_kastb_detector()
    tmp = tstutils.get_kastb_detector()

    tmp['det'] = 2
    sobjs[1]['DETECTOR'] = tmp
    # Write
    header = fits.PrimaryHDU().header
    header['TST'] = 'TEST'
    ofile = data_path('tst_specobjs.fits')
    if os.path.isfile(ofile):
        os.remove(ofile)
    sobjs.write_to_fits(header, ofile, overwrite=False)
    # Read
    hdul = fits.open(ofile)
    assert len(hdul) == 7  # Primary + 4 Obj + 2 Detectors
    assert hdul[0].header['NSPEC'] == 4
    #
    _sobjs = specobjs.SpecObjs.from_fitsfile(ofile)
    assert _sobjs.nobj == 4
    assert np.array_equal(sobjs[0].BOX_WAVE, _sobjs[0].BOX_WAVE)
    assert np.array_equal(sobjs[1].BOX_WAVE, _sobjs[1].BOX_WAVE)
    _sobjs.write_to_fits(header, ofile, overwrite=True)

    # Detector
    assert _sobjs[0].DETECTOR is not None, '1st object started with Detector'
    assert _sobjs[1].DETECTOR is not None, '2nd object has DET=1 so should get decorated'
    assert _sobjs[2].DETECTOR is None

    # Now try updates!
    sobjs1 = specobjs.SpecObjs([sobj1])
    sobjs[0]['BOX_WAVE'] = np.arange(2000).astype(float)
    sobjs1[0]['DETECTOR'] = tstutils.get_kastb_detector()
    header1 = fits.PrimaryHDU().header
    sobjs1.write_to_fits(header1, ofile, overwrite=True, update_det=1)

    # Test
    _sobjs1 = specobjs.SpecObjs.from_fitsfile(ofile)
    assert _sobjs1.nobj == 3
    assert _sobjs1[2].BOX_WAVE.size == 2000

    os.remove(ofile)
