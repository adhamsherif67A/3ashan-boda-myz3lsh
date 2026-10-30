#include "mako_ps4_control/controls.hpp"
#include <limits>
#include <iostream>
#include <stdexcept>
void check(bool ok) { if(!ok) throw std::runtime_error("Control test failed"); }
int main() {
  mako::Mapping m; std::vector<float> a(6,0);
  auto n=mako::map(a,m,true); check(n.x==0 && n.y==0 && n.z==500 && n.r==0);
  for(int index=0;index<4;++index) {
    a.assign(6,0);a[index]=1;
    const auto c=mako::map(a,m,true);
    check((c.x!=0)==(index==1)); check((c.y!=0)==(index==0));
    check((c.z!=500)==(index==3)); check((c.r!=0)==(index==2));
  }
  a={-1,1,-1,1,0,0}; auto c=mako::map(a,m,true);
  check(c.x==-500 && c.y==-500 && c.z==750 && c.r==500);
  m.lateral_sign=-1; const auto flipped=mako::map(a,m,true);
  check(flipped.y==-c.y && flipped.x==c.x && flipped.z==c.z && flipped.r==c.r);
  m.lateral_sign=1;
  auto disabled=mako::map(a,m,false);check(disabled.x==0 && disabled.z==500);
  a[1]=std::numeric_limits<float>::quiet_NaN();
  auto bad=mako::map(a,m,true);check(bad.x==0 && bad.z==500 && !mako::centered(a,m));
  check(mako::map({},m,true).z==500);
  a.assign(6,0.04f); check(mako::centered(a,m) && mako::map(a,m,true).x==0);
  a[0]=0.2; check(!mako::centered(a,m));
  m.gain=1;
  for(float v : {-10.f,-1.f,0.f,1.f,10.f}) {
    a.assign(6,v); c=mako::map(a,m,true);
    check(std::abs(c.x)<=1000 && std::abs(c.y)<=1000 && std::abs(c.r)<=1000 && c.z>=0 && c.z<=1000);
  }
  mako::PressEdge edge;
  check(!edge.update(true)); check(!edge.update(false));check(edge.update(true));
  check(!edge.update(true));check(!edge.update(false));check(edge.update(true));
  edge.reset();check(!edge.update(true));
  std::cout<<"PASS: axis isolation, signs, neutral, bounds, invalid input, deadzone, button edge\n";
}
