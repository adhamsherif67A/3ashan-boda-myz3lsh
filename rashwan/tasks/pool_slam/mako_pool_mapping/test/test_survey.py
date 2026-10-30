import importlib.util
import sys
from pathlib import Path
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from mako_pool_mapping.survey_routes import route, wrap
from coverage import bin_surface

class SurveyTests(unittest.TestCase):
    def test_yaw_wrap_takes_short_path_across_pi(self):
        self.assertAlmostEqual(wrap(np.deg2rad(-179-179)),np.deg2rad(2))

    def test_survey_views_and_clearance(self):
        targets=route('coverage')
        self.assertTrue(all(abs(x)<=3.5 and abs(y)<=2.5 and -2.6<z<-.35 for x,y,z,a in targets))
        headings={round(a,4) for x,y,z,a in targets}
        self.assertGreaterEqual(len(headings),8)
        self.assertEqual(targets[-1],(0.,0.,-1.5,0.))

    def test_surface_coverage_counts_real_cells_without_filling_holes(self):
        points=np.array([[.1,.1],[.2,.2],[.9,.9]])
        mask=bin_surface(points,[(0,1),(0,1)],.5)
        self.assertEqual(int(mask.sum()),2);self.assertEqual(mask.size,4)

if __name__=='__main__':unittest.main()
