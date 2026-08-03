import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from std_srvs.srv import Trigger
from rclpy.action import ActionServer # استدعاء مكتبة الأكشن
from fake_depth_interfaces.action import Dive # استدعاء الأكشن بتاعنا
import math
import time

class FakeDepthPublisher(Node):
    def __init__(self):
        super().__init__('fake_depth_publisher')
        
        # 1. البابلشر (بتاع بروجكت A)
        self.publisher_ = self.create_publisher(Float32, 'depth', 10)
        
        # 2. السيرفيس (بتاعة التصفير)
        self.srv = self.create_service(Trigger, 'calibrate_depth', self.calibrate_callback)
        
        # 3. الأكشن سيرفر الجديد (بتاع الغطس)
        self._action_server = ActionServer(
            self,
            Dive,
            'dive_action',
            self.execute_callback
        )
        
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.start_time = time.time()
        
        # متغيرات عشان نحسب بيها العمق
        self.current_base_depth = 5.0 # العمق الأساسي اللي بنبدأ منه
        self.depth_offset = 0.0 # قيمة التصفير
        self.is_diving = False # متغير بيعرفنا إحنا بنغطس دلوقتي ولا لأ
        
        self.get_logger().info('السنسور شغال، والسيرفيس والأكشن جاهزين!')

    # دالة التصفير
    def calibrate_callback(self, request, response):
        current_time = time.time() - self.start_time
        wave = 5.0 * math.sin(current_time)
        self.depth_offset = self.current_base_depth + wave
        
        response.success = True
        response.message = 'تم تصفير الحساس!'
        self.get_logger().info('تم عمل Calibration وتصفير الحساس.')
        return response

    # دالة الغطس (الأكشن)
    def execute_callback(self, goal_handle):
        target = goal_handle.request.target_depth
        self.get_logger().info(f'جالي أمر غطس لعمق: {target} متر...')
        
        self.is_diving = True
        feedback_msg = Dive.Feedback()
        
        # بنحدد هننزل لتحت ولا هنطلع لفوق بناءً على الهدف
        step = 1.0 if target > self.current_base_depth else -1.0
        
        # بنعمل لوب يزود العمق خطوة بخطوة لحد ما نقرب للهدف
        while abs(target - self.current_base_depth) > 0.5:
            self.current_base_depth += step
            
            # بنحسب العمق الحالي ونبعته كـ Feedback
            feedback_msg.current_depth = self.current_base_depth - self.depth_offset
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'بنغطس... العمق الحالي: {feedback_msg.current_depth:.2f} متر')
            
            time.sleep(1.0) # بنستنى ثانية بين كل متر عشان نحاكي الغطس
            
        # وصلنا للهدف
        self.current_base_depth = target
        self.is_diving = False
        
        goal_handle.succeed()
        result = Dive.Result()
        result.success = True
        self.get_logger().info('وصلنا للعمق المطلوب بنجاح!')
        return result

    # دالة البابلشر العادية
    def timer_callback(self):
        # مش هننشر موجة عشوائية طول ما الغواصة بتنفذ أمر غطس
        if not self.is_diving:
            msg = Float32()
            current_time = time.time() - self.start_time
            wave = 5.0 * math.sin(current_time)
            
            msg.data = (self.current_base_depth + wave) - self.depth_offset
            self.publisher_.publish(msg)
            self.get_logger().info(f'العمق الحالي: {msg.data:.2f} متر')

def main(args=None):
    rclpy.init(args=args)
    node = FakeDepthPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
