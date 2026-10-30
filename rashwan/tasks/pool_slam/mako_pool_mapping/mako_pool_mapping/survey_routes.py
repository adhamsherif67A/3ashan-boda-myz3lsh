"""Coverage routes and heading math independent of ROS."""
import math

def wrap(angle):return math.atan2(math.sin(angle),math.cos(angle))

def route(kind,size=1.5):
    if kind=='rectangle':
        return [(0.,0.,-1.,0.),(size,0.,-1.,0.),(size,size,-1.,0.),(0.,size,-1.,0.),(0.,0.,-1.,0.)]
    headings=[0.,-math.pi/4,-math.pi/2,-3*math.pi/4,-math.pi,3*math.pi/4,math.pi/2,math.pi/4,0.]
    if kind=='yaw':return [(0.,0.,-1.5,a) for a in headings]
    if kind=='coverage':
        # A central 360 view plus four off-center views cover the center blind
        # spot and look back at each wall. Consecutive turns are only 45 degrees.
        result=[]
        for x,y in [(0.,0.),(3.5,2.5),(-3.5,2.5),(-3.5,-2.5),(3.5,-2.5),(0.,0.)]:
            result.extend((x,y,-1.5,a) for a in headings)
        return result
    raise ValueError('Unknown route: '+kind)
