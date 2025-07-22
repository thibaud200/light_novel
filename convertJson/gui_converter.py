import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading
import importlib.util

# ANSI codes for terminal colors (might not display in Tkinter log directly but good for consistency)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check_and_install_dependencies_for_gui():
    """
    Checks if necessary dependencies are installed and installs them if not.
    This version is adapted for the GUI context, using messagebox for errors.
    """
    required_packages = {
        "ebooklib": "EbookLib",
        "lxml": "lxml"
    }

    # Use a list to collect messages for the log/messagebox
    messages = []
    all_dependencies_met = True

    messages.append("Checking and installing dependencies if needed...")

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            messages.append(f"The dependency '{package_name}' ({module_name}) was not found. Installation in progress...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                messages.append(f"'{package_name}' installed successfully.")
            except subprocess.CalledProcessError as e:
                messages.append(f"ERROR: Could not install '{package_name}'. Please try manual installation with 'pip install {package_name}'.")
                messages.append(f"Error details: {e}")
                all_dependencies_met = False
                break
            except Exception as e:
                messages.append(f"An unexpected error occurred during installation of '{package_name}': {e}")
                all_dependencies_met = False
                break
        else:
            messages.append(f"The dependency '{package_name}' ({module_name}) is already installed.")
    
    if not all_dependencies_met:
        messagebox.showerror("Dependency Error", "\n".join(messages))
    else:
        messagebox.showinfo("Dependencies Check", "\n".join(messages))
    
    return all_dependencies_met # Return a status

class JsonToEpubConverterGUI:
    def __init__(self, master):
        self.master = master
        master.title("JSON to EPUB Converter")

        # --- Input Directory (-i) ---
        self.input_frame = tk.LabelFrame(master, text="Input Directory")
        self.input_frame.pack(padx=10, pady=5, fill="x")

        self.input_dir_label = tk.Label(self.input_frame, text="Path:")
        self.input_dir_label.pack(side="left", padx=5, pady=5)

        self.input_dir_entry = tk.Entry(self.input_frame, width=50)
        self.input_dir_entry.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.browse_input_button = tk.Button(self.input_frame, text="Browse", command=self.browse_input_dir)
        self.browse_input_button.pack(side="left", padx=5, pady=5)

        # --- Output Directory (-o) ---
        self.output_frame = tk.LabelFrame(master, text="Output Directory (Optional)")
        self.output_frame.pack(padx=10, pady=5, fill="x")

        self.output_dir_label = tk.Label(self.output_frame, text="Path:")
        self.output_dir_label.pack(side="left", padx=5, pady=5)

        self.output_dir_entry = tk.Entry(self.output_frame, width=50)
        self.output_dir_entry.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.browse_output_button = tk.Button(self.output_frame, text="Browse", command=self.browse_output_dir)
        self.browse_output_button.pack(side="left", padx=5, pady=5)

        # --- Mode Selection (-m) ---
        self.mode_frame = tk.LabelFrame(master, text="Conversion Mode")
        self.mode_frame.pack(padx=10, pady=5, fill="x")

        self.mode_var = tk.StringVar(value="chapter")
        self.chapter_radio = tk.Radiobutton(self.mode_frame, text="Chapter (1 EPUB per file)", variable=self.mode_var, value="chapter", command=self.toggle_volume_options)
        self.chapter_radio.pack(anchor="w", padx=5, pady=2)

        self.volume_radio = tk.Radiobutton(self.mode_frame, text="Volume (Merge chapters)", variable=self.mode_var, value="volume", command=self.toggle_volume_options)
        self.volume_radio.pack(anchor="w", padx=5, pady=2)

        # --- Volume Options (Boundaries -b / Simple Boundaries -sb) ---
        self.volume_options_frame = tk.LabelFrame(master, text="Volume Grouping Options")
        self.volume_options_frame.pack(padx=10, pady=5, fill="x")

        self.boundaries_var = tk.StringVar(value="simple") # Default to simple boundaries

        # Simple Boundaries (-sb)
        self.simple_boundaries_radio = tk.Radiobutton(self.volume_options_frame, text="Simple Boundaries (chapters per volume):", variable=self.boundaries_var, value="simple", command=self.toggle_boundary_fields)
        self.simple_boundaries_radio.pack(anchor="w", padx=5, pady=2)

        self.simple_boundaries_entry = tk.Entry(self.volume_options_frame, width=10)
        self.simple_boundaries_entry.pack(anchor="w", padx=25, pady=2)
        self.simple_boundaries_entry.insert(0, "50") # Default value

        # Custom Boundaries (-b)
        self.custom_boundaries_radio = tk.Radiobutton(self.volume_options_frame, text="Custom Boundaries (e.g., {1: [(1, 20)], 2: [(21, 60)]}):", variable=self.boundaries_var, value="custom", command=self.toggle_boundary_fields)
        self.custom_boundaries_radio.pack(anchor="w", padx=5, pady=2)

        self.custom_boundaries_entry = tk.Entry(self.volume_options_frame, width=60)
        self.custom_boundaries_entry.pack(anchor="w", padx=25, pady=2)
        self.custom_boundaries_entry.insert(0, "{}") # Default value

        # --- Merge Unspecified (-u) ---
        self.merge_unspecified_var = tk.BooleanVar()
        self.merge_unspecified_check = tk.Checkbutton(master, text="Merge Unspecified Chapters", variable=self.merge_unspecified_var)
        self.merge_unspecified_check.pack(anchor="w", padx=10, pady=5)

        # --- Run Button ---
        self.run_button = tk.Button(master, text="Run Conversion", command=self.run_conversion)
        self.run_button.pack(pady=10)

        # --- Output Log ---
        self.log_frame = tk.LabelFrame(master, text="Output Log")
        self.log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_text = tk.Text(self.log_frame, height=15, state="disabled")
        self.log_text.pack(padx=5, pady=5, fill="both", expand=True)

        self.log_scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

        self.toggle_volume_options() # Initialize the state of volume options
        self.toggle_boundary_fields() # Initialize the state of boundary fields

    def browse_input_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir_entry.delete(0, tk.END)
            self.input_dir_entry.insert(0, directory)

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def toggle_volume_options(self):
        is_volume_mode = (self.mode_var.get() == "volume")

        # Enable/disable volume grouping options
        for widget in [self.simple_boundaries_radio, self.simple_boundaries_entry,
                       self.custom_boundaries_radio, self.custom_boundaries_entry,
                       self.merge_unspecified_check]:
            if is_volume_mode:
                widget.config(state="normal")
            else:
                widget.config(state="disabled")
        self.toggle_boundary_fields() # Re-evaluate boundary field states

    def toggle_boundary_fields(self):
        is_volume_mode = (self.mode_var.get() == "volume")
        is_simple_boundaries = (self.boundaries_var.get() == "simple")

        if is_volume_mode:
            if is_simple_boundaries:
                self.simple_boundaries_entry.config(state="normal")
                self.custom_boundaries_entry.config(state="disabled")
            else:
                self.simple_boundaries_entry.config(state="disabled")
                self.custom_boundaries_entry.config(state="normal")
        else:
            self.simple_boundaries_entry.config(state="disabled")
            self.custom_boundaries_entry.config(state="disabled")

    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Scroll to the end
        self.log_text.config(state="disabled")

    def run_conversion(self):
        input_dir = self.input_dir_entry.get()
        output_dir = self.output_dir_entry.get()
        mode = self.mode_var.get()
        merge_unspecified = self.merge_unspecified_var.get()

        if not input_dir:
            messagebox.showerror("Error", "Input directory is required.")
            return

        command = ["python", "convertJson.py", "-i", input_dir]

        if output_dir:
            command.extend(["-o", output_dir])

        command.extend(["-m", mode])

        if mode == "volume":
            if self.boundaries_var.get() == "simple":
                simple_boundaries_value = self.simple_boundaries_entry.get()
                if not simple_boundaries_value.isdigit() or int(simple_boundaries_value) <= 0:
                    messagebox.showerror("Error", "Simple boundaries must be a positive integer.")
                    return
                command.extend(["-sb", simple_boundaries_value])
            else: # custom boundaries
                custom_boundaries_value = self.custom_boundaries_entry.get()
                try:
                    # Basic validation: ensure it's a valid dict string
                    if not custom_boundaries_value.strip().startswith("{") or not custom_boundaries_value.strip().endswith("}"):
                        raise ValueError("Invalid dictionary format")
                    eval(custom_boundaries_value) # Try evaluating to catch syntax errors
                except Exception:
                    messagebox.showerror("Error", "Invalid custom boundaries format. Please use a valid Python dictionary string (e.g., \"{1: [(1, 20)]}\").")
                    return
                command.extend(["-b", custom_boundaries_value])

            if merge_unspecified:
                command.append("-u")

        self.log_message(f"Running command: {' '.join(command)}")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END) # Clear previous log
        self.log_text.config(state="disabled")
        self.run_button.config(state="disabled") # Disable button while running

        # Run the script in a separate thread to keep the GUI responsive
        threading.Thread(target=self._execute_script, args=(command,)).start()

    def _execute_script(self, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1 # Line-buffered output
            )

            # Read stdout line by line
            for line in iter(process.stdout.readline, ''):
                self.master.after(0, self.log_message, line.strip())

            # Wait for the process to finish and get stderr
            process.stdout.close()
            stderr_output = process.stderr.read()
            if stderr_output:
                self.master.after(0, self.log_message, f"ERROR:\n{stderr_output.strip()}")

            process.wait() # Wait for the process to terminate

            if process.returncode == 0:
                self.master.after(0, self.log_message, "Conversion completed successfully!")
            else:
                self.master.after(0, self.log_message, f"Conversion failed with exit code {process.returncode}")

        except FileNotFoundError:
            self.master.after(0, messagebox.showerror, "Error", "Python or convertJson.py script not found. Make sure they are in your PATH or correctly specified.")
        except Exception as e:
            self.master.after(0, messagebox.showerror, "Error", f"An unexpected error occurred: {e}")
        finally:
            self.master.after(0, lambda: self.run_button.config(state="normal")) # Re-enable button

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonToEpubConverterGUI(root)
    root.mainloop()