    case SUB_FRAME_CUSTOM:
        _frame_class_string = "CUSTOM";
        // Fish ROV Omni Six: front right, front left, rear right, rear left, mid right, mid left.
        //                                    roll    pitch   yaw     climb   forward lateral order
        add_motor_raw_6dof(AP_MOTORS_MOT_1,     0.45f,  0.45f,  0.45f,  0.45f,  0.77f,  0.45f,  1);
        add_motor_raw_6dof(AP_MOTORS_MOT_2,     0.45f,  0.45f, -0.45f,  0.45f,  0.77f, -0.45f,  2);
        add_motor_raw_6dof(AP_MOTORS_MOT_3,     0.39f, -0.39f, -0.39f,  0.39f,  0.84f,  0.39f,  3);
        add_motor_raw_6dof(AP_MOTORS_MOT_4,     0.39f, -0.39f,  0.39f,  0.39f,  0.84f, -0.39f,  4);
        add_motor_raw_6dof(AP_MOTORS_MOT_5,     1.00f,  0.03f,  0.00f,  1.00f,  0.00f,  1.00f,  5);
        add_motor_raw_6dof(AP_MOTORS_MOT_6,    -1.00f,  0.03f,  0.00f,  1.00f,  0.00f, -1.00f,  6);
        break;

