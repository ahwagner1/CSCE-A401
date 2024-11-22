import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import numpy as np
import sqlite3
from datetime import datetime
import os

class BallisticCalculator:
    """Separate class to handle ballistic calculations"""
    
    def __init__(self):
        self.GRAVITY = 32.174  # ft/s²
        self.YARDS_TO_FEET = 3
    
    def calculate_drop(self, distance_yards, muzzle_velocity_fps, ballistic_coefficient, sight_height_inches=1.5):
        """
        Calculate bullet drop at given distance
        Returns drop in inches
        """
        # Convert distance to feet
        distance_feet = distance_yards * self.YARDS_TO_FEET
        time_of_flight = distance_feet / muzzle_velocity_fps
        
        # Basic drop calculation (gravity only)
        drop_feet = 0.5 * self.GRAVITY * time_of_flight**2
        
        # Convert to inches and adjust for sight height
        drop_inches = drop_feet * 12
        
        # Apply very basic air resistance using BC
        # This is a simplified model - real ballistics are more complex
        air_resistance_factor = 1 - ballistic_coefficient
        actual_drop = drop_inches * (1 + air_resistance_factor)
        
        # Adjust for sight height
        actual_drop -= sight_height_inches
        
        return actual_drop

class ScopeAdjustmentApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Scope Adjustment Calculator")
        self.image_path = None
        self.image = None
        self.shot_coordinates = []
        self.target_width = tk.StringVar()
        self.target_height = tk.StringVar()
        self.target_distance = tk.StringVar()
        self.adjustment_type = tk.StringVar(value="MOA")
        
        # Ballistic variables
        self.muzzle_velocity = tk.StringVar(value="2700")  # Default 2700 fps
        self.ballistic_coefficient = tk.StringVar(value="0.5")  # Default BC
        self.sight_height = tk.StringVar(value="1.5")  # Default 1.5 inches
        
        self.ballistic_calculator = BallisticCalculator()

        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.expanduser("~"), "scope_adjustment_data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.setup_database()
        self.current_user = None
        self.create_widgets()
        
    def setup_database(self):
        """Initialize SQLite database for storing calibration history and user profiles"""
        # Store database in user's home directory
        db_path = os.path.join(self.data_dir, 'scope_adjustments.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                created_date TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS calibration_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TIMESTAMP,
                target_distance FLOAT,
                horizontal_adjustment FLOAT,
                vertical_adjustment FLOAT,
                adjustment_type TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill='both', expand=True)
        
        # Main tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Adjustment Calculator')
        
        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text='History')
        
        # Main tab widgets
        self.create_main_widgets()
        self.create_history_widgets()
    
    def create_image_frame(self, parent_frame):
        """Create the frame that will hold the target image and canvas"""
        # Image handling frame
        image_frame = ttk.LabelFrame(parent_frame, text="Target Image")
        image_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Create the upload button
        self.upload_button = ttk.Button(image_frame, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(pady=5)
        
        # Create the canvas for displaying the image and marking shots
        self.canvas = tk.Canvas(image_frame, width=500, height=500, bg='lightgray')
        self.canvas.pack(padx=5, pady=5)
        
        # Add a label with instructions
        ttk.Label(image_frame, 
                text="Upload a target image and use 'Mark Shots' to indicate shot locations",
                wraplength=400).pack(pady=5)

    def create_control_buttons(self, parent_frame):
        """Create the frame containing all control buttons"""
        # Control buttons frame
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(padx=5, pady=5, fill='x')
        
        # Button frame for measurement controls
        measurement_frame = ttk.LabelFrame(control_frame, text="Measurement Controls")
        measurement_frame.pack(padx=5, pady=5, fill='x')
        
        # Create a frame for the adjustment type radio buttons
        adjustment_type_frame = ttk.Frame(measurement_frame)
        adjustment_type_frame.pack(pady=5)
        
        # Add radio buttons for MOA/MIL selection
        ttk.Label(adjustment_type_frame, text="Adjustment Type:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(adjustment_type_frame, 
                        text="MOA", 
                        variable=self.adjustment_type,
                        value="MOA").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(adjustment_type_frame,
                        text="MIL",
                        variable=self.adjustment_type,
                        value="MIL").pack(side=tk.LEFT, padx=5)
        
        # Create a frame for the action buttons
        button_frame = ttk.Frame(measurement_frame)
        button_frame.pack(pady=5)
        
        # Add the action buttons
        self.mark_shots_button = ttk.Button(button_frame,
                                        text="Mark Shots",
                                        command=self.start_marking_shots)
        self.mark_shots_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_shots_button = ttk.Button(button_frame,
                                        text="Clear Shots",
                                        command=self.clear_shots)
        self.clear_shots_button.pack(side=tk.LEFT, padx=5)
        
        self.calculate_button = ttk.Button(button_frame,
                                        text="Calculate Adjustment",
                                        command=self.calculate_adjustment)
        self.calculate_button.pack(side=tk.LEFT, padx=5)

    def create_main_widgets(self):
        # Create notebook for sub-tabs in main tab
        main_notebook = ttk.Notebook(self.main_frame)
        main_notebook.pack(fill='both', expand=True)
        
        # Target tab
        target_tab = ttk.Frame(main_notebook)
        main_notebook.add(target_tab, text='Target')
        
        # Ballistics tab
        ballistics_tab = ttk.Frame(main_notebook)
        main_notebook.add(ballistics_tab, text='Ballistics')
        
        # Target information frame
        target_frame = ttk.LabelFrame(target_tab, text="Target Information")
        target_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Label(target_frame, text="Target Width (inches):").pack()
        ttk.Entry(target_frame, textvariable=self.target_width).pack()
        
        ttk.Label(target_frame, text="Target Height (inches):").pack()
        ttk.Entry(target_frame, textvariable=self.target_height).pack()
        
        ttk.Label(target_frame, text="Target Distance (yards):").pack()
        ttk.Entry(target_frame, textvariable=self.target_distance).pack()
        
        # Ballistics information frame
        ballistics_frame = ttk.LabelFrame(ballistics_tab, text="Ballistic Information")
        ballistics_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Label(ballistics_frame, text="Muzzle Velocity (fps):").pack()
        ttk.Entry(ballistics_frame, textvariable=self.muzzle_velocity).pack()
        
        ttk.Label(ballistics_frame, text="Ballistic Coefficient:").pack()
        ttk.Entry(ballistics_frame, textvariable=self.ballistic_coefficient).pack()
        
        ttk.Label(ballistics_frame, text="Sight Height (inches):").pack()
        ttk.Entry(ballistics_frame, textvariable=self.sight_height).pack()
        
        # Rest of the widgets...
        self.create_image_frame(target_tab)
        self.create_control_buttons(target_tab)
    
    def clear_shots(self):
        """Clear all marked shots from the canvas and reset shot coordinates"""
        if self.image:
            # Redraw the image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            # Clear the shot coordinates
            self.shot_coordinates = []
            messagebox.showinfo("Clear Shots", "All shots have been cleared")
        else:
            messagebox.showinfo("Clear Shots", "No image loaded")

    def create_history_widgets(self):
        # Create frame for history controls
        control_frame = ttk.Frame(self.history_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Add refresh button
        ttk.Button(control_frame, text="Refresh History", command=self.load_history).pack(side=tk.LEFT, padx=5)
        
        # Add clear history button
        ttk.Button(control_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # Create Treeview for history
        columns = ('Date', 'Distance', 'Horizontal', 'Vertical', 'Type')
        self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        self.history_tree.pack(padx=5, pady=5, fill='both', expand=True)

    def clear_history(self):
        """Clear all history from the database"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history? This cannot be undone."):
            self.cursor.execute('DELETE FROM calibration_history')
            self.conn.commit()
            self.load_history()
            messagebox.showinfo("Clear History", "History has been cleared")

    def __del__(self):
        """Ensure database connection is closed when the app is closed"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def upload_image(self):
        """
        This function opens a popup that allows a uder to select an image
        Once the image is selected, it gets resized to 500 x 500
        This might cause problems when trying to calculate the adjustments on a rectangular target
        """

        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.image = Image.open(self.image_path)
            self.image = self.image.resize((500, 500))
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
    
    def start_marking_shots(self):
        """
        This functions binds the left mouce click to the mark_shot function defined below
        Once this mode is enbaled, it doesn't turn off which needs to be fixed
        """
        self.canvas.bind("<Button-1>", self.mark_shot)
        messagebox.showinfo("Mark Shots", "Click on the image to mark each shot. Press 'Calculate Adjustment' when done.")
    
    def mark_shot(self, event):
        """
        This function will keep track of all the coordinates that a user marks
        """
        x, y = event.x, event.y
        self.shot_coordinates.append((x, y))
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")

    def calculate_adjustment(self):
        if not self.shot_coordinates:
            messagebox.showerror("Error", "No shots marked!")
            return
        
        try:
            target_width = float(self.target_width.get())
            target_height = float(self.target_height.get())
            target_distance = float(self.target_distance.get())
            muzzle_velocity = float(self.muzzle_velocity.get())
            ballistic_coefficient = float(self.ballistic_coefficient.get())
            sight_height = float(self.sight_height.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all fields")
            return
        
        # Calculate bullet drop
        bullet_drop = self.ballistic_calculator.calculate_drop(
            target_distance, 
            muzzle_velocity,
            ballistic_coefficient,
            sight_height
        )
        
        center_x, center_y = 250, 250
        
        # Calculate average position of shots
        avg_x = sum(x for x, _ in self.shot_coordinates) / len(self.shot_coordinates)
        avg_y = sum(y for _, y in self.shot_coordinates) / len(self.shot_coordinates)
        
        # Calculate difference from center in inches
        diff_x = center_x - avg_x
        diff_y = center_y - avg_y
        
        adjustment_x = (diff_x / 500) * target_width
        adjustment_y = (diff_y / 500) * target_height
        
        # Add bullet drop to vertical adjustment
        adjustment_y += bullet_drop
        
        # Convert to MOA or MIL based on selection
        if self.adjustment_type.get() == "MOA":
            # MOA conversion: 1 MOA = 1.047 inches at 100 yards
            adjustment_x_angular = (adjustment_x / (target_distance / 100)) / 1.047
            adjustment_y_angular = (adjustment_y / (target_distance / 100)) / 1.047
            unit = "MOA"
        else:
            # MIL conversion: 1 MIL = 3.6 inches at 100 yards
            adjustment_x_angular = (adjustment_x / (target_distance / 100)) / 3.6
            adjustment_y_angular = (adjustment_y / (target_distance / 100)) / 3.6
            unit = "MIL"
        
        # Save to history
        self.save_calibration(target_distance, adjustment_x_angular, adjustment_y_angular, unit)
        
        # Show results
        messagebox.showinfo("Adjustment Needed", 
                          f"Horizontal: {adjustment_x_angular:.2f} {unit}\n"
                          f"Vertical: {adjustment_y_angular:.2f} {unit}\n"
                          f"Bullet Drop: {bullet_drop:.2f} inches\n"
                          f"At {target_distance} yards")

    def save_calibration(self, distance, horizontal, vertical, adjustment_type):
        """Save calibration data to database"""
        user_id = self.current_user if self.current_user else 1  # Default to user 1 if no user system
        self.cursor.execute('''
            INSERT INTO calibration_history 
            (user_id, date, target_distance, horizontal_adjustment, vertical_adjustment, adjustment_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, datetime.now(), distance, horizontal, vertical, adjustment_type))
        self.conn.commit()
        self.load_history()

    def load_history(self):
        """Load and display calibration history"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load history from database
        self.cursor.execute('''
            SELECT date, target_distance, horizontal_adjustment, vertical_adjustment, adjustment_type
            FROM calibration_history
            ORDER BY date DESC
            LIMIT 50
        ''')
        
        for row in self.cursor.fetchall():
            date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
            self.history_tree.insert('', 'end', values=(date, f"{row[1]} yards", 
                                                      f"{row[2]:.2f} {row[4]}", 
                                                      f"{row[3]:.2f} {row[4]}", 
                                                      row[4]))

if __name__ == "__main__":
    root = tk.Tk()
    app = ScopeAdjustmentApp(root)
    root.mainloop()