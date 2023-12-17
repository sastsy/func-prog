import os
import threading
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import tkinter as tk
from tkinter import filedialog, Checkbutton, IntVar


class ImageProcessorApp():
    def __init__(self, master):
        self.master = master
        self.master.title("Image Processor")

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.filters = {
            "sharpen": tk.IntVar(),
            "sepia": tk.IntVar(),
            "shrink": tk.IntVar(),
        }

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Input Folder:").pack()
        tk.Entry(self.master, textvariable=self.input_folder, state="readonly").pack(expand=True)
        tk.Button(self.master, text="Browse", command=self.browse_input_folder).pack(pady=10)

        tk.Label(self.master, text="Output Folder:").pack()
        tk.Entry(self.master, textvariable=self.output_folder, state="readonly").pack(expand=True)
        tk.Button(self.master, text="Browse", command=self.browse_output_folder).pack(pady=10)

        tk.Label(self.master, text="Filters:").pack()
        for filter_name, filter_var in self.filters.items():
            Checkbutton(self.master, text=filter_name, variable=filter_var).pack(pady=3)

        tk.Button(self.master, text="Process Images", command=self.process_images).pack()

    def browse_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)
    
    def apply_filters(self, input_path, output_path):
        print('started processing')
        original_image = Image.open(input_path)
        processed_image = original_image
        # print(self.filters)
        for filter_name, filter_var in self.filter_values.items():
            if filter_var:
                filter_func = self.get_filter_function(filter_name)
                processed_image = filter_func(processed_image)
        output_filename = f"{os.path.splitext(os.path.basename(input_path))[0]}_{filter_name}.jpg"
        output_filepath = os.path.join(output_path, output_filename)
        processed_image.save(output_filepath)

    def get_filter_function(self, filter_name):
        if filter_name == "sharpen":
            return lambda img: ImageEnhance.Sharpness(img).enhance(5.0)
        elif filter_name == "sepia":
            return lambda img: ImageOps.colorize(img.convert('L'), '#704214', '#C0C080')
        elif filter_name == "shrink":
            return lambda img: img.resize((img.width // 2, img.height // 2))

    def process_images(self):
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()

        if not input_folder or not output_folder:
            tk.messagebox.showerror("Error", "Please select input and output folders.")
            return

        os.makedirs(output_folder, exist_ok=True)

        image_files = [f for f in os.listdir(input_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

        self.filter_values = {filter_name: filter_var.get() for filter_name, filter_var in self.filters.items()}

        threads = []
        for image_file in image_files:
            input_filepath = os.path.join(input_folder, image_file)
            thread = threading.Thread(target=self.apply_filters, args=(input_filepath, output_folder))
            threads.append(thread)
            thread.start()
        
        print(threads)

        for thread in threads:
            thread.join()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.geometry("400x400")
    root.mainloop()
