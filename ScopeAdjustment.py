import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

class ScopeAdjustmentApp:
    """
    This houses the core logic for the rough draft of the scope adjustment software
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Scope Adjustment Calculator")
        self.image_path = None
        self.image = None
        self.shot_coordinates = []
        self.target_width = tk.StringVar()
        self.target_height = tk.StringVar()
        self.create_widgets()
        
    def create_widgets(self):
        """
        This function creates all the necessary tkinter widgets for the software
        """
        # upload button
        self.upload_button = tk.Button(self.master, text="Upload Image", command=self.upload_image)
        self.upload_button.pack()
        
        # target dimensions inputs
        tk.Label(self.master, text="Target Width (inches):").pack()
        tk.Entry(self.master, textvariable=self.target_width).pack()
        tk.Label(self.master, text="Target Height (inches):").pack()
        tk.Entry(self.master, textvariable=self.target_height).pack()
        
        # create canvas to display image
        self.canvas = tk.Canvas(self.master, width=500, height=500)
        self.canvas.pack()
        
        # button to enter shot selection mode
        self.mark_shots_button = tk.Button(self.master, text="Mark Shots", command=self.start_marking_shots)
        self.mark_shots_button.pack()
        
        # button to calculate the distance from center
        self.calculate_button = tk.Button(self.master, text="Calculate Adjustment", command=self.calculate_adjustment)
        self.calculate_button.pack()
        
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
        """
        This function will find the average x and y coordinates of all the marked shots, and then calculate the distance from center that the shot grouping was
        """
        if not self.shot_coordinates:
            messagebox.showerror("Error", "No shots marked!")
            return
        
        center_x, center_y = 250, 250
        
        # calculate the average position of the shots
        avg_x = sum(x for x, _ in self.shot_coordinates) / len(self.shot_coordinates)
        avg_y = sum(y for _, y in self.shot_coordinates) / len(self.shot_coordinates)
        
        # calculate the difference between the average shot position and the center of the target
        diff_x = center_x - avg_x
        diff_y = center_y - avg_y
        
        # convert from pixels coordinates back to inches
        target_width = float(self.target_width.get())
        target_height = float(self.target_height.get())
        
        adjustment_x = (diff_x / 500) * target_width
        adjustment_y = (diff_y / 500) * target_height
        
        messagebox.showinfo("Adjustment Needed", 
                            f"Horizontal: {adjustment_x:.2f} inches\n"
                            f"Vertical: {adjustment_y:.2f} inches")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScopeAdjustmentApp(root)
    root.mainloop()