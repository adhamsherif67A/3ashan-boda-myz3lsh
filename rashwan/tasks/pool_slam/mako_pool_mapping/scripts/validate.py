"""Cross-check database loop links, optimized geometry, cloud and video artifacts."""
import argparse
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import numpy as np


def pose_matrix(values):
    x,y,z,qx,qy,qz,qw=values
    q=np.array([qx,qy,qz,qw],dtype=float);q/=np.linalg.norm(q)
    xq,yq,zq,wq=q
    r=np.array([[1-2*(yq*yq+zq*zq),2*(xq*yq-zq*wq),2*(xq*zq+yq*wq)],
                [2*(xq*yq+zq*wq),1-2*(xq*xq+zq*zq),2*(yq*zq-xq*wq)],
                [2*(xq*zq-yq*wq),2*(yq*zq+xq*wq),1-2*(xq*xq+yq*yq)]])
    t=np.eye(4);t[:3,:3]=r;t[:3,3]=[x,y,z];return t


def read_poses(path):
    result={}
    if path.exists():
        for line in path.read_text().splitlines():
            if not line or line.startswith('#'):continue
            values=list(map(float,line.split()))
            if len(values)==9:result[int(values[-1])]=pose_matrix(values[1:8])
    return result


def constraint_error(a,b,measurement):
    residual=np.linalg.inv(measurement)@np.linalg.inv(a)@b
    translation=float(np.linalg.norm(residual[:3,3]))
    angle=math.degrees(math.acos(float(np.clip((np.trace(residual[:3,:3])-1)/2,-1,1))))
    return {'translation_m':translation,'rotation_deg':angle}


def se3_aligned_rmse(points,reference):
    """Standard ATE alignment: rigid rotation + translation only, never scale."""
    x=points-points.mean(axis=0);y=reference-reference.mean(axis=0)
    u,_singular,vt=np.linalg.svd(x.T@y)
    rotation=vt.T@u.T
    if np.linalg.det(rotation)<0:
        vt[-1]*=-1;rotation=vt.T@u.T
    errors=(rotation@x.T).T-y
    return float(np.sqrt(np.mean(np.sum(errors*errors,axis=1))))


def validate(folder):
    db=sqlite3.connect('file:'+str((folder/'pool.db').resolve())+'?mode=ro',uri=True)
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    count=db.execute('SELECT count(*) FROM Node').fetchone()[0]
    links=db.execute('SELECT from_id,to_id,type,transform FROM Link WHERE type=1').fetchall()
    optimized=read_poses(folder/'pool_optimized_poses.txt')
    raw=read_poses(folder/'pool_raw_poses.txt')
    stamps=dict(db.execute('SELECT id,stamp FROM Node').fetchall())
    reference_path=folder/'evaluation_ground_truth.txt'
    reference=np.loadtxt(reference_path,ndmin=2) if reference_path.exists() else np.empty((0,8))
    def ground_truth(node_id):
        if len(reference)==0 or node_id not in stamps:return None
        index=int(np.argmin(np.abs(reference[:,0]-stamps[node_id])))
        if abs(reference[index,0]-stamps[node_id])>.08:return None
        return pose_matrix(reference[index,1:8])
    report={'database_integrity':integrity,'database_nodes':count,'unique_global_loop_links':0,
            'loop_constraint_residuals':[]}
    seen=set()
    for a,b,kind,blob in links:
        pair=tuple(sorted((a,b)))
        if pair in seen:continue
        seen.add(pair)
        if a in optimized and b in optimized and a in raw and b in raw and len(blob)==48:
            measurement=np.eye(4);measurement[:3,:]=np.frombuffer(blob,dtype=np.float32).reshape(3,4)
            row={'from':a,'to':b,
              'before':constraint_error(raw[a],raw[b],measurement),
              'after':constraint_error(optimized[a],optimized[b],measurement)}
            gt_a,gt_b=ground_truth(a),ground_truth(b)
            if gt_a is not None and gt_b is not None:
                row['independent_ground_truth_error']=constraint_error(gt_a,gt_b,measurement)
            report['loop_constraint_residuals'].append(row)
    report['unique_global_loop_links']=len(seen)
    report['active_global_loop_links']=len(report['loop_constraint_residuals'])
    report['retained_inactive_links']=len(seen)-len(report['loop_constraint_residuals'])
    cloud=folder/'pool_optimized_cloud.ply'
    report['cloud_vertices']=0
    if cloud.exists():
        with cloud.open('rb') as f:
            for _ in range(100):
                line=f.readline().decode('ascii',errors='ignore').strip()
                if line.startswith('element vertex '):report['cloud_vertices']=int(line.split()[-1])
                if line=='end_header':break
    video=folder/'loop_closure_demo.mp4'
    report['video_duration_s']=0.0
    if video.exists():
        result=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                    '-of','default=noprint_wrappers=1:nokey=1',str(video)],capture_output=True,text=True)
        if result.returncode==0:report['video_duration_s']=float(result.stdout.strip())
    report['drift_correction_demonstrated']=any(
        row['before']['translation_m']>.01 and row['after']['translation_m']<row['before']['translation_m']*.8
        for row in report['loop_constraint_residuals'])
    report['ground_truth_checked_links']=sum('independent_ground_truth_error' in r for r in report['loop_constraint_residuals'])
    report['global_links_geometrically_consistent']=bool(report['loop_constraint_residuals']) and all(
        'independent_ground_truth_error' in r and r['independent_ground_truth_error']['translation_m']<.3
        and r['independent_ground_truth_error']['rotation_deg']<8
        for r in report['loop_constraint_residuals'])
    common=sorted(i for i in raw if i in optimized and ground_truth(i) is not None)
    if common:
        first=common[0];gt_first=ground_truth(first)
        for name,poses in [('raw',raw),('optimized',optimized)]:
            align=gt_first@np.linalg.inv(poses[first])
            errors=[float(np.linalg.norm((align@poses[i])[:3,3]-ground_truth(i)[:3,3])) for i in common]
            report[name+'_position_rmse_m']=float(np.sqrt(np.mean(np.square(errors))))
            points=np.array([poses[i][:3,3] for i in common])
            reference_points=np.array([ground_truth(i)[:3,3] for i in common])
            report[name+'_se3_aligned_rmse_m']=se3_aligned_rmse(points,reference_points)
        report['trajectory_metric_note']='position_rmse_m pins the first pose; se3_aligned_rmse_m is standard rigid SE(3)-aligned ATE, without scale. Both are reported to expose frame/anchor effects.'
    report['trajectory_accuracy_acceptable']=report.get('optimized_se3_aligned_rmse_m',float('inf'))<.5
    report['all_deliverables_verified']=(integrity=='ok' and count>10 and len(seen)>0
       and report['cloud_vertices']>1000 and report['video_duration_s']>10
       and report['drift_correction_demonstrated'] and report['global_links_geometrically_consistent']
       and report['trajectory_accuracy_acceptable']
       and report.get('optimized_se3_aligned_rmse_m',float('inf'))<report.get('raw_se3_aligned_rmse_m',0))
    (folder/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);args=parser.parse_args();validate(args.folder)
