import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.constants as spc

def ftomz(f, b):
    return (spc.constants.e*b) / (2*spc.pi*f) / 1.660539e-27

f = 1000000
t = np.arange(0, 0.1-1/f, 1/f)
y = np.sin(2 * np.pi * (f/10) * t)
print('freq = ' + str(f/10))

yD = np.fft.rfft(y)
yD = np.abs(yD)**2
xD = np.fft.rfftfreq(y.shape[0], d=1./f)

#yD = yD[xD.shape[0]-1:]
vfunc = np.vectorize(ftomz)

print(ftomz(196642, 9.35))
print(xD)
xD = vfunc(xD[1:], 9.34)
print(xD)

fig, ax = plt.subplots()
ax.plot(xD, yD[1:])
plt.show()

