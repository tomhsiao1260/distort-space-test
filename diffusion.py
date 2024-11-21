import nrrd
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
from matplotlib.colors import ListedColormap
from scipy.ndimage import convolve

def update_potential(potential):
    pc = potential.copy()

    pc[1:-1, 1:-1]  = potential[1:-1, :-2]
    pc[1:-1, 1:-1] += potential[1:-1, 2:]
    pc[1:-1, 1:-1] += potential[:-2, 1:-1]
    pc[1:-1, 1:-1] += potential[2:, 1:-1]
    pc[1:-1, 1:-1] /= 4

    pc[0, :]  = pc[1, :]
    pc[-1, :] = pc[-2, :]
    pc[:, 0]  = pc[:, 1]
    pc[:, -1] = pc[:, -2]
    return pc

def update_mask(potential, mask, counts):
    pc = potential.copy()

    sums = np.bincount(mask.flatten(), weights=pc.flatten(), minlength=256)
    averages = np.zeros_like(sums)
    nonzero = counts > 0
    averages[nonzero] = sums[nonzero] / counts[nonzero]

    pc = averages[mask]
    return pc

def update_mask_potential(potential, mask, kernel_size=3):
    kernel = np.ones((kernel_size, kernel_size))

    binary_mask = (mask > 0).astype(int)
    counts = convolve(binary_mask, kernel, mode='constant', cval=0)
    counts[counts == 0] = 1

    sums = convolve(potential * binary_mask, kernel, mode='constant', cval=0)
    updated_potential = sums / counts
    return updated_potential

if __name__ == '__main__':
    z, y, x, layer = 3513, 1900, 3400, 0
    mask_dir = f'/Users/yao/Desktop/distort-space-test/{z:05}_{y:05}_{x:05}_mask.nrrd'

    # plot init
    fig, axes = plt.subplots(2, 3, figsize=(7, 3))

    axes = axes.ravel()
    for ax in axes: ax.axis('off')

    # load boundary
    boundary, header = nrrd.read(mask_dir)
    boundary = boundary[layer]
    boundary = boundary[140:600]

    top_label, bot_label = 3, 1
    h, w = boundary.shape

    # mask
    mask = np.zeros_like(boundary, dtype=np.uint8)

    mask[boundary == top_label] = top_label
    # mask[boundary == bot_label] = bot_label

    mask_plot = np.zeros_like(mask, dtype=np.uint8)
    mask_plot[mask > 0] =  255
    axes[0].imshow(mask_plot, cmap='gray')

    # potential
    potential = np.zeros_like(mask,  dtype=float)

    for i in range(h): potential[i, :] = (i / h) * 255
    potential[:10, :] = 255
    potential[-10:, :] = 0

    boundary_mask = np.zeros_like(mask, dtype=bool)
    boundary_mask[:10, :] = True
    boundary_mask[-10, :] = True

    colors = ['#000000', '#ffffff'] * 20
    cmap = ListedColormap(colors)
    counts = np.bincount(mask.flatten(), minlength=256)

    axes[1].imshow(potential, cmap=cmap)

    # update potential
    plt.ion()

    for i in range(12000):
        pc = potential.copy()

        pc = update_potential(pc)
        pc[boundary_mask] = potential[boundary_mask]

        # pcm = update_mask(pc, mask, counts)
        pcm = update_mask_potential(pc, mask)

        pcm[mask <= 0] = pc[mask <= 0]
        pcm[boundary_mask] = pc[boundary_mask]

        potential = pcm

        if (i%100 == 0):
            print(i)
            axes[2].imshow(potential, cmap=cmap)

            plt.pause(0.01)

    plt.ioff()

    # show the plot
    plt.show()
