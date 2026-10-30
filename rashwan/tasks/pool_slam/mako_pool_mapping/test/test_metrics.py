import importlib.util
from pathlib import Path
import unittest
import numpy as np
spec=importlib.util.spec_from_file_location('metrics',Path(__file__).resolve().parents[1]/'scripts/validate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ResidualTests(unittest.TestCase):
    def test_exact_constraint_zero_with_rotation(self):
        a=m.pose_matrix([2,3,1,0,0,np.sin(.3),np.cos(.3)])
        measurement=m.pose_matrix([1,0,0,0,0,np.sin(.1),np.cos(.1)])
        result=m.constraint_error(a,a@measurement,measurement)
        self.assertAlmostEqual(result['translation_m'],0,places=10)
        self.assertAlmostEqual(result['rotation_deg'],0,places=5)

    def test_detects_and_quantifies_real_constraint_error(self):
        identity=np.eye(4);drifted=np.eye(4);drifted[0,3]=.4
        result=m.constraint_error(identity,drifted,identity)
        self.assertAlmostEqual(result['translation_m'],.4)
        self.assertEqual(m.constraint_error(identity,identity,identity)['translation_m'],0)

    def test_se3_alignment_removes_frame_offset_but_not_scale_error(self):
        points=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
        r=m.pose_matrix([2.,3.,4.,0.,0.,np.sin(.4),np.cos(.4)])
        reference=(r[:3,:3]@points.T).T+r[:3,3]
        self.assertAlmostEqual(m.se3_aligned_rmse(points,reference),0.,places=10)
        self.assertGreater(m.se3_aligned_rmse(points*2,reference),.1)

if __name__=='__main__':unittest.main()
