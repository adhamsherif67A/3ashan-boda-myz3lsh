#include "Thruster.hpp"

Thruster::Thruster() : speed(0), status("Idle") {}

void Thruster::setSpeed(int newSpeed)
{
    speed = newSpeed;
    if (speed == 0)
    {
        status = "Idle";
    }
    else if (speed > 0)
    {
        status = "Moving Forward";
    }
    else
    {
        status = "Moving Backward";
    }
}

string Thruster::getStatus() const
{
    return status;
}