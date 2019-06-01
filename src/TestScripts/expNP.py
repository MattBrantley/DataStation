import numpy as np

a = np.array([np.nan, 1, np.nan, np.nan, 2, np.nan, np.nan, 4, np.nan, np.nan, np.nan, np.nan, 6, np.nan, np.nan, np.nan])

print(a)

ind = np.where(~np.isnan(a))[0]
for i in range(0, len(ind)-1):
    a[ind[i]:ind[i+1]] = a[ind[i]]

a[ind[-1]:] = a[ind[-1]]
a[:ind[0]] = a[ind[0]]

# first, last = ind[0], ind[-1]
# a[:first] = a[first]
# a[last + 1:] = a[last]

print(a)