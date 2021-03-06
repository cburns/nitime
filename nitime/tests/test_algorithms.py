import numpy as np
from numpy.testing import *
from scipy.signal import signaltools
from nipy.timeseries import algorithms as tsa
from nipy.testing import *
from nipy.timeseries import utils as ut

def test_scipy_resample():
    """ Tests scipy signal's resample function
    """
    # create a freq list with max freq < 16 Hz
    freq_list = np.random.randint(0,high=15,size=5)
    # make a test signal with sampling freq = 64 Hz
    a = [np.sin(2*np.pi*f*np.linspace(0,1,64,endpoint=False))
         for f in freq_list]
    tst = np.array(a).sum(axis=0)
    # interpolate to 128 Hz sampling
    t_up = signaltools.resample(tst, 128)
    np.testing.assert_array_almost_equal(t_up[::2], tst)
    # downsample to 32 Hz
    t_dn = signaltools.resample(tst, 32)
    np.testing.assert_array_almost_equal(t_dn, tst[::2])

    # downsample to 48 Hz, and compute the sampling analytically for comparison
    dn_samp_ana = np.array([np.sin(2*np.pi*f*np.linspace(0,1,48,endpoint=False))
                            for f in freq_list]).sum(axis=0)
    t_dn2 = signaltools.resample(tst, 48)
    np.testing.assert_array_almost_equal(t_dn2, dn_samp_ana)

def test_coherency_mlab():
    """Tests that the coherency algorithm runs smoothly, using the mlab csd
    routine, that the resulting matrix is symmetric and that the frequency bands
    in the output make sense"""
    
    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])

    method = {"this_method":'mlab',
              "NFFT":256,
              "Fs":2*np.pi}

    f,c = tsa.coherency(np.vstack([x,y]),csd_method=method)

    np.testing.assert_array_almost_equal(c[0,1],c[1,0].conjugate())
    np.testing.assert_array_almost_equal(c[0,0],np.ones(f.shape))
    f_theoretical = ut.get_freqs(method['Fs'],method['NFFT'])
    np.testing.assert_array_almost_equal(f,f_theoretical)

def test_coherency_multi_taper():
    """Tests that the coherency algorithm runs smoothly, using the multi_taper
    csd routine and that the resulting matrix is symmetric"""
    
    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])

    method = {"this_method":'multi_taper_csd',
              "Fs":2*np.pi}

    f,c = tsa.coherency(np.vstack([x,y]),csd_method=method)

    np.testing.assert_array_almost_equal(c[0,1],c[1,0].conjugate())
    np.testing.assert_array_almost_equal(c[0,0],np.ones(f.shape))

def test_coherence_mlab():
    """Tests that the code runs and that the resulting matrix is symmetric """  

    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])

    method = {"this_method":'mlab',
              "NFFT":256,
              "Fs":2*np.pi}
    
    f,c = tsa.coherence(np.vstack([x,y]),csd_method=method)
    np.testing.assert_array_almost_equal(c[0,1],c[1,0])

    f_theoretical = ut.get_freqs(method['Fs'],method['NFFT'])
    np.testing.assert_array_almost_equal(f,f_theoretical)

def test_coherence_multi_taper():
    """Tests that the code runs and that the resulting matrix is symmetric """  

    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])

    method = {"this_method":'multi_taper_csd',
              "Fs":2*np.pi}
     
    f,c = tsa.coherence(np.vstack([x,y]),csd_method=method)
    np.testing.assert_array_almost_equal(c[0,1],c[1,0])

def test_coherence_partial():
 """ Test partial coherence"""

    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])
    z = x + np.random.rand(t.shape[-1])

    method = {"this_method":'mlab',
              "NFFT":256,
              "Fs":2*np.pi}
    f,c = tsa.coherence_partial(np.vstack([x,y]),z,csd_method=method)

    f_theoretical = ut.get_freqs(method['Fs'],method['NFFT'])
    np.testing.assert_array_almost_equal(f,f_theoretical)
    np.testing.assert_array_almost_equal(c[0,1],c[1,0])

    
def test_coherency_cached():
    """Tests that the cached coherency gives the same result as the standard
    coherency"""

    t = np.linspace(0,16*np.pi,1024)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + np.random.rand(t.shape[-1])
    y = x + np.random.rand(t.shape[-1])

    f1,c1 = tsa.coherency(np.vstack([x,y]))

    ij = [(0,1),(1,0)]
    f2,cache = tsa.cache_fft(np.vstack([x,y]),ij)

    c2 = tsa.cache_to_coherency(cache,ij)

    np.testing.assert_array_almost_equal(c1[1,0],c2[1,0])
    np.testing.assert_array_almost_equal(c1[0,1],c2[0,1])

def test_coherence_linear_dependence():
    """
    Tests that the coherence between two linearly dependent time-series
    behaves as expected.
    
    From William Wei's book, according to eq. 14.5.34, if two time-series are
    linearly related through:

    y(t)  = alpha*x(t+time_shift)

    then the coherence between them should be equal to:

    .. :math:
    
    C(\nu) = \frac{1}{1+\frac{fft_{noise}(\nu)}{fft_{x}(\nu) \cdot \alpha^2}}
    
    """
    t = np.linspace(0,16*np.pi,2**14)
    x = np.sin(t) + np.sin(2*t) + np.sin(3*t) + 0.1 *np.random.rand(t.shape[-1])
    N = x.shape[-1]

    alpha = 10
    m = 3
    noise = 0.1 * np.random.randn(t.shape[-1])
    y = alpha*(np.roll(x,m)) + noise

    f_noise = np.fft.fft(noise)[0:N/2]
    f_x = np.fft.fft(x)[0:N/2]

    c_t = ( 1/( 1 + ( f_noise/( f_x*(alpha**2)) ) ) )

    f,c = tsa.coherence(np.vstack([x,y]))
    c_t = np.abs(signaltools.resample(c_t,c.shape[-1]))

    np.testing.assert_array_almost_equal(c[0,1],c_t,2)
    
@dec.skipif(True)
def test_coherence_phase_spectrum ():
    assert False, "Test Not Implemented"

@dec.skipif(True)
def test_coherency_bavg():
    assert False, "Test Not Implemented"

@dec.skipif(True)
def test_coherence_partial():
    assert False, "Test Not Implemented"

@dec.skipif(True)
def test_coherence_partial_bavg():
    assert False, "Test Not Implemented"

#XXX def test_coherency_phase ()
#XXX def test_coherence_partial_phase()

@dec.skipif(True)
def test_fir():
    assert False, "Test Not Implemented"

@dec.skipif(True)
def test_percent_change():
    assert False, "Test Not Implemented"
                
def test_yule_walker_AR():
    arsig,_,_ = ut.ar_generator(N=512)
    avg_pwr = (arsig*arsig.conjugate()).mean()
    w, psd = tsa.yule_AR_est(arsig, 8, 1024)
    # for efficiency, let's leave out the 2PI in the numerator and denominator
    # for the following integral
    dw = 1./1024
    avg_pwr_est = np.trapz(psd, dx=dw)
    assert_almost_equal(avg_pwr, avg_pwr_est, decimal=2)

def test_LD_AR():
    arsig,_,_ = ut.ar_generator(N=512)
    avg_pwr = (arsig*arsig.conjugate()).mean()
    w, psd = tsa.LD_AR_est(arsig, 8, 1024)
    # for efficiency, let's leave out the 2PI in the numerator and denominator
    # for the following integral
    dw = 1./1024
    avg_pwr_est = np.trapz(psd, dx=dw)
    assert_almost_equal(avg_pwr, avg_pwr_est, decimal=2)
    
def test_periodogram():
    arsig,_,_ = ut.ar_generator(N=512)
    avg_pwr = (arsig*arsig.conjugate()).mean()
    f, psd = tsa.periodogram(arsig, N=2048)
    # for efficiency, let's leave out the 2PI in the numerator and denominator
    # for the following integral
    dw = 1./2048
    avg_pwr_est = np.trapz(psd, dx=dw)
    assert_almost_equal(avg_pwr, avg_pwr_est, decimal=1)
    
def permutation_system(N):
    p = np.zeros((N,N))
    targets = range(N)
    for i in xrange(N):
        popper = np.random.randint(0, high=len(targets))
        j = targets.pop(popper)
        p[i,j] = 1
    return p
                                   
