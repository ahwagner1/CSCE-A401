import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import os


class ScopeAdjustmentApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Scope Adjustment Calculator")
        self.image_path = None
        self.image = None
        self.shot_coordinates = []
        self.target_center = None  # Store custom target center coordinates
        self.marking_mode = tk.StringVar(value="shots")  # Track current marking mode
        self.target_width = tk.StringVar()
        self.target_height = tk.StringVar()
        self.target_distance = tk.StringVar()
        self.adjustment_type = tk.StringVar(value="MOA")
        
        # Bullet variables
        self.bullet_manufacturer = tk.StringVar()
        self.bullet_model = tk.StringVar()
        self.bullet_weight = tk.StringVar()

        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.expanduser("~"), "scope_adjustment_data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.setup_database()
        self.current_user = None
        self.create_notebook()
        
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
                bullet_manufacturer TEXT,
                bullet_model TEXT,
                bullet_weight INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def create_notebook(self):
        """Create the notebook to hold the main and history tabs"""
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill='both', expand=True)
        
        # Main tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Adjustment Calculator')
        
        # History tab
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text='History')
        
        # Create the widgets in each tab
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
        
        # Create the canvas for displaying the image and marking shots/center
        self.canvas = tk.Canvas(image_frame, width=500, height=500, bg='lightgray')
        self.canvas.pack(padx=5, pady=5)
        
        # Add a label with instructions
        ttk.Label(image_frame, 
                text="Upload a target image and use 'Mark Shots' to indicate shot locations",
                wraplength=400).pack(pady=5)

    def create_control_buttons(self, parent_frame):
        """Create the frame containing all control buttons"""

        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(padx=5, pady=5, fill='x')
        
        # Control buttons frame
        measurement_frame = ttk.LabelFrame(control_frame, text="Measurement Controls")
        measurement_frame.pack(padx=5, pady=5, fill='x')
        
        # Create a frame for the adjustment type buttons
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
        
        # Add marking mode selection
        marking_mode_frame = ttk.Frame(measurement_frame)
        marking_mode_frame.pack(pady=5)
        ttk.Label(marking_mode_frame, text="Target Center:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(marking_mode_frame,
                       text="Use Image Center",
                       variable=self.marking_mode,
                       value="default",
                       command=self.update_center_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(marking_mode_frame,
                       text="Mark Center",
                       variable=self.marking_mode,
                       value="center",
                       command=self.update_center_display).pack(side=tk.LEFT, padx=5)
        
        # Create a frame for the action buttons
        button_frame = ttk.Frame(measurement_frame)
        button_frame.pack(pady=5)
        
        # Add the action buttons
        self.mark_center_button = ttk.Button(button_frame,
                                           text="Mark Center",
                                           command=self.start_marking_center)
        self.mark_center_button.pack(side=tk.LEFT, padx=5)
        
        self.mark_shots_button = ttk.Button(button_frame,
                                          text="Mark Shots",
                                          command=self.start_marking_shots)
        self.mark_shots_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame,
                                     text="Clear All",
                                     command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.calculate_button = ttk.Button(button_frame,
                                         text="Calculate Adjustment",
                                         command=self.calculate_adjustment)
        self.calculate_button.pack(side=tk.LEFT, padx=5)

    def update_center_display(self):
        """Update the display to show or hide the center point based on mode"""

        if self.image:
            self.redraw_canvas()
            if self.marking_mode.get() == "default":
                center_x, center_y = 250, 250
                self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, 
                                     fill="blue", tags="center")
                self.target_center = (center_x, center_y)
            elif self.target_center:
                x, y = self.target_center
                self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue", tags="center")

    def start_marking_center(self):
        """Enable center marking mode"""

        if not self.image:
            messagebox.showerror("Error", "Please upload an image first")
            return
        
        self.marking_mode.set("center")
        self.canvas.bind("<Button-1>", self.mark_center)
        messagebox.showinfo("Mark Center", "Click on the image to mark the center of the target")

    def mark_center(self, event):
        """Handle marking the center point"""

        self.target_center = (event.x, event.y)
        self.redraw_canvas()
        self.canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, 
                              fill="blue", tags="center")
        self.canvas.unbind("<Button-1>")
        messagebox.showinfo("Center Marked", "Target center has been marked")

    def clear_all(self):
        """Clear all markings from the canvas"""

        self.shot_coordinates = []
        self.target_center = None
        if self.marking_mode.get() == "default":
            self.target_center = (250, 250)
        self.redraw_canvas()
        self.update_center_display()

    def create_main_widgets(self):
        """Create all widgets """

        # Create notebook for sub-tabs in main tab
        main_notebook = ttk.Notebook(self.main_frame)
        main_notebook.pack(fill='both', expand=True)
        
        # Target tab
        target_tab = ttk.Frame(main_notebook)
        main_notebook.add(target_tab, text='Target')
        
        # Bullet information tab
        bullet_information_tab = ttk.Frame(main_notebook)
        main_notebook.add(bullet_information_tab, text='Bullet Information')
        
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
        ballistics_frame = ttk.LabelFrame(bullet_information_tab, text="Bullet Information")
        ballistics_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Label(ballistics_frame, text="Bullet Manufacturer:").pack()
        ttk.Entry(ballistics_frame, textvariable=self.bullet_manufacturer).pack()
        
        ttk.Label(ballistics_frame, text="Bullet Model:").pack()
        ttk.Entry(ballistics_frame, textvariable=self.bullet_model).pack()
        
        ttk.Label(ballistics_frame, text="Bullet Grain:").pack()
        ttk.Entry(ballistics_frame, textvariable=self.bullet_weight).pack()
        
        # Rest of the widgets...
        self.create_image_frame(target_tab)
        self.create_control_buttons(target_tab)

    def redraw_canvas(self):
        """Redraw the canvas with the current image and all markings"""

        self.canvas.delete("all")
        if self.image:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            for x, y in self.shot_coordinates:
                self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")
    
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
        """Create the widgets for the history tab"""

        # Create frame for history controls
        control_frame = ttk.Frame(self.history_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Add refresh button
        ttk.Button(control_frame, text="Refresh History", command=self.load_history).pack(side=tk.LEFT, padx=5)
        
        # Add clear history button
        ttk.Button(control_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # Create Treeview for history
        columns = ('Date', 'Distance', 'Horizontal', 'Vertical', 'Type', 'Bullet Manufacturer', 'Bullet Model', 'Bullet Grain')
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
        """Handles the image uploading to the app"""

        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.image = Image.open(self.image_path)
            self.image = self.image.resize((500, 500))
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
    
    def start_marking_shots(self):
        """This functions binds the left mouce click to the mark_shot function defined below"""

        self.canvas.bind("<Button-1>", self.mark_shot)
        messagebox.showinfo("Mark Shots", "Click on the image to mark each shot. Press 'Calculate Adjustment' when done.")
    
    def mark_shot(self, event):
        """This function will keep track of all the coordinates that a user marks"""

        x, y = event.x, event.y
        self.shot_coordinates.append((x, y))
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")

    def calculate_adjustment(self):
        """The math for figuring out the adjustments needed to sight in the rifle"""

        if not self.shot_coordinates:
            messagebox.showerror("Error", "No shots marked!")
            return
        
        try:
            target_width = float(self.target_width.get())
            target_height = float(self.target_height.get())
            target_distance = float(self.target_distance.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all fields")
            return
        
        # Get center coordinates based on mode
        if self.marking_mode.get() == "default":
            center_x, center_y = 250, 250
        else:
            if not self.target_center:
                messagebox.showerror("Error", "Please mark the target center first")
                return
            center_x, center_y = self.target_center
        
        # Calculate average position of shots
        avg_x = sum(x for x, _ in self.shot_coordinates) / len(self.shot_coordinates)
        avg_y = sum(y for _, y in self.shot_coordinates) / len(self.shot_coordinates)
        
        # Calculate difference from center in inches
        diff_x = center_x - avg_x
        diff_y = center_y - avg_y
        
        adjustment_x = (diff_x / 500) * target_width
        adjustment_y = (-diff_y / 500) * target_height
        
        # Convert to MOA or MIL based on selection
        if self.adjustment_type.get() == "MOA":
            adjustment_x_angular = (adjustment_x / (target_distance / 100)) / 1.047
            adjustment_y_angular = (adjustment_y / (target_distance / 100)) / 1.047
            unit = "MOA"
        else:
            adjustment_x_angular = (adjustment_x / (target_distance / 100)) / 3.6
            adjustment_y_angular = (adjustment_y / (target_distance / 100)) / 3.6
            unit = "MIL"
        
        # Save to history
        self.save_calibration(target_distance, adjustment_x_angular, adjustment_y_angular, unit,
                            self.bullet_manufacturer.get(), self.bullet_model.get(), 
                            int(self.bullet_weight.get()) if self.bullet_weight.get() else 0)
        
        # Show results
        messagebox.showinfo("Adjustment Needed", 
                          f"Horizontal: {adjustment_x_angular:.2f} {unit}\n"
                          f"Vertical: {adjustment_y_angular:.2f} {unit}\n"
                          f"At {target_distance} yards")

    def save_calibration(self, distance, horizontal, vertical, adjustment_type, bullet_manufacturer, bullet_model, bullet_weight):
        """Save calibration data to database"""

        user_id = self.current_user if self.current_user else 1  # Default to user 1 if no user system
        self.cursor.execute('''
            INSERT INTO calibration_history 
            (user_id, date, target_distance, horizontal_adjustment, vertical_adjustment,
            adjustment_type, bullet_manufacturer, bullet_model, bullet_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, datetime.now(), distance, horizontal, vertical, adjustment_type, bullet_manufacturer, bullet_model, bullet_weight))
        self.conn.commit()
        self.load_history()

    def load_history(self):
        """Load and display calibration history"""
        
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load history from database
        self.cursor.execute('''
            SELECT date, target_distance, horizontal_adjustment, vertical_adjustment, adjustment_type,
                    bullet_manufacturer, bullet_model, bullet_weight
            FROM calibration_history
            ORDER BY date DESC
            LIMIT 50
        ''')
        
        for row in self.cursor.fetchall():
            date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
            self.history_tree.insert('', 'end', values=(date, f"{row[1]} yards", 
                                                      f"{row[2]:.2f} {row[4]}", 
                                                      f"{row[3]:.2f} {row[4]}", 
                                                      row[4], row[5], row[6], row[7]))

if __name__ == "__main__":
    root = tk.Tk()
    app = ScopeAdjustmentApp(root)
    root.mainloop()