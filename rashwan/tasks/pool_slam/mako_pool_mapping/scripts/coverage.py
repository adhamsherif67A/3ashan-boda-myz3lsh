"""Measure observed pool floor/inner-wall coverage from the actual exported PLY."""
import argparse
import json
from pathlib import Path
import sqlite3
import numpy as np
from validate import read_poses, pose_matrix


def read_cloud(path):
    types={'float':'<f4','double':'<f8','uchar':'u1','char':'i1','int':'<i4','uint':'<u4','short':'<i2','ushort':'<u2'}
    with path.open('rb') as f:
        count=0;fields=[];vertex=False;binary=False
        while True:
            line=f.readline().decode('ascii').strip()
            if line=='end_header':break
            if line.startswith('format '):binary='binary_little_endian' in line
            if line.startswith('element '):
                words=line.split();vertex=words[1]=='vertex'
                if vertex:count=int(words[2])
            elif vertex and line.startswith('property '):
                _,kind,name=line.split();fields.append((name,types[kind]))
        if not binary:raise ValueError('Expected a binary little-endian RTAB-Map PLY')
        points=np.fromfile(f,dtype=np.dtype(fields),count=count)
    return np.column_stack([points[k] for k in ['x','y','z']])


def bin_surface(uv,bounds,resolution):
    (a0,a1),(b0,b1)=bounds
    shape=(int(np.ceil((a1-a0)/resolution)),int(np.ceil((b1-b0)/resolution)))
    hits=np.zeros(shape,dtype=bool)
    keep=(uv[:,0]>=a0)&(uv[:,0]<=a1)&(uv[:,1]>=b0)&(uv[:,1]<=b1)
    indices=np.floor((uv[keep]-[a0,b0])/resolution).astype(int)
    if len(indices):
        indices=np.minimum(indices,np.array(shape)-1);hits[indices[:,0],indices[:,1]]=True
    return hits


def measure(folder,resolution=.25,tolerance=.25):
    points=read_cloud(folder/'pool_optimized_cloud.ply')
    poses=read_poses(folder/'pool_optimized_poses.txt')
    reference=np.loadtxt(folder/'evaluation_ground_truth.txt',ndmin=2)
    db=sqlite3.connect('file:'+str((folder/'pool.db').resolve())+'?mode=ro',uri=True)
    stamps=dict(db.execute('select id,stamp from Node'))
    first=min(poses);sample=reference[np.argmin(abs(reference[:,0]-stamps[first]))]
    transform=pose_matrix(sample[1:8])@np.linalg.inv(poses[first])
    points=(transform[:3,:3]@points.T).T+transform[:3,3]
    points=points[np.all(np.isfinite(points),axis=1)]
    surfaces={
      'floor':(np.abs(points[:,2]+3)<tolerance,[0,1],[(-7,7),(-6,6)]),
      'east_wall':(np.abs(points[:,0]-7)<tolerance,[1,2],[(-6,6),(-3,0)]),
      'north_wall':(np.abs(points[:,1]-6)<tolerance,[0,2],[(-7,7),(-3,0)]),
      'south_wall':(np.abs(points[:,1]+6)<tolerance,[0,2],[(-7,7),(-3,0)])}
    report={'resolution_m':resolution,'plane_tolerance_m':tolerance,
      'reference':'First exported map pose rigidly aligned to independent Gazebo reference; reference is not used by SLAM.',
      'scope':'14x12 m floor and three inner wet walls z=-3..0; pool has no west wall.',
      'surfaces':{}}
    masks={}
    for name,(keep,axes,bounds) in surfaces.items():
        mask=bin_surface(points[keep][:,axes],bounds,resolution);masks[name]=mask
        report['surfaces'][name]={'observed_cells':int(mask.sum()),'total_cells':mask.size,
                                 'coverage_percent':100.*float(mask.mean())}
    report['coverage_target_met']=all(v['coverage_percent']>=95. for v in report['surfaces'].values())
    (folder/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(folder/'coverage_cells.npz',**masks)
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    args=parser.parse_args();measure(args.folder)
