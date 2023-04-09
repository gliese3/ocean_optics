import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d, median_filter
import matplotlib as mpl

folder = "E:\\Spectroscopy data"

name = "FAMAPbBr09I01_2-microcrystal_04-06-2023"
data = np.loadtxt(f"{folder}\\{name}\\run 3.csv", skiprows=1, delimiter=",")

_, steps = data.shape

# create colors for plot
cmap = mpl.cm.get_cmap("turbo", steps - 1)
cmaplist = [cmap(i) for i in range(steps - 1)][::-1]

# wavelengths
x = data[:, 0]

for i, step in enumerate(range(1, steps)): # steps
    plt.plot(x, gaussian_filter1d(median_filter(data[:, step], 3), 5), color=cmaplist[i], label=f"step {step}", alpha=0.8) # by default 3 and 5
    
plt.grid()
# plt.legend()
plt.title("red-beginning, blue-end")
plt.xlabel("Wavelength, nm")
plt.ylabel("Intensity, a.u.")
plt.show()