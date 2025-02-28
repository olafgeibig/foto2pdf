Task 1: Project Setup
	•	Create a new project directory (e.g., document_processor).
	•	Set up a virtual environment (using venv or conda).
	•	Install dependencies via pip:
	•	Pillow (e.g., pip install Pillow)
	•	deskew (e.g., pip install deskew)
	•	NumPy (e.g., pip install numpy)
	•	(Optionally) a PDF generation library like ReportLab for later tasks.

Task 2: File Importer Module
	•	Implement a function that scans a given directory recursively for image files.
	•	Use Python’s pathlib (or os.walk) to list files.
	•	Filter files by image extensions (e.g., .jpg, .jpeg, .png).
	•	Output: A list of file paths to process.

Task 3: Basic Image Loading
	•	Implement a function that takes a file path and opens the image using Pillow.
	•	Ensure the image is loaded properly.
	•	(Optionally) Log the image’s filename, size, and format for debugging.

Task 4: Deskewing Function
	•	Implement a function to deskew a single image:
	•	Convert the image to grayscale (using Pillow’s .convert("L")).
	•	Convert the Pillow image to a NumPy array (needed for the deskew function).
	•	Use the determine_skew() function from the deskew library on the NumPy array.
	•	Rotate the original image by the negative of the detected skew angle using Pillow’s .rotate() method with expand=True.
	•	Output: A deskewed Pillow image.

Task 5: Cropping Function
	•	Implement a function that crops the deskewed image.
	•	For a first version, define a fixed crop box (e.g., a centered box that approximates a DIN A4 region).
	•	Use Pillow’s .crop() method.
	•	Output: A cropped Pillow image.

Task 6: Combined Processing Pipeline
	•	Implement a high-level function that, given an image file path, performs the following in sequence:
	1.	Opens the image.
	2.	Deskews the image (calls the deskewing function).
	3.	Crops the deskewed image (calls the cropping function).
	•	Return: The processed image ready for further processing (such as PDF conversion).

Task 7: Batch Processing
	•	Implement a function that takes a directory path (from Task 2) and iterates over all the image file paths.
	•	For each image, run the combined processing pipeline.
	•	Save or store the processed images in a list or directly to an output folder.
	•	Output: Processed images saved to disk (e.g., with a prefix like processed_).

Task 8: Command-Line Interface (CLI)
	•	Set up a CLI using argparse:
	•	Add arguments for the input directory and output directory.
	•	Optionally add parameters (e.g., crop dimensions, deskew tolerance) if you want to expose them.
	•	Integrate the batch processing function so that when the script is run from the command line, it processes the given directory and saves results.

Task 9: (Optional) PDF Generation Stub
	•	Implement a stub function that will eventually take the processed images and generate a PDF.
	•	For now, simply log or print a message indicating that PDF generation is pending.
	•	(Later, integrate a library such as ReportLab or FPDF to combine images into a PDF.)

Task 10: Documentation and Testing
	•	Write documentation (docstrings or README) explaining how each module and function works.
	•	Implement simple tests for key functions:
	•	Test that the file importer returns the correct number of image paths.
	•	Test the deskew function on sample images with known skew.
	•	Test that cropping returns images of the expected size.
	•	Optionally, include logging for errors or unexpected behavior.
