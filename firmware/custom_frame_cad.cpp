    case SUB_FRAME_CUSTOM:
        _frame_class_string = "CUSTOM";
        // Fish CAD-calibrated SITL mixer. See firmware/allocation.json.
        //                               roll pitch yaw climb forward lateral test
        add_motor_raw_6dof(AP_MOTORS_MOT_1, -0.602347273f, 0.999993064f, -0.000000102f, 1.000000000f, -0.000005226f, -1.000000000f, 1);
        add_motor_raw_6dof(AP_MOTORS_MOT_2, 0.602344793f, 1.000000000f, -0.000000012f, 0.999994795f, 0.000005340f, 0.999995668f, 2);
        add_motor_raw_6dof(AP_MOTORS_MOT_3, -0.602348993f, -0.999992846f, -0.000000097f, 0.729937171f, 0.000005158f, 0.949964440f, 3);
        add_motor_raw_6dof(AP_MOTORS_MOT_4, 0.602344787f, -0.999997372f, -0.000000007f, 0.729932880f, -0.000005055f, -0.949957666f, 4);
        add_motor_raw_6dof(AP_MOTORS_MOT_5, 1.000000000f, 0.000002181f, -1.000000000f, -0.000012390f, 0.999999362f, -0.211149706f, 5);
        add_motor_raw_6dof(AP_MOTORS_MOT_6, -1.000000000f, -0.000002181f, 1.000000000f, 0.000003403f, 1.000000000f, 0.211149706f, 6);
        break;
