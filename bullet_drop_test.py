import math
import numpy as np

def find_zero_angle(
    initial_velocity,     # fps
    ballistic_coef,       
    zero_range,          # yards
    sight_height,        # inches
    drag_function="G1"
):
    """
    Find the initial angle needed to zero the rifle at the specified range.
    Uses binary search to find the correct angle.
    """
    # Convert units
    sight_height = sight_height / 12  # convert to feet
    zero_range = zero_range * 3       # convert to feet
    
    # Constants
    GRAVITY = 32.174      # ft/s²
    AIR_DENSITY = 0.0023769  # lb/ft³
    
    def calculate_drag_coefficient(velocity, drag_model="G1"):
        mach = velocity / 1116.4
        if drag_model == "G1":
            if mach < 0.7:
                return 0.2
            elif mach < 1.2:
                return 0.25 + (mach - 0.7) * 0.5
            else:
                return 0.52
        else:  # G7
            if mach < 0.7:
                return 0.1
            elif mach < 1.2:
                return 0.15 + (mach - 0.7) * 0.3
            else:
                return 0.3

    def simulate_to_zero(angle):
        dt = 0.001
        x = 0.0
        y = sight_height
        vx = initial_velocity * math.cos(angle)
        vy = initial_velocity * math.sin(angle)
        
        while x <= zero_range:
            v = math.sqrt(vx**2 + vy**2)
            cd = calculate_drag_coefficient(v, drag_function)
            drag = (AIR_DENSITY * v**2 * cd) / (ballistic_coef * 2)
            
            drag_x = drag * vx / v if v > 0 else 0
            drag_y = drag * vy / v if v > 0 else 0
            
            vx = vx - (drag_x * dt)
            vy = vy - (GRAVITY + drag_y) * dt
            
            x = x + vx * dt
            y = y + vy * dt
            
            if x >= zero_range:
                return y
        
        return y

    # Binary search for the correct angle
    angle_low = -0.1  # radians
    angle_high = 0.1  # radians
    target_height = sight_height  # at zero range, we want to hit the sight line
    
    for _ in range(50):  # usually converges within 20 iterations
        angle_mid = (angle_low + angle_high) / 2
        height = simulate_to_zero(angle_mid)
        
        if abs(height - target_height) < 0.0001:  # feet
            return angle_mid
        elif height > target_height:
            angle_high = angle_mid
        else:
            angle_low = angle_mid
            
    return (angle_low + angle_high) / 2

def calculate_trajectory(
    initial_velocity,     # fps
    ballistic_coef,       
    zero_range,          # yards
    target_range,        # yards
    sight_height,        # inches
    drag_function="G1"
):
    """
    Calculate bullet trajectory with proper zeroing.
    """
    # Find the initial angle needed for zeroing
    initial_angle = find_zero_angle(
        initial_velocity,
        ballistic_coef,
        zero_range,
        sight_height,
        drag_function
    )
    
    # Constants
    GRAVITY = 32.174
    AIR_DENSITY = 0.0023769
    
    # Convert inputs to feet
    sight_height = sight_height / 12
    target_range = target_range * 3
    
    def calculate_drag_coefficient(velocity, drag_model="G1"):
        mach = velocity / 1116.4
        if drag_model == "G1":
            if mach < 0.7:
                return 0.2
            elif mach < 1.2:
                return 0.25 + (mach - 0.7) * 0.5
            else:
                return 0.52
        else:  # G7
            if mach < 0.7:
                return 0.1
            elif mach < 1.2:
                return 0.15 + (mach - 0.7) * 0.3
            else:
                return 0.3
    
    # Initial conditions with proper angle
    x = 0.0
    y = sight_height
    vx = initial_velocity * math.cos(initial_angle)
    vy = initial_velocity * math.sin(initial_angle)
    
    dt = 0.001
    positions = []
    
    while x <= target_range:
        # Calculate relative height to line of sight
        sight_line = sight_height  # straight line from sight to target
        
        v = math.sqrt(vx**2 + vy**2)
        cd = calculate_drag_coefficient(v, drag_function)
        drag = (AIR_DENSITY * v**2 * cd) / (ballistic_coef * 2)
        
        drag_x = drag * vx / v if v > 0 else 0
        drag_y = drag * vy / v if v > 0 else 0
        
        vx = vx - (drag_x * dt)
        vy = vy - (GRAVITY + drag_y) * dt
        
        x = x + vx * dt
        y = y + vy * dt
        
        # Store position relative to sight line
        drop = y - sight_line
        positions.append((x / 3, drop * 12))  # convert to yards and inches
    
    return {
        'range_yards': target_range / 3,
        'drop_inches': positions[-1][1],
        'trajectory': positions
    }

def print_trajectory_example():
    params = {
        'initial_velocity': 2750,    # fps
        'ballistic_coef': 0.485,     # G1 BC
        'zero_range': 100,           # 100 yard zero
        'target_range': 500,         # max range to calculate
        'sight_height': 1.5,         # 1.5 inch sight height
        'drag_function': "G1"
    }
    
    result = calculate_trajectory(**params)
    
    print("\nTrajectory Table:")
    print("Range (yards) | Drop (inches)")
    print("-" * 30)
    for range_yards, drop_inches in result['trajectory']:
        print(f"{range_yards:12.0f} | {drop_inches:12.2f}")

if __name__ == "__main__":
    print_trajectory_example()