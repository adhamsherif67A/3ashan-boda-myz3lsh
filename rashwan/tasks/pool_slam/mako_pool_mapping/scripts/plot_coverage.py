"""Offline visualization of measured exported-cloud coverage (requires matplotlib)."""
import argparse
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def main(folder):
    report=json.loads((folder/'coverage.json').read_text())
    masks=np.load(folder/'coverage_cells.npz')
    extents={'floor':[-7,7,-6,6],'east_wall':[-6,6,-3,0],
             'north_wall':[-7,7,-3,0],'south_wall':[-7,7,-3,0]}
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    for ax,name in zip(axes.flat,extents):
        ax.imshow(masks[name].T,origin='lower',extent=extents[name],interpolation='nearest',
                  cmap=ListedColormap(['#fff2df','#147d92']),vmin=0,vmax=1,aspect='equal')
        score=report['surfaces'][name]['coverage_percent']
        ax.set_title(f'{name.replace("_"," ").title()}: {score:.1f}% observed')
        ax.set_xlabel(('Y' if name=='east_wall' else 'X')+' (m)')
        ax.set_ylabel(('Y' if name=='floor' else 'Z')+' (m)')
    fig.suptitle('Actual pool-map coverage: blue = observed cells; cream = missing\n25 cm cells; no interpolation or geometry filling',fontsize=13)
    fig.savefig(folder/'coverage.png',dpi=150);plt.close(fig)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    main(parser.parse_args().folder)
