import random, numpy as np

def sparse2wave(self, sparseData):

    return waveData










def randWaveData(self):
    count = random.randint(1,100)
    var = random.randint(-5,10)
    newData = np.array([var-1,var])
    for i in range(count):
        data = np.array([var, random.randint(1,10)])
        var = var + 1
        newData = np.vstack((newData, data))
    return newData