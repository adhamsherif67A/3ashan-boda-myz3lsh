#ifndef THRUSTER_HPP
#define THRUSTER_HPP

#include <string>

using namespace std;

class Thruster
{
private:
    int speed;
    string status;

public:
    Thruster();
    void setSpeed(int newSpeed);
    string getStatus() const;
};

#endif