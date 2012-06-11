"""
Class for the calculation of photon-ALPs conversion

History:
- 11/15/11: created
- 05/08/12: adding reconversion in galactic magnetic field (GMF)
"""
__version__=0.02
__author__="M. Meyer // manuel.meyer@physik.uni-hamburg.de"


import numpy as np
from math import ceil
import eblstud.ebl.tau_from_model as Tau
from eblstud.ebl import mfn_model as MFN
from eblstud.misc.constants import *
import logging
import warnings

def Tau_Giorgio(z,E):
    """
    Tau calculation by Giorgio Galanti
    Fit to Franceschini Model
    E in eV
    """
    a00=29072.8078002930
    a01=-12189.9033508301
    a02=2032.30382537842
    a03=-168.504407882690
    a04=6.95066644996405
    a05=-0.114138037664816

    E *= 1e12

    c_a=[1003.34072943900,1744.79443325556,-3950.79983395431,3095.04470168520]

    anomal=c_a[0]+c_a[1]*z+c_a[2]*z**2.+c_a[3]*z**3.

    power = np.log10(E/(0.999+z)**-0.6)
    return anomal*z*10.**(a00+a01*power+a02*power**2. \
	    +a03*power**3.+a04*power**4.+a05*power**5.)

class PhotALPs(object):
    """
    Class for photon ALP conversion in the ingtergalactic magnetic field (IGMF)

    Attributes
    ----------
    Ld = Ldom1
    xi = g * B
    dz = redshift step

    tau = optical depth class
    E0 = initial energy
    Nd = number of domains
    z = maximum redshift

    mfn_print	= for debugging, unimportant
    dtau	= steps in optical depth
    Psin	= angle between IGMF and propagation direction in n-th domain
    dn		= delta parameter, see Notes
    EW1n	= Eigenvalue 1 of mixing matrix in n-th domain
    EW2n	= Eigenvalue 2 of mixing matrix in n-th domain
    EW3n	= Eigenvalue 3 of mixing matrix in n-th domain
    E0		= Energy in TeV
    Dn		= sqrt(1 - 4* dn**2.), see notes
    T1		= Transfer matrix 1
    T2		= Transfer matrix 2
    T3		= Transfer matrix 3
    Un		= Total transfermatrix in n-th domain

    Notes
    -----
    For Photon - ALP mixing theory see e.g. De Angelis et al. 2011 
    http://adsabs.harvard.edu/abs/2011PhRvD..84j5030D
    """

    def __init__(self, Ldom1=5., xi= 1., model='kneiske',filename='None'):
	"""
	Init photon-ALPs conversion class with 

	Parameters
	----------
	Ldom1: domain size at z=0 in Mpc, default: 5.
	xi: intergalactic magnetic field at z=0 in nG times photon-ALPs coupling strength in 10^-11 GeV^-1, defautl: 1
	model: EBL model to be used, default: 'kneiske'

	Returns
	-------
	Nothing
	"""
	self.Ld = Ldom1
	self.xi = xi
	self.dz = 1.17e-3 * self.Ld / 5.

	self.tau = Tau.OptDepth()
	#self.mfn = MFN.MFNModel(file_name='/home/manuel/projects/blazars/EBLmodelFiles/mfn_kneiske.dat.gz', model = 'kneiske')

	if filename == 'None':
	    self.tau.readfile(model = model)
	else:
	    self.tau.readfile(model = model, file_name = filename)

	self.E0 = 0.	# Energy in TeV
	self.Nd = 0.
	self.z = 0.

	self.mfn_print	= 0.
	self.dtau	= 0.
	self.Psin	= 0.
	self.dn		= 0.
	self.EW1n	= 0.
	self.EW2n	= 0.
	self.EW3n	= 0.
	self.Dn		= 0.
	self.T1		= np.zeros((3,3),np.complex)
	self.T2		= np.zeros((3,3),np.complex)
	self.T3		= np.zeros((3,3),np.complex)
	self.Un		= np.zeros((3,3),np.complex)
	return 

    def readz(self,z):
	"""
	set redshift and calculate number of domains

	Parameters
	----------
	z:	redshift

	Returns
	-------
	Nothing
	"""

	self.z = z
	self.Nd = int(ceil(0.85e3*5./self.Ld*z))
	return 

    def SetT1n(self):
	"""
	Set T1 in n-th domain
	
	Parameters
	----------
	None (self only)

	Returns
	-------
	Nothing
	"""
	s = np.sin(self.Psin)
	c = np.cos(self.Psin)
	self.T1[0,0] = c*c 
	self.T1[0,1] = -1.*s*c
	self.T1[1,0] = self.T1[0,1]
	self.T1[1,1] = s*s
	return

    def SetT2n(self):
	"""
	Set T2 in n-th domain
	
	Parameters
	----------
	None (self only)

	Returns
	-------
	Nothing
	"""
	s = np.sin(self.Psin)
	c = np.cos(self.Psin)
	self.T2[0,0] = 0.5* (1. + self.Dn) / self.Dn * s*s
	self.T2[0,1] = 0.5* (1. + self.Dn) / self.Dn * s*c
	#self.T2[0,2] = -1. * self.dn/self.Dn * s
	self.T2[0,2] = -1.j * self.dn/self.Dn * s
	self.T2[1,0] = self.T2[0,1]
	#self.T2[2,0] = -1. * self.T2[0,2]
	self.T2[2,0] = self.T2[0,2]

	self.T2[1,1] = 0.5* (1. + self.Dn) / self.Dn * c*c
	#self.T2[1,2] = -1. * self.dn/self.Dn * c
	self.T2[1,2] = -1.j * self.dn/self.Dn * c
	#self.T2[2,1] = -1. * self.T2[1,2]
	self.T2[2,1] = self.T2[1,2]

	self.T2[2,2] = 0.5* ( -1. + self.Dn ) / self.Dn
	return 

    def SetT3n(self):
	"""
	Set T3 in n-th domain
	
	Parameters
	----------
	None (self only)

	Returns
	-------
	Nothing
	"""
	s = np.sin(self.Psin)
	c = np.cos(self.Psin)
	self.T3[0,0] = 0.5* (-1. + self.Dn) / self.Dn * s*s
	self.T3[0,1] = 0.5* (-1. + self.Dn) / self.Dn * s*c
	#self.T3[0,2] = 1. * self.dn/self.Dn * s
	self.T3[0,2] = 1.j * self.dn/self.Dn * s
	self.T3[1,0] = self.T3[0,1]
	#self.T3[2,0] = -1. * self.T3[0,2]
	self.T3[2,0] = self.T3[0,2]

	self.T3[1,1] = 0.5* (-1. + self.Dn) / self.Dn * c*c
	#self.T3[1,2] = 1. * self.dn/self.Dn * c
	self.T3[1,2] = 1.j * self.dn/self.Dn * c
	#self.T3[2,1] = -1. * self.T3[1,2]
	self.T3[2,1] = self.T3[1,2]

	self.T3[2,2] = 0.5* ( 1. + self.Dn ) / self.Dn
	return 

    def SetUn(self):
	"""
	Set Transfer Matrix Un in n-th domain
	
	Parameters
	----------
	None (self only)

	Returns
	-------
	Nothing
	"""
	self.Un = np.exp(self.EW1n* self.Ln) * self.T1 \
	    + np.exp(self.EW2n* self.Ln) * self.T2 \
	    + np.exp(self.EW3n* self.Ln) * self.T3 
	return

    def SetDomainN(self,n):
	"""
	Set domain length, energy, magnetic field, mean free path and delta to n-th domain

	Parameters
	----------
	n:	Number of domain, 0 <= n <= self.Nd

	Returns:
	--------
	Un:	3x3 complex numpy array with transfer matrix Un of n-th domain
	"""

	En	= self.E0*(1. + (n-1.)*self.dz)
	#Bn	= self.B0*(1. + (n-1.)*self.dz)**2.
	difftau	=self.tau.opt_depth(n*self.dz , self.E0) - self.tau.opt_depth((n-1.)*self.dz , self.E0)
	#difftau	=Tau_Giorgio(n*self.dz , self.E0) - Tau_Giorgio((n-1.)*self.dz , self.E0)
	self.Ln	= 4.29e3*self.dz / (1. + 1.45*(n - 1.)*self.dz)
	if difftau:
	    mfn	= self.Ln / difftau 
	else:
	    #raise ValueError("difftau is zero!")
	    mfn	= self.Ln / 1e-20

	#mfn = self.mfn.get_mfn(n*self.dz , self.E0)*100./Mpc2cm
	self.mfn_print = mfn
	self.dtau= difftau
	# What's right? Alessandro (1) or Cssaki (2) et al.? 
	# The (1 + z)**2 factor comes from the B-field scaling
	#self.dn = 3.04e-2*self.xi*mfn*(1. + (n-1.)*self.dz)**2.
	self.dn = 0.11*self.xi*mfn*(1. + (n-1.)*self.dz)**2.
	self.Dn	= 1. - 4.*self.dn**2. + 0.j
	self.Dn = np.sqrt(self.Dn)
	self.EW1n = -0.5 / mfn 
	self.EW2n = -0.25 / mfn * ( 1. + self.Dn)
	self.EW3n = -0.25/ mfn * ( 1. - self.Dn)

	self.SetT1n()
	self.SetT2n()
	self.SetT3n()

	self.SetUn()
	return self.Un

# --- Conversion without absorption, designed to match values in Clusters -------------------------------------------#
from deltas import *
class PhotALPs_ICM(object):
    def __init__(self, Lcoh=10., B=1., r_abell=1500.*h , E_GeV = 1000., g = 1., m = 1., n = 1.):
	"""

	**** OUTDATED! USE conversion_ICM.py INSTEAD! ****

	init photon axion conversion in intracluster medium -> not energy independent, no absorption
	Lcoh: coherence length of Bfield in kpc
	B: B-field in muG
	r_abell: Abell radius of Cluster in kpc
	E_GeV: photon energy in GeV
	g: ALP-photon coupling in 10^-11 GeV^-1
	m: ALP mass in 10^-9 eV
	n: electron density in 10^-3 cm^-3
	"""

	self.Nd		= r_abell / Lcoh	# number of domains, no expansion assumed
	self.Lcoh	= Lcoh
	self.E		= E_GeV
	self.B		= B
	self.g		= g
	self.m		= m
	self.n		= n
	self.xi		= g * B			# xi parameter as in IGM case, in kpc
	self.Psin	= 0.			# angle between photon propagation on B-field in i-th domain 
	self.T1		= np.zeros((3,3),np.complex)	# Transfer matrices
	self.T2		= np.zeros((3,3),np.complex)
	self.T3		= np.zeros((3,3),np.complex)
	self.Un		= np.zeros((3,3),np.complex)
	return

    def __setDeltas(self):
	"""Set Deltas of mixing matrix"""
	self.Dperp	= Delta_pl_kpc(self.n,self.E) + 2.*Delta_QED_kpc(self.B,self.E)
	self.Dpar	= Delta_pl_kpc(self.n,self.E) + 3.5*Delta_QED_kpc(self.B,self.E)
	self.Dag	= Delta_ag_kpc(self.g,self.B)
	self.Da		= Delta_a_kpc(self.m,self.E)
	self.alph	= 0.5 * np.arctan(2. * self.Dag / (self.Dpar - self.Da)) # maybe arctan2?
	self.Dosc	= np.sqrt((self.Dpar - self.Da)**2. + 4.*self.Dag**2.)

	#logging.debug("Dperp, Dpar, Dag, Da, alph, Dosc: {0:.2e} {1:.2e} {2:.2e} {3:.2e} {4:.2e} {5:.2e}".format(self.Dperp, self.Dpar, self.Dag, self.Da, self.alph, self.Dosc))
	return

    def __setEW(self):
	"""Set Eigenvalues"""
	self.__setDeltas()
	self.EW1 = self.Dperp
	self.EW2 = 0.5 * (self.Dpar + self.Da - self.Dosc)
	self.EW3 = 0.5 * (self.Dpar + self.Da + self.Dosc)
	return
	

    def __setT1n(self):
	c = np.cos(self.Psin)
	s = np.sin(self.Psin)
	self.T1[0,0]	= c*c
	self.T1[0,1]	= -1. * c*s
	self.T1[1,0]	= self.T1[0,1]
	self.T1[1,1]	= s*s
	return

    def __setT2n(self):
	c = np.cos(self.Psin)
	s = np.sin(self.Psin)
	ca = np.cos(self.alph)
	sa = np.sin(self.alph)
	self.T2[0,0] = s*s*sa*sa
	self.T2[0,1] = s*c*sa*sa
	self.T2[0,2] = -1. * s * sa *ca

	self.T2[1,0] = self.T2[0,1]
	self.T2[1,1] = c*c*sa*sa
	self.T2[1,2] = -1. * c *ca * sa

	self.T2[2,0] = self.T2[0,2]
	self.T2[2,1] = self.T2[1,2]
	self.T2[2,2] = ca * ca
	return

    def __setT3n(self):
	c = np.cos(self.Psin)
	s = np.sin(self.Psin)
	ca = np.cos(self.alph)
	sa = np.sin(self.alph)
	self.T3[0,0] = s*s*ca*ca
	self.T3[0,1] = s*c*ca*ca
	self.T3[0,2] = s*sa*ca

	self.T3[1,0] = self.T3[0,1]
	self.T3[1,1] = c*c*ca*ca
	self.T3[1,2] = c * sa *ca

	self.T3[2,0] = self.T3[0,2]
	self.T3[2,1] = self.T3[1,2]
	self.T3[2,2] = sa*sa
	return

    def __setUn(self):
	""" set Transfer matrix in i-th domain """
	self.Un = np.exp(1.j * self.EW1 * self.Lcoh) * self.T1 + \
	np.exp(1.j * self.EW2 * self.Lcoh) * self.T2 + \
	np.exp(1.j * self.EW3 * self.Lcoh) * self.T3
	return

    def SetDomainN(self):
	"""set Transfer matrix to i-th domain"""
	self.__setEW()
	self.__setT1n()
	self.__setT2n()
	self.__setT3n()
	self.__setUn()
	#self.Un = np.round(self.Un,8)
	return self.Un
# --- Conversion in the galactic magnetic field ---------------------------------------------------------------------#
from gmf import gmf
from gmf.trafo import *
from kapteyn import wcs
from scipy.integrate import simps

pertubation = 0.10	# Limit for pertubation theory to be valid

class PhotALPs_GMF(PhotALPs_ICM):
    """

	**** OUTDATED! USE conversion_GMF.py INSTEAD! ****

    Class for conversion of ALP into photons in the regular component of the galactic magnetic field (GMF)

    Attributes
    ----------
    l: galactic longitude of source
    b: galactic latitude of source
    B: B GMF field instance (B-field in muG)
    g: ALP-photon coupling in 10^-11 GeV^-1
    m: ALP mass in 10^-9 eV
    n: electron density in 10^-3 cm^-3
    E: Energy in GeV
    d: postition of origin along x axis in GC coordinates
    """

    def __init__(self, pol_t = 1./np.sqrt(2.) , pol_u = 1./np.sqrt(2.), g = 1., m = 1., n = 1.e4, galactic = -1., rho_max = 20., zmax = 50., d = -8.5,Lcoh = 0.01):
	"""
	init GMF class

	Parameters
	----------
	pol_t: float (optional)
	    polarization of photon beam in one transverse direction
	    default: 0.5
	pol_u: float (optional)
	    polarization of photon beam in the other transverse direction
	    default: 0.5
	galactic: float (optional)
	    if -1: source is considered extragalactic. Otherwise provide distance from the sun in kpc
	    default: -1
	rho_max: float (optional)
	    maximal rho of GMF in kpc
	    default: 20 kpc
	zmax: float (optional)
	    maximal z of GMF in kpc
	    default: 50 kpc
	d : float (optional)
	    position of origin along x axis in GC coordinates
	    default is postion of the sun, i.e. d = -8.5kpc
	Lcoh : float (optional)
	    coherence length or step size for integration

	Returns
	-------
	None.
	"""
	super(PhotALPs_GMF,self).__init__(g = g, m = m, n = n, Lcoh = Lcoh)	#Inherit everything from PhotALPs_ICM

	self.l		= 0.
	self.b		= 0.
	self.smax	= 0.
	self.pol_t	= pol_t
	self.pol_u	= pol_u
	self.rho_max	= rho_max
	self.zmax	= zmax
	self.galactic	= galactic
	self.d		= d


	self.E		= 0.
	# ALP parameters: already provided in super call
	#self.g		= g
	#self.m		= m
	#self.n		= n
	# Initialize the Bfield the class
	self.Bgmf = gmf.GMF()

	return

    def set_coordinates(self, ra, dec):
	"""
	set the coordinates l,b and the the maximum distance smax where |GMF| > 0

	Parameters
	----------
	ra: float
	    right ascension of source in degrees
	dec: float
	    declination of source in degrees

	Returns
	-------
	l: float
	    galactic longitude
	b: float
	    galactic latitude
	smax: float
	    maximum distance from sun considered here where |GMF| > 0
	"""

	# Transformation RA, DEC -> L,B
	tran = wcs.Transformation("EQ,fk5,J2000.0", "GAL")
	self.l,self.b = tran.transform((ra,dec))
	d = self.d

	if self.galactic < 0.:
	    cl = np.cos(self.l)
	    cb = np.cos(self.b)
	    sb = np.sin(self.b)
	    self.smax = np.amin([self.zmax/np.abs(sb),1./np.abs(cb) * (-d*cl + np.sqrt(d**2 + cl**2 - d**2*cb + self.rho_max**2))])
	    #logging.debug("l,b,cl,cb,sb,smax: {0:.3f},{1:.3f},{2:.3f},{3:.3f},{4:.3f},{5:.3f}".format(self.l,self.b,cl,cb,sb,self.smax))
	else:
	    self.smax = self.galactic

	return self.l, self.b, self.smax

    def Bgmf_calc(self,s,l = 0.,b = 0.):
	"""
	compute GMF at (s,l,b) position where origin at self.d along x-axis in GC coordinates is assumed

	Parameters
	-----------
	s: float, distance from sun in kpc
	l: galactic longitude
	b: galactic latitude

	Returns
	-------
	GMF at this positon in galactocentric cylindrical coordinates (rho, phi, z) and field strength
	"""
	if not l:
	    l = self.l
	if not b:
	    b = self.b

	rho	= rho_HC2GC(s,l,b,self.d)	# compute rho in GC coordinates for s,l,b
	phi	= phi_HC2GC(s,l,b,self.d)	# compute phi in GC coordinates for s,l,b
	z	= z_HC2GC(s,l,b,self.d)		# compute z in GC coordinates for s,l,b

	B = self.Bgmf.Bdisk(rho,phi,z)[0] 	# add all field components
	B += self.Bgmf.Bhalo(rho,z)[0] 
	B += self.Bgmf.BX(rho,z)[0] 

	# Single components for debugging
	#B = self.Bgmf.Bdisk(rho,phi,z)[0] 	# add all field components
	#B = self.Bgmf.Bhalo(rho,z)[0] 
	#B = self.Bgmf.BX(rho,z)[0] 

	Babs = np.sqrt(np.sum(B**2.))	# compute overall field strength

	#logging.debug('rho,phi,z,Babs, Bfield = {0:.2f},{1:.2f},{2:.2f},{3},{4}'.format(rho,phi,z,Babs,B))

	return B,Babs

    def integrate_los(self,ra = 0.,dec = 0.):
	"""
	compute the line of sight integral of ALPs - Conversion probability,
	I_{t/u} = | \int_0^{s_\mathrm{max}} \mathrm{d}s \Delta_{a\gamma}^{t/u}(s) \exp(i(\Delta_a(s) - \Delta_{|| / \perp}(s))s) |^2

	Parameters
	-----------
	None
	(l,b,smax and energy need to be set!)

	Returns
	-------
	Values of I_t and I_u

	Notes
	-----
	See Mirizzi, Raffelt & Serpico (2007) Eq. A23
	and Simet, Hooper and Serpico (2008) Eq. 1
	and my theory lab book p. 149f
	"""

	#sa	= np.linspace(0.,self.smax,100)
	sa	= np.linspace(0.,self.smax,int(self.smax/self.Lcoh))
	kernel_t = np.zeros(sa.shape[0],np.complex)
	kernel_u = np.zeros(sa.shape[0],np.complex)
	#logging.debug("smax,l,b = {0},{1},{2}".format(self.smax,self.l,self.b))
	for i,s in enumerate(sa):

	    B,Babs	= self.Bgmf_calc(s)
	    Bs, Bt, Bu	= GC2HCproj(B, s, self.l, self.b,self.d)	# Compute Bgmf and the projection to HC coordinates (s,b,l)
	    sb,tb,ub	= HC_base(self.l,self.b)
	    Btrans	= Bt * tb + Bu * ub				# transverse Component
	    Btrans_abs	= np.sqrt(Bt**2. + Bu**2.)			# absolute value of transverse Component, needed for Delta_QED

#	    if Btrans_abs:
#		self.Psin	= np.arccos(Bt/Btrans_abs)				# angle between B and propagation direction, cos(Psi) = < B,s > / |B||s|
#		if Bu < 0.:
#		    self.Psin = 2.*np.pi - self.Psin
#	    else:
#		self.Psin = 0.
	    #logging.debug("Integrate Psi: {0:.5f}, Bu: {1:.5f}".format(self.Psin, Bu))
	    #logging.debug("Integrate: B cos(phi),B sin(phi), Bt, Bu: {0:.3f},{1:.3f},{2:.3f},{3:.3f}".format(Btrans_abs * np.cos(self.Psin), Btrans_abs * np.sin(self.Psin), Bt, Bu))

#	    Bu = np.sin(self.Psin) * Btrans_abs	# doesn't matter results are unchanged

	    #logging.debug("s,Bt,Bu,Btrans: {0:.3f},{1:.3f},{2:.3f},{3:.3f}".format(s,Bt,Bu,Btrans_abs))

	    # Compute the Delta factors
	    #Delta_ag_t	= Delta_ag_kpc(self.g,np.abs(Bt))
	    #Delta_ag_u	= Delta_ag_kpc(self.g,np.abs(Bu))
	    Delta_ag_t	= Delta_ag_kpc(self.g,Bt)
	    Delta_ag_u	= Delta_ag_kpc(self.g,Bu)


	    if Delta_ag_t > pertubation:
		warnings.warn("Warning: large Delta_ag_t = {0:.5f} detected in Integration at s = {1}".format(Delta_ag_t,s),RuntimeWarning)
	    if Delta_ag_u > pertubation:
		warnings.warn("Warning: large Delta_ag_u = {0:.5f} detected in Integration at s = {1}".format(Delta_ag_u,s),RuntimeWarning)


	    Delta_a	= Delta_a_kpc(self.m,self.E)
	    Delta_perp	= Delta_pl_kpc(self.n,self.E) + 2.*Delta_QED_kpc(Btrans_abs,self.E)	# perp goes together with t component
	    Delta_par 	= Delta_pl_kpc(self.n,self.E) + 3.5*Delta_QED_kpc(Btrans_abs,self.E)	# par goes together with u component

	    #logging.debug("Delta_a, Delta_perp, Delta_par: {0:.5f},{1:.5f},{2:.5f}".format(Delta_a, Delta_perp, Delta_par))
	    #logging.debug("Delta t,u : {0:.5f},{1:.5f}".format(Delta_ag_t, Delta_ag_u))

	    kernel_t[i] = Delta_ag_t*np.exp(1.j*s*(Delta_a - Delta_perp))	# Compute the kernel for the t polarization 
	    kernel_u[i] = Delta_ag_u*np.exp(1.j*s*(Delta_a - Delta_par))	# Compute the kernel for the u polarization

	    #logging.debug("s, kernet_t , kernel_u : {0:.3f} {1:.3f} {2:.3f}".format(s,kernel_t[i],kernel_u[i]))
	    #logging.debug("s, Delta_a - Delta_perp : {0} {1}".format(s,Delta_a - Delta_perp))
	    #logging.debug("exp t : {0}".format(np.exp(1.j*s*(Delta_a - Delta_perp))))

	m_t = kernel_t*np.conjugate(kernel_t) > 1e-20
	m_u = kernel_u*np.conjugate(kernel_u) > 1e-20
	
	#logging.debug('kernel t,u: {0}, {1}'.format(kernel_t[m_t], kernel_u[m_u]))

	if np.sum(m_t):
	    I_t = simps(kernel_t[m_t].real,sa[m_t]) + 1.j * simps(kernel_t[m_t].imag,sa[m_t])
	else:
	    I_t = 0.
	if np.sum(m_u):
	    I_u = simps(kernel_u[m_u].real,sa[m_u]) + 1.j * simps(kernel_u[m_u].imag,sa[m_u])
	else:
	    I_u = 0.

	#assert (I_t * np.conjugate(I_t)) == I_t.real**2. + I_t.imag**2.
	#logging.debug("I t , |I t|^2,u : {0}, {1}".format(I_t,I_t.real**2. + I_t.imag**2.))

	return (I_t * np.conjugate(I_t)).real, (I_u * np.conjugate(I_u)).real, (np.conjugate(I_u) * I_t).real

    def Pag(self, E, ra, dec, pol_t = -1 , pol_u = -1):
	"""
	compute the line of sight integral of ALPs - Conversion probability,
	I_{t/u} = | \int_0^{s_\mathrm{max}} \mathrm{d}s \Delta_{a\gamma}^{t/u}(s) \exp(i(\Delta_a(s) - \Delta_{|| / \perp}(s))s) |^2

	Parameters
	-----------
	E: float, Energy in GeV
	ra, dec: float, float, coordinates of the source in degrees
	pol_t: float, polarization of t direction (optional)
	pol_u: float, polarization of u direction (optional)

	Returns
	-------
	Pag: float, photon ALPs conversion probability

	Notes
	-----
	(1) See Mirizzi, Raffelt & Serpico (2007)
	(2) and Simet, Hooper and Serpico (2008)
	(3) and my theory lab book p. 149f
	"""
	self.set_coordinates(ra,dec)
	self.E		= E
	if pol_t > 0.:
	    self.pol_t	= pol_t
	if pol_u > 0.:
	    self.pol_u	= pol_u

	It, Iu, ItIu = self.integrate_los()

	# This is a hack - what to do if results largen than one? Pertubation theory not applicable?
	# I think my Integration
#	if It > 1:
#	    It = 1.
#	if Iu > 1:
#	    Iu = 1.
#	if ItIu > 1:
#	    ItIu = 1.
	    
	return self.pol_t ** 2. * It + self.pol_u ** 2. * Iu		# (1) - Eq. A23
	#return 2. * (pol_t ** 2. * It + pol_u ** 2. * Iu)	# (2) - Eq. 1
	#return (pol_t ** 2. + pol_u ** 2.) * (pol_t ** 2. * It + pol_u ** 2. * Iu + 2.*pol_u*pol_t*ItIu)	# (3) - p.149f
    def Pag_TM(self, E, ra, dec, pol, pol_final = None):
	"""
	Compute the conversion probability using the Transfer matrix formalism

	Parameters
	----------
	E: float, Energy in GeV
	ra, dec: float, float, coordinates of the source in degrees
	pol: np.array((3,3)): 3x3 matrix of the initial polarization
	Lcoh (optional): float, cell size
	pol_final (optional): np.array((3,3)): 3x3 matrix of the final polarization
	if none, results for final polarization in t,u and ALPs direction are returned

	Returns
	-------
	Pag: float, photon ALPs conversion probability

	Notes
	-----
	"""
	self.set_coordinates(ra,dec)
	self.E	= E
	# first domain is that one farthest away from us, i.e. that on the edge of the milky way
	logging.debug("smax {0:.5f}".format(self.smax))
	sa	= np.linspace(self.smax,0., int(self.smax/self.Lcoh),endpoint = False)	# divide distance into smax / Lcoh large cells

	U 	= np.diag(np.diag(np.ones((3,3), np.complex)))

	pol_t = np.zeros((3,3),np.complex)
	pol_t[0,0] += 1.
	pol_u = np.zeros((3,3),np.complex)
	pol_u[1,1] += 1.
	pol_unpol = 0.5*(pol_t + pol_u)
	pol_a = np.zeros((3,3),np.complex)
	pol_a[2,2] += 1.

	for i,s in enumerate(sa):
	    B,Babs	= self.Bgmf_calc(s)
	    Bs, Bt, Bu	= GC2HCproj(B, s, self.l, self.b,self.d)	# Compute Bgmf and the projection to HC coordinates (s,b,l)
	    sb,tb,ub	= HC_base(self.l,self.b)
	    Btrans	= Bt * tb + Bu * ub				# transverse Component
	    self.B	= np.sqrt(Bt**2. + Bu**2.)
	    if self.B:
		self.Psin	= np.arccos(Bt/self.B)			# angle between B and propagation direction, cos(Psi) = < B,s > / |B||s|
		if Bu < 0.:
		    self.Psin = 2.*np.pi - self.Psin
	    else:
		self.Psin = 0.

	    #logging.debug("Psi: {0:.5f}, Bu: {1:.5f}".format(self.Psin, Bu))
	    #logging.debug("s,Bt,Bu,Btrans: {0:.3f},{1:.3f},{2:.3f},{3:.3f}".format(s,Bt,Bu,self.B))
	    #logging.debug("B cos(phi),B sin(phi): {0:.3f},{1:.3f}".format(self.B * np.cos(self.Psin), self.B * np.sin(self.Psin)))

	    #assert np.round(self.B* np.cos(self.Psin),5) == np.round(Bt,5)
	    #assert np.round(self.B* np.sin(self.Psin),5) == np.round(Bu,5)

	    U = np.dot(U,super(PhotALPs_GMF,self).SetDomainN())							# calculate product of all transfer matrices

	    #logging.debug("s,U : {0}--------------\n{1}\n{2}\n{3}".format(s,Un[0,:],Un[1,:],Un[2,:]))
	    

	if pol_final == None:
	    Pt = np.sum(np.diag(np.dot(pol_t,np.dot(U,np.dot(pol,U.transpose().conjugate())))))	#Pt = Tr( pol_t U pol U^\dagger )
	    Pu = np.sum(np.diag(np.dot(pol_u,np.dot(U,np.dot(pol,U.transpose().conjugate())))))	#Pu = Tr( pol_u U pol U^\dagger )
	    Pa = np.sum(np.diag(np.dot(pol_a,np.dot(U,np.dot(pol,U.transpose().conjugate())))))	#Pa = Tr( pol_a U pol U^\dagger )
	    return Pt,Pu,Pa
	else:
	    return np.sum(np.diag(np.dot(pol_final,np.dot(U,np.dot(pol,U.transpose().conjugate())))))
