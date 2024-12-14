import sys
import fitz  # PyMuPDF
from PyQt5 import QtWidgets, QtGui  # Import QtWidgets and QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, 
                             QGraphicsView, QGraphicsScene, QVBoxLayout, 
                             QWidget, QPushButton, QHBoxLayout, QGraphicsRectItem, QMessageBox)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QPalette  # Import QPalette
from PIL import Image
import numpy as np
import tempfile
import os

class PDFCropTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pdf_document = None
        self.crop_rect_item = None  # To store the cropping rectangle
        self.start_pos = None  # To store the start position of the crop
        self.is_drawing = False  # To track if a rectangle is being drawn
        self.original_file_name = None  # To store the original file name

    def initUI(self):
        self.setWindowTitle('PDF Crop Tool')
        self.setGeometry(100, 100, 800, 600)

        # Set the application icon
        self.setWindowIcon(QtGui.QIcon('C:/Users/USER/Downloads/End term/pdfcropperapp.ico'))  # Update this path

        # Set the application style
        QApplication.setStyle('Fusion')
        self.set_custom_palette()  # Call the custom palette function

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        # Create buttons with icons
        button_layout = QHBoxLayout()
        open_button = QPushButton('Open PDF')
        open_button.setIcon(QtGui.QIcon('path/to/open_icon.png'))  # Add icon
        open_button.clicked.connect(self.open_pdf)

        crop_button = QPushButton('Crop PDF')
        crop_button.setIcon(QtGui.QIcon('path/to/crop_icon.png'))  # Add icon
        crop_button.clicked.connect(self.crop_pdf)

        zoom_in_button = QPushButton('Zoom In')
        zoom_in_button.setIcon(QtGui.QIcon('path/to/zoom_in_icon.png'))  # Add icon
        zoom_in_button.clicked.connect(self.zoom_in)

        zoom_out_button = QPushButton('Zoom Out')
        zoom_out_button.setIcon(QtGui.QIcon('path/to/zoom_out_icon.png'))  # Add icon
        zoom_out_button.clicked.connect(self.zoom_out)

        button_layout.addWidget(open_button)
        button_layout.addWidget(crop_button)
        button_layout.addWidget(zoom_in_button)
        button_layout.addWidget(zoom_out_button)
        layout.addLayout(button_layout)

        # Enable mouse events for cropping
        self.view.setMouseTracking(True)
        self.view.mousePressEvent = self.start_crop
        self.view.mouseMoveEvent = self.update_crop
        self.view.mouseReleaseEvent = self.end_crop

        # Apply QSS for additional styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E2E2E; /* Dark gray background */
            }
            QPushButton {
                background-color: #4CAF50; /* Green */
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green */
            }
            QGraphicsView {
                border: 1px solid #ccc;
                background-color: #3C3C3C; /* Slightly lighter gray for the view */
            }
            QLabel {
                color: white; /* White text for labels */
            }
        """)

    def set_custom_palette(self):
        palette = QPalette()  # Create a QPalette instance
        palette.setColor(QPalette.Window, QColor(46, 46, 46))  # Dark gray
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        palette.setColor(QPalette.Button, QColor(70, 130, 180))  # Button color
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White button text
        palette.setColor(QPalette.Highlight, QColor(100, 150, 250))  # Highlight color
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # Highlighted text color
        QApplication.setPalette(palette)

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF files (*.pdf)")
        if file_name:
            try:
                self.pdf_document = fitz.open(file_name)
                self.original_file_name = os.path.splitext(os.path.basename(file_name))[0]
                self.load_pages()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open PDF: {e}")

    def load_pages(self):
        if not self.pdf_document:
            return

        self.scene.clear()
        combined_image = None
        
        # Convert all pages to images and combine them with transparency
        for page_num in range(self.pdf_document.page_count):
            page = self.pdf_document[page_num]
            # Set DPI to 300 by using a scaling factor
            zoom = 300 / 72  # 72 is the default DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)  # Higher resolution
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            if combined_image is None:
                combined_image = np.array(img).astype(float)
            else:
                # Add new page with reduced opacity
                new_img = np.array(img).astype(float)
                combined_image = combined_image * 0.7 + new_img * 0.3
        
        if combined_image is not None:
            # Convert back to QImage
            combined_image = combined_image.astype(np.uint8)
            height, width, channel = combined_image.shape
            bytes_per_line = 3 * width
            
            q_img = QImage(combined_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            self.scene.addPixmap(pixmap)
            self.view.setSceneRect(QRectF(pixmap.rect()))
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def start_crop(self, event):
        self.start_pos = self.view.mapToScene(event.pos())
        if self.crop_rect_item:
            self.scene.removeItem(self.crop_rect_item)
        self.crop_rect_item = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
        self.crop_rect_item.setPen(QPen(QColor(255, 0, 0), 2, Qt.SolidLine))
        self.scene.addItem(self.crop_rect_item)
        self.is_drawing = True

    def update_crop(self, event):
        if self.is_drawing and self.crop_rect_item is not None:
            end_pos = self.view.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            self.crop_rect_item.setRect(rect)

    def end_crop(self, event):
        self.is_drawing = False

    def crop_pdf(self):
        if not self.pdf_document or self.crop_rect_item is None:
            QMessageBox.warning(self, "Warning", "No crop area selected.")
            return

        # Get the crop rectangle from the scene
        crop_rect = self.crop_rect_item.rect()
        crop_box = (crop_rect.left(), crop_rect.top(), crop_rect.right(), crop_rect.bottom())

        # Create a new PDF document for the cropped pages
        cropped_pdf = fitz.open()

        temp_files = []  # To keep track of temporary files

        try:
            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                # Set DPI to 300 by using a scaling factor
                zoom = 300 / 72  # 72 is the default DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)  # Higher resolution
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Crop the image based on the selected rectangle
                cropped_img = img.crop(crop_box)

                # Compress the image by reducing quality
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img_file:
                    cropped_img.save(temp_img_file, format="JPEG", quality=85)  # Adjust quality as needed
                    temp_img_file.flush()
                    temp_files.append(temp_img_file.name)

                    # Insert the JPEG image into the new PDF
                    new_page = cropped_pdf.new_page(width=cropped_img.width, height=cropped_img.height)
                    new_page.insert_image(new_page.rect, filename=temp_img_file.name)

            # Save the cropped PDF with a new name
            save_path = QFileDialog.getSaveFileName(self, "Save Cropped PDF", f"{self.original_file_name}_crop.pdf", "PDF files (*.pdf)")[0]
            if save_path:
                cropped_pdf.save(save_path)
                QMessageBox.information(self, "Success", "Cropped PDF saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to crop PDF: {e}")
        finally:
            cropped_pdf.close()
            self.clear_pdf()  # Clear the current PDF from memory
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Failed to delete temporary file {temp_file}: {e}")

    def clear_pdf(self):
        """Clear the current PDF from memory and reset the UI."""
        self.pdf_document = None
        self.scene.clear()
        self.crop_rect_item = None
        self.original_file_name = None

    def zoom_in(self):
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        self.view.scale(0.8, 0.8)

def main():
    app = QApplication(sys.argv)
    tool = PDFCropTool()
    tool.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()