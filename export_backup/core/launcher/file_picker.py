#!/usr/bin/env python3
"""
File Picker Module - GUI file selection with tkinter
Provides visual file selection with preview and validation
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FilePicker:
    """Enhanced file picker with GUI support and validation"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.settings_file = self.data_dir / "user_preferences.json"
        self.last_directory = self._load_last_directory()
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_last_directory(self) -> str:
        """Load the last used directory from settings"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get("last_directory", str(Path.home()))
        except Exception:
            pass
        return str(Path.home())
    
    def _save_last_directory(self, directory: str):
        """Save the last used directory to settings"""
        try:
            settings = {}
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
            
            settings["last_directory"] = directory
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass  # Fail silently if we can't save settings
    
    def _validate_image_file(self, file_path: str) -> bool:
        """Validate that the file is a supported image format"""
        try:
            file_path = Path(file_path)
            
            # Check extension
            if file_path.suffix.lower() not in self.supported_formats:
                return False
            
            # Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Try to open with PIL to verify it's a valid image
            with Image.open(file_path) as img:
                img.verify()
            
            # Check file size (max 50MB)
            if file_path.stat().st_size > 50 * 1024 * 1024:
                messagebox.showwarning(
                    "File Too Large",
                    f"File is {file_path.stat().st_size / (1024*1024):.1f}MB. "
                    "Maximum supported size is 50MB."
                )
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror(
                "Invalid Image",
                f"Could not validate image file:\n{str(e)}"
            )
            return False
    
    def pick_single_file(self) -> Optional[str]:
        """Open GUI file picker for single file selection"""
        try:
            # Hide the default tkinter root window
            root = tk.Tk()
            root.withdraw()
            
            # File dialog options
            filetypes = [
                ("Image files", " ".join(f"*{ext}" for ext in self.supported_formats)),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("GIF files", "*.gif"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
            
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Image for Video Generation",
                initialdir=self.last_directory,
                filetypes=filetypes
            )
            
            root.destroy()
            
            if not file_path:
                return None
            
            # Validate the selected file
            if not self._validate_image_file(file_path):
                return None
            
            # Save directory for next time
            self._save_last_directory(str(Path(file_path).parent))
            
            return file_path
            
        except Exception as e:
            messagebox.showerror("File Picker Error", f"Error opening file picker: {str(e)}")
            return None
    
    def pick_multiple_files(self) -> List[str]:
        """Open GUI file picker for multiple file selection"""
        try:
            # Hide the default tkinter root window
            root = tk.Tk()
            root.withdraw()
            
            # File dialog options
            filetypes = [
                ("Image files", " ".join(f"*{ext}" for ext in self.supported_formats)),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("GIF files", "*.gif"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
            
            # Open file dialog for multiple files
            file_paths = filedialog.askopenfilenames(
                title="Select Images for Batch Video Generation",
                initialdir=self.last_directory,
                filetypes=filetypes
            )
            
            root.destroy()
            
            if not file_paths:
                return []
            
            # Validate all selected files
            validated_files = []
            invalid_files = []
            
            for file_path in file_paths:
                if self._validate_image_file(file_path):
                    validated_files.append(file_path)
                else:
                    invalid_files.append(Path(file_path).name)
            
            # Show results
            if invalid_files:
                messagebox.showwarning(
                    "Some Files Invalid",
                    f"The following files were skipped (invalid format or corrupted):\n\n" +
                    "\n".join(invalid_files[:5]) +  # Show first 5
                    (f"\n... and {len(invalid_files) - 5} more" if len(invalid_files) > 5 else "")
                )
            
            if validated_files:
                # Save directory for next time
                self._save_last_directory(str(Path(validated_files[0]).parent))
                
                messagebox.showinfo(
                    "Files Selected",
                    f"Successfully selected {len(validated_files)} valid image files for batch processing."
                )
            
            return validated_files
            
        except Exception as e:
            messagebox.showerror("File Picker Error", f"Error opening file picker: {str(e)}")
            return []
    
    def pick_with_preview(self) -> Optional[str]:
        """Advanced file picker with image preview"""
        try:
            class PreviewFilePicker:
                def __init__(self, parent_picker):
                    self.parent_picker = parent_picker
                    self.selected_file = None
                    self.root = tk.Tk()
                    self.root.title("Select Image - FAL.AI Video Generator")
                    self.root.geometry("800x600")
                    self.root.resizable(True, True)
                    
                    self.setup_ui()
                
                def setup_ui(self):
                    # Main frame
                    main_frame = ttk.Frame(self.root, padding="10")
                    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                    
                    # Configure grid weights
                    self.root.columnconfigure(0, weight=1)
                    self.root.rowconfigure(0, weight=1)
                    main_frame.columnconfigure(1, weight=1)
                    main_frame.rowconfigure(1, weight=1)
                    
                    # File selection frame
                    file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
                    file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
                    file_frame.columnconfigure(1, weight=1)
                    
                    # Browse button
                    ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=0, padx=(0, 10))
                    
                    # File path display
                    self.file_path_var = tk.StringVar(value="No file selected")
                    file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var, background="white", relief="sunken")
                    file_path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
                    
                    # File info
                    self.file_info_var = tk.StringVar(value="")
                    ttk.Label(file_frame, textvariable=self.file_info_var, foreground="gray").grid(row=1, column=1, sticky=(tk.W,))
                    
                    # Preview frame
                    preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="5")
                    preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
                    preview_frame.columnconfigure(0, weight=1)
                    preview_frame.rowconfigure(0, weight=1)
                    
                    # Preview canvas
                    self.preview_canvas = tk.Canvas(preview_frame, background="white", width=400, height=300)
                    self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                    
                    # Preview scrollbars
                    h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
                    h_scroll.grid(row=1, column=0, sticky=(tk.W, tk.E))
                    v_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
                    v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
                    
                    self.preview_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
                    
                    # Buttons frame
                    button_frame = ttk.Frame(main_frame)
                    button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
                    
                    ttk.Button(button_frame, text="Select This Image", command=self.select_file, state="disabled").grid(row=0, column=0, padx=(0, 10))
                    ttk.Button(button_frame, text="Cancel", command=self.cancel).grid(row=0, column=1)
                    
                    self.select_button = button_frame.winfo_children()[0]
                
                def browse_file(self):
                    filetypes = [
                        ("Image files", " ".join(f"*{ext}" for ext in self.parent_picker.supported_formats)),
                        ("All files", "*.*")
                    ]
                    
                    file_path = filedialog.askopenfilename(
                        title="Select Image",
                        initialdir=self.parent_picker.last_directory,
                        filetypes=filetypes
                    )
                    
                    if file_path and self.parent_picker._validate_image_file(file_path):
                        self.load_preview(file_path)
                
                def load_preview(self, file_path):
                    try:
                        # Update file path display
                        self.file_path_var.set(file_path)
                        
                        # Get file info
                        file_size = Path(file_path).stat().st_size
                        with Image.open(file_path) as img:
                            width, height = img.size
                            format_name = img.format
                        
                        size_mb = file_size / (1024 * 1024)
                        self.file_info_var.set(f"{format_name} • {width}×{height} • {size_mb:.1f} MB")
                        
                        # Load and display image
                        with Image.open(file_path) as img:
                            # Calculate preview size (max 400x300, maintain aspect ratio)
                            preview_width = 400
                            preview_height = 300
                            
                            img_ratio = img.width / img.height
                            preview_ratio = preview_width / preview_height
                            
                            if img_ratio > preview_ratio:
                                # Image is wider
                                new_width = preview_width
                                new_height = int(preview_width / img_ratio)
                            else:
                                # Image is taller
                                new_height = preview_height
                                new_width = int(preview_height * img_ratio)
                            
                            # Resize image for preview
                            preview_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            self.photo = ImageTk.PhotoImage(preview_img)
                            
                            # Clear canvas and display image
                            self.preview_canvas.delete("all")
                            self.preview_canvas.create_image(200, 150, image=self.photo, anchor=tk.CENTER)
                            
                            # Update canvas scroll region
                            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
                        
                        # Enable select button
                        self.select_button.configure(state="normal")
                        self.temp_file_path = file_path
                        
                    except Exception as e:
                        messagebox.showerror("Preview Error", f"Could not load image preview: {str(e)}")
                
                def select_file(self):
                    if hasattr(self, 'temp_file_path'):
                        self.selected_file = self.temp_file_path
                        self.parent_picker._save_last_directory(str(Path(self.temp_file_path).parent))
                    self.root.quit()
                    self.root.destroy()
                
                def cancel(self):
                    self.selected_file = None
                    self.root.quit()
                    self.root.destroy()
                
                def run(self):
                    self.root.mainloop()
                    return self.selected_file
            
            # Run the preview picker
            picker = PreviewFilePicker(self)
            return picker.run()
            
        except ImportError:
            # PIL not available, fall back to basic picker
            return self.pick_single_file()
        except Exception as e:
            messagebox.showerror("Preview Picker Error", f"Error in preview picker: {str(e)}")
            return self.pick_single_file()
    
    def get_cli_file_path(self, prompt: str = "Enter image path") -> Optional[str]:
        """Get file path via CLI input with validation"""
        while True:
            try:
                path = input(f"{prompt}: ").strip()
                if not path:
                    return None
                
                # Handle quotes
                path = path.strip('"\'')
                
                if self._validate_image_file(path):
                    self._save_last_directory(str(Path(path).parent))
                    return path
                else:
                    print("❌ Invalid or unsupported image file. Please try again.")
                    print(f"Supported formats: {', '.join(self.supported_formats)}")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None
            except Exception as e:
                print(f"❌ Error: {e}")

# Convenience functions for backward compatibility
def pick_file() -> Optional[str]:
    """Simple file picker function"""
    picker = FilePicker()
    return picker.pick_single_file()

def pick_files() -> List[str]:
    """Simple multiple file picker function"""
    picker = FilePicker()
    return picker.pick_multiple_files()

def pick_file_with_preview() -> Optional[str]:
    """File picker with image preview"""
    picker = FilePicker()
    return picker.pick_with_preview()

# Test function
if __name__ == "__main__":
    print("Testing File Picker...")
    
    picker = FilePicker()
    
    print("\n1. Testing single file selection...")
    file_path = picker.pick_single_file()
    if file_path:
        print(f"✅ Selected: {file_path}")
    else:
        print("❌ No file selected")
    
    print("\n2. Testing CLI file selection...")
    cli_path = picker.get_cli_file_path("Enter image path for CLI test")
    if cli_path:
        print(f"✅ CLI Selected: {cli_path}")
    else:
        print("❌ No CLI file selected")