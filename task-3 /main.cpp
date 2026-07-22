#include <iostream>
#include "Thruster.hpp"

using namespace std;

int main()
{
    Thruster myThruster;

    cout << myThruster.getStatus() << endl;

    myThruster.setSpeed(50);
    cout << myThruster.getStatus() << endl;

    myThruster.setSpeed(-20);
    cout << myThruster.getStatus() << endl;

    myThruster.setSpeed(0);
    cout << myThruster.getStatus() << endl;

    return 0;
}