"""Render measured trajectories and loop-constraint residuals from a saved run."""
import argparse
import json
from pathlib import Path
import sqlite3
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from validate import read_poses, pose_matrix

def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);args=parser.parse_args()
    folder=args.folder
    raw=read_poses(folder/'pool_raw_poses.txt');optimized=read_poses(folder/'pool_optimized_poses.txt')
    reference=np.loadtxt(folder/'evaluation_ground_truth.txt',ndmin=2)
    stamps=dict(sqlite3.connect('file:'+str((folder/'pool.db').resolve())+'?mode=ro',uri=True).execute('select id,stamp from Node'))
    ids=sorted(i for i in raw if i in optimized)
    gt={i:pose_matrix(reference[np.argmin(abs(reference[:,0]-stamps[i])),1:8]) for i in ids}
    report=json.loads((folder/'validation.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    actual=np.array([gt[i][:3,3] for i in ids]);axes[0].plot(actual[:,0],actual[:,1],'k--',lw=2,label='Gazebo reference (evaluation only)')
    for name,poses,color in [('Raw visual odometry',raw,'#de6845'),('Optimized map',optimized,'#18935e')]:
        alignment=gt[ids[0]]@np.linalg.inv(poses[ids[0]])
        points=np.array([(alignment@poses[i])[:3,3] for i in ids])
        axes[0].plot(points[:,0],points[:,1],color=color,lw=1.5,label=name)
    axes[0].set(xlabel='World X (m)',ylabel='World Y (m)',title='Trajectory (first-pose alignment)')
    axes[0].axis('equal');axes[0].grid(alpha=.3);axes[0].legend(fontsize=8)
    rows=report['loop_constraint_residuals'];x=np.arange(len(rows))
    axes[1].bar(x-.18,[100*r['before']['translation_m'] for r in rows],.36,label='Before optimization',color='#de6845')
    axes[1].bar(x+.18,[100*r['after']['translation_m'] for r in rows],.36,label='After optimization',color='#18935e')
    axes[1].set(xlabel='Accepted global loop constraint',ylabel='Translation residual (cm)',title='Loop-constraint consistency')
    axes[1].legend(fontsize=8);axes[1].grid(axis='y',alpha=.3)
    fig.savefig(folder/'trajectory_and_loop_errors.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
