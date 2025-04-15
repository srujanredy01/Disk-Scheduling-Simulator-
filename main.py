import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from threading import Thread
import queue

class DiskSchedulingSimulator:
    def __init__(self, root):  # Fixed typo: _init_ to __init__
        self.root = root
        self.root.title("Disk Scheduling Simulator")
        self.root.configure(bg="#f4f6f8")
        self.root.state('zoomed')  # Fullscreen on launch

        # Initialize variables
        self.requests = []
        self.head = 0
        self.disk_size = 200
        self.direction = "outward"
        self.animation_queue = queue.Queue()
        self.animation_thread = None
        self.animation_running = False
        self.paused = False
        self.current_sequence = []
        self.current_seek_time = 0

        # Build the GUI
        self.build_gui()
        self.configure_status_text()  # Moved configuration to initialization

    def build_gui(self):
        # Configure styles
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 11), background="#f4f6f8")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TCombobox", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))

        # Create frames
        self.left_frame = tk.Frame(self.root, bg="#f4f6f8", padx=20, pady=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = tk.Frame(self.root, bg="#f4f6f8", padx=20, pady=20)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add title
        ttk.Label(self.left_frame, text="Disk Scheduling Simulator", 
                 style="Title.TLabel").pack(pady=(0, 20), anchor="w")

        # Build input and plot areas
        self.build_inputs()
        self.build_plot_area()

    def build_inputs(self):
        # Disk requests input
        ttk.Label(self.left_frame, text="Disk Requests (comma-separated):").pack(anchor="w", pady=5)
        self.requests_entry = ttk.Entry(self.left_frame, width=30)
        self.requests_entry.insert(0, "50, 82, 120, 30, 140, 10, 180, 65")
        self.requests_entry.pack(pady=5)
        self.requests_entry.bind("<KeyRelease>", self.on_input_change)

        # Head position input
        ttk.Label(self.left_frame, text="Initial Head Position:").pack(anchor="w", pady=5)
        self.head_entry = ttk.Entry(self.left_frame, width=10)
        self.head_entry.insert(0, "50")
        self.head_entry.pack(pady=5)
        self.head_entry.bind("<KeyRelease>", self.on_input_change)

        # Disk size input
        ttk.Label(self.left_frame, text="Disk Size:").pack(anchor="w", pady=5)
        self.disk_size_entry = ttk.Entry(self.left_frame, width=10)
        self.disk_size_entry.insert(0, "200")
        self.disk_size_entry.pack(pady=5)
        self.disk_size_entry.bind("<KeyRelease>", self.on_input_change)

        # Algorithm selection
        ttk.Label(self.left_frame, text="Algorithm:").pack(anchor="w", pady=5)
        self.algo_var = tk.StringVar(value="FCFS")
        algo_menu = ttk.Combobox(self.left_frame, textvariable=self.algo_var, 
                                values=["FCFS", "SSTF", "SCAN", "C-SCAN"], 
                                state="readonly", width=15)
        algo_menu.pack(pady=5)
        algo_menu.bind("<<ComboboxSelected>>", self.on_input_change)

        # Direction selection
        ttk.Label(self.left_frame, text="Direction (SCAN/C-SCAN):").pack(anchor="w", pady=5)
        self.dir_var = tk.StringVar(value="outward")
        dir_menu = ttk.Combobox(self.left_frame, textvariable=self.dir_var, 
                               values=["outward", "inward"], state="readonly", width=15)
        dir_menu.pack(pady=5)
        dir_menu.bind("<<ComboboxSelected>>", self.on_input_change)

        # Simulation button
        ttk.Button(self.left_frame, text="Simulate", command=self.simulate).pack(pady=(15, 5))

        # Animation control buttons
        button_frame = tk.Frame(self.left_frame, bg="#f4f6f8")
        button_frame.pack(pady=5)

        self.play_button = ttk.Button(button_frame, text="▶ Play", command=self.play_simulation)
        self.play_button.grid(row=0, column=0, padx=5)

        self.pause_button = ttk.Button(button_frame, text="⏸ Pause", command=self.pause_simulation, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset)
        self.reset_button.grid(row=0, column=2, padx=5)

        # Metrics display
        self.metrics_frame = tk.LabelFrame(self.left_frame, text="Performance Metrics", 
                                         bg="#f4f6f8", fg="#333", font=("Segoe UI", 10, "bold"))
        self.metrics_frame.pack(pady=20, fill=tk.X)

        self.metrics_label = tk.Label(self.metrics_frame, text="", bg="#f4f6f8", 
                                    font=("Segoe UI", 10), justify="left", fg="#333")
        self.metrics_label.pack(pady=5, padx=5)

        # Status Screen with scrollbar
        status_frame = tk.Frame(self.left_frame)
        status_frame.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

        self.status_text = tk.Text(status_frame, height=15, width=40, bg="#ffffff", 
                                 fg="#2d3436", font=("Segoe UI", 10), wrap="word")
        self.status_scroll = tk.Scrollbar(status_frame, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=self.status_scroll.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.status_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Exit button
        exit_button = ttk.Button(self.left_frame, text="Exit", command=self.root.destroy)
        exit_button.pack(side=tk.BOTTOM, pady=(20, 0))

    def build_plot_area(self):
        # Create the plot area
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.fig.set_facecolor("#f9f9f8")
        self.ax.set_facecolor("#f9f9f8")
        
        # Initialize empty plot
        self.ax.set_ylim(-0.1, 0.1)
        self.ax.set_yticks([])
        self.ax.set_xlim(0, 200)
        self.ax.set_xlabel("Track Number")
        self.ax.set_title("Disk Scheduling Visualization")
        self.ax.grid(True, axis='x', linestyle='--')
        
        # Create canvas for embedding in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def log_status(self, message, is_error=False):
        """Log a message to the status screen with appropriate color."""
        # Insert the message
        self.status_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        # Apply error tag only to the current line if it's an error
        if is_error:
            current_line = self.status_text.index(tk.END).split('.')[0]  # Get the line number
            self.status_text.tag_add("error", f"{current_line}.0", f"{current_line}.0 lineend")
        self.status_text.see(tk.END)  # Auto-scroll to the latest message

    def on_input_change(self, event):
        """Handle changes in input fields and log them."""
        try:
            # Parse current input values
            requests_input = self.requests_entry.get()
            head = int(self.head_entry.get()) if self.head_entry.get().strip() else 0
            disk_size = int(self.disk_size_entry.get()) if self.disk_size_entry.get().strip() else 200
            algorithm = self.algo_var.get()
            direction = self.dir_var.get()

            # Log the changes
            self.log_status(f"Input updated - Requests: {requests_input}, Head: {head}, Disk Size: {disk_size}, "
                          f"Algorithm: {algorithm}, Direction: {direction}")
        except ValueError:
            # Log an error if conversion fails (e.g., non-integer input)
            self.log_status("Invalid input detected. Please enter valid numbers.", is_error=True)

    def validate_inputs(self):
        self.log_status("Validating inputs...")
        try:
            # Validate and parse inputs
            self.requests = [int(x.strip()) for x in self.requests_entry.get().split(",") if x.strip()]
            self.head = int(self.head_entry.get())
            self.disk_size = int(self.disk_size_entry.get())
            
            if not self.requests:
                raise ValueError("Please enter at least one disk request.")
                
            if not (0 <= self.head < self.disk_size):
                raise ValueError(f"Head position must be between 0 and {self.disk_size-1}.")
                
            # Check if any request exceeds disk size
            if any(req >= self.disk_size for req in self.requests):
                raise ValueError(f"Request(s) {', '.join(str(req) for req in self.requests if req >= self.disk_size)} exceed disk size of {self.disk_size}.")
                
            self.log_status(f"Inputs validated successfully: {len(self.requests)} requests, Head={self.head}, Disk Size={self.disk_size}")
            self.play_button.config(state=tk.NORMAL)  # Enable play button on valid input
            return True
            
        except ValueError as e:
            self.log_status(str(e), is_error=True)
            messagebox.showerror("Invalid Input", str(e))
            self.play_button.config(state=tk.DISABLED)  # Disable play button on invalid input
            return False

    def simulate(self):
        if not self.validate_inputs():
            return

        algo = self.algo_var.get()
        direction = self.dir_var.get()
        self.log_status(f"Starting simulation with {algo} algorithm, direction: {direction}")
        
        # Run the selected algorithm
        self.current_sequence, self.current_seek_time = self.run_algorithm(algo, direction)
        self.log_status(f"{algo}: Simulation completed. Final sequence: {self.current_sequence}, Total Seek Time: {self.current_seek_time}")
        
        # Calculate performance metrics
        avg_seek_time = self.current_seek_time / len(self.requests)
        throughput = len(self.requests) / (self.current_seek_time + 1e-6)  # Avoid division by zero
        
        # Update metrics display
        self.metrics_label.config(
            text=f"Total Seek Time: {self.current_seek_time}\n"
                 f"Average Seek Time: {avg_seek_time:.2f}\n"
                 f"Throughput: {throughput:.2f} req/unit time\n"
                 f"Total Requests: {len(self.requests)}"
        )
        
        # Prepare the full visualization
        self.update_plot(self.current_sequence, algo)

    def run_algorithm(self, algo, direction):
        req = self.requests.copy()
        head = self.head
        sequence = [head]
        seek = 0

        if algo == "FCFS":
            self.log_status("FCFS: Starting algorithm execution...")
            for r in req:
                seek += abs(head - r)
                head = r
                sequence.append(r)
                self.log_status(f"FCFS: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                
        elif algo == "SSTF":
            self.log_status("SSTF: Starting algorithm execution...")
            while req:
                closest = min(req, key=lambda x: abs(head - x))
                seek += abs(head - closest)
                head = closest
                sequence.append(closest)
                req.remove(closest)
                self.log_status(f"SSTF: Moving from {sequence[-2]} to {closest}, Seek increment: {abs(sequence[-2] - closest)}")
                
        elif algo == "SCAN":
            self.log_status(f"SCAN: Starting algorithm execution, direction: {direction}...")
            left = sorted([r for r in req if r < head])
            right = sorted([r for r in req if r >= head])
            
            if direction == "outward":
                for r in right:
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                if head != self.disk_size - 1:
                    seek += abs(head - (self.disk_size - 1))
                    head = self.disk_size - 1
                    sequence.append(head)
                    self.log_status(f"SCAN: Moving to end at {head}, Seek increment: {abs(sequence[-2] - head)}")
                for r in reversed(left):
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
            else:
                for r in reversed(left):
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                if head != 0:
                    seek += abs(head - 0)
                    head = 0
                    sequence.append(0)
                    self.log_status(f"SCAN: Moving to start at {head}, Seek increment: {abs(sequence[-2] - head)}")
                for r in right:
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                    
        elif algo == "C-SCAN":
            self.log_status(f"C-SCAN: Starting algorithm execution, direction: {direction}...")
            left = sorted([r for r in req if r < head])
            right = sorted([r for r in req if r >= head])
            
            if direction == "outward":
                for r in right:
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"C-SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                if head != self.disk_size - 1:
                    seek += abs(head - (self.disk_size - 1))
                    sequence.append(self.disk_size - 1)
                    self.log_status(f"C-SCAN: Moving to end at {self.disk_size - 1}, Seek increment: {abs(sequence[-2] - (self.disk_size - 1))}")
                seek += self.disk_size - 1
                head = 0
                sequence.append(0)
                self.log_status(f"C-SCAN: Jumping to start at {head}, Seek increment: {self.disk_size - 1}")
                for r in left:
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"C-SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
            else:
                for r in reversed(left):
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"C-SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")
                if head != 0:
                    seek += abs(head - 0)
                    sequence.append(0)
                    self.log_status(f"C-SCAN: Moving to start at 0, Seek increment: {abs(sequence[-2] - 0)}")
                seek += self.disk_size - 1
                head = self.disk_size - 1
                sequence.append(head)
                self.log_status(f"C-SCAN: Jumping to end at {head}, Seek increment: {self.disk_size - 1}")
                for r in reversed(right):
                    seek += abs(head - r)
                    head = r
                    sequence.append(r)
                    self.log_status(f"C-SCAN: Moving from {sequence[-2]} to {r}, Seek increment: {abs(sequence[-2] - r)}")

        return sequence, seek

    def update_plot(self, sequence, algo):
        self.ax.clear()
        
        # Plot the head movement path
        self.ax.plot(sequence, [0]*len(sequence), '-o', color='#2c7bb6', 
                     markersize=8, linewidth=2, label='Head Movement', alpha=0.7)
        
        # Mark the initial head position
        self.ax.scatter([sequence[0]], [0], color='#d7191c', s=150, 
                       label='Initial Head', zorder=5)
        
        # Mark all request positions
        self.ax.scatter(self.requests, [0]*len(self.requests), color='#fdae61', 
                       s=100, label='Requests', zorder=4)
        
        # Add track number labels for important points
        for i, val in enumerate(sequence):
            if i == 0 or i == len(sequence)-1 or val in [0, self.disk_size-1]:
                self.ax.text(val, 0.02, str(val), ha='center', va='bottom', 
                            fontsize=9, bbox=dict(facecolor='white', alpha=0.7, pad=1))
        
        # Set plot limits and labels
        self.ax.set_ylim(-0.1, 0.1)
        self.ax.set_yticks([])
        self.ax.set_xlim(0, self.disk_size)
        self.ax.set_xlabel("Track Number")
        self.ax.set_title(f"{algo} Disk Scheduling Algorithm", pad=20)
        self.ax.grid(True, axis='x', linestyle='--', alpha=0.6)
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        
        # Adjust layout and draw
        self.fig.tight_layout()
        self.canvas.draw()

    def play_simulation(self):
        if not hasattr(self, 'current_sequence') or not self.current_sequence:
            self.log_status("Error: No simulation to play. Please run a simulation first.", is_error=True)
            messagebox.showwarning("No Simulation", "Please run a simulation first.")
            return
            
        if self.animation_running:
            self.log_status("Animation already running.")
            return
            
        self.log_status("Starting animation...")
        # Clear any previous animation
        while not self.animation_queue.empty():
            self.animation_queue.get()
            
        # Prepare animation frames
        for i in range(1, len(self.current_sequence)):
            self.animation_queue.put((self.current_sequence[:i+1], self.current_sequence[i]))
            
        # Start animation thread
        self.animation_running = True
        self.paused = False
        self.play_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        
        self.animation_thread = Thread(target=self.animate_movement, daemon=True)
        self.animation_thread.start()

    def animate_movement(self):
        algo = self.algo_var.get()
        
        while not self.animation_queue.empty() and self.animation_running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            sequence, current_pos = self.animation_queue.get()
            self.log_status(f"{algo}: Animating step: Moving to track {current_pos}")
            
            # Update plot in main thread
            self.root.after(0, self.update_animation_plot, sequence, current_pos, algo)
            
            # Control animation speed
            time.sleep(0.5)
            
        # Animation complete
        self.log_status(f"{algo}: Animation completed.")
        self.root.after(0, self.animation_complete)

    def update_animation_plot(self, sequence, current_pos, algo):
        self.ax.clear()
        
        # Plot the path taken so far
        self.ax.plot(sequence, [0]*len(sequence), '-o', color='#2c7bb6', 
                     markersize=8, linewidth=2, label='Head Movement', alpha=0.7)
        
        # Mark the initial head position
        self.ax.scatter([sequence[0]], [0], color='#d7191c', s=150, 
                       label='Initial Head', zorder=5)
        
        # Mark all request positions
        self.ax.scatter(self.requests, [0]*len(self.requests), color='#fdae61', 
                       s=100, label='Requests', zorder=4)
        
        # Highlight current position
        self.ax.scatter([current_pos], [0], color='#2c7bb6', s=200, 
                       label='Current Position', zorder=6, edgecolor='black')
        
        # Add track number labels
        for i, val in enumerate(sequence):
            if i == 0 or i == len(sequence)-1 or val in [0, self.disk_size-1]:
                self.ax.text(val, 0.02, str(val), ha='center', va='bottom', 
                            fontsize=9, bbox=dict(facecolor='white', alpha=0.7, pad=1))
        
        # Set plot properties
        self.ax.set_ylim(-0.1, 0.1)
        self.ax.set_yticks([])
        self.ax.set_xlim(0, self.disk_size)
        self.ax.set_xlabel("Track Number")
        self.ax.set_title(f"{algo} Disk Scheduling (Animating...)", pad=20)
        self.ax.grid(True, axis='x', linestyle='--', alpha=0.6)
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def animation_complete(self):
        self.animation_running = False
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        
        # Show complete visualization
        self.update_plot(self.current_sequence, self.algo_var.get())

    def pause_simulation(self):
        if not self.animation_running:
            self.log_status("Error: No animation running to pause.", is_error=True)
            return
            
        self.paused = not self.paused
        self.log_status(f"Animation {'paused' if self.paused else 'resumed'}.")
        if self.paused:
            self.pause_button.config(text="⏸ Paused")
        else:
            self.pause_button.config(text="⏸ Pause")

    def reset(self):
        # Stop any running animation
        self.animation_running = False
        self.paused = False
        self.log_status("Resetting simulation.")
        
        # Reset UI elements
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ Pause")
        
        # Clear metrics
        self.metrics_label.config(text="")
        
        # Reset plot
        self.ax.clear()
        self.ax.set_ylim(-0.1, 0.1)
        self.ax.set_yticks([])
        self.ax.set_xlim(0, 200)
        self.ax.set_xlabel("Track Number")
        self.ax.set_title("Disk Scheduling Visualization")
        self.ax.grid(True, axis='x', linestyle='--')
        self.canvas.draw()

    def configure_status_text(self):
        """Configure tags for the status text widget."""
        self.status_text.tag_configure("error", foreground="#d63031")  # Red for errors

if __name__ == "__main__":  # Fixed typo: _main_ to __main__
    root = tk.Tk()
    app = DiskSchedulingSimulator(root)
    root.mainloop()
