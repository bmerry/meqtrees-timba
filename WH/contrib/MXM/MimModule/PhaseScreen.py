#just a trick to import the phasescreen
import math
import numpy
from numpy.fft import *
from numpy.random import *

phasescreen=[];

def init_phasescreen(N=10,beta=5.):
    global phasescreen;
    # X,Y are matrices containing the x and y coordinates
    X = numpy.matrix(numpy.ones((2*N,1))) * numpy.matrix(range(-N,N))*1.0/N
    Y = numpy.matrix(range(-N,N)).T * numpy.matrix(numpy.ones((1,2*N)))*1.0/N
    # Q is the distance from the origin
    Q = numpy.sqrt(numpy.power(X,2) + numpy.power(Y,2))
    
    # W is complex white noise
    W = (standard_normal((2*N,2*N))) * numpy.exp(1j*uniform(-math.pi,math.pi,(2*N,2*N)))
    
    # Shape white noise by multiplying it by Q^(-2-beta)
    Q[N,N] = 1
    S = numpy.multiply(W, numpy.power(Q, -2-beta))
    S[N,N] = 0
    
    # Compute the inverse real ffts in both directions
    screen = numpy.real(ifft2(fftshift(S)));

    # Normalize phasescreen to have all values between -1 and 1
    print "in PhaseScreen",len(screen);
    minscreen = numpy.min(screen)
    print "Min screen", minscreen
    maxscreen = numpy.max(numpy.abs(screen));
    print "Max screen", maxscreen;
    phasescreen = screen / maxscreen;
    print "****************************************************************************************"
    print phasescreen
    print "****************************************************************************************"