"""
Manages metadata overlays for photos.
"""
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtCore import Qt

from .photo_processing import get_capture_date_str

class MetadataManager:
    """Manages metadata overlays for photos."""
    
    def __init__(self, scene, config):
        """Initialize the metadata manager.
        
        Args:
            scene: The QGraphicsScene instance
            config: Configuration object
        """
        self.scene = scene
        self.config = config
    
    def update_overlay(self, ui_components, exif, photo_path, pixmap, image_x, image_y, position="left"):
        """Update the metadata overlay with the capture date information.
        
        Args:
            ui_components: UIComponentManager instance
            exif: EXIF data dictionary
            photo_path: Path to the current photo
            pixmap: The current photo pixmap
            image_x: X position of the image in the scene
            image_y: Y position of the image in the scene
            position: Which overlay to update ("left" or "right")
        """
        # Select the appropriate overlay items based on position
        if position == "left":
            metadata_rect = ui_components.metadata_rect_left
            metadata_text = ui_components.metadata_text_left
        else:  # "right"
            metadata_rect = ui_components.metadata_rect_right
            metadata_text = ui_components.metadata_text_right
        
        # Get the capture date string
        date_str = get_capture_date_str(exif, photo_path)
        
        # Configure font
        font = QFont(self.config.get('metadata_font', 'Arial'))
        font.setPointSize(self.config.get('metadata_point_size', 20))
        metadata_text.setFont(font)
        metadata_text.setPlainText(date_str)
        
        # Calculate text dimensions
        text_width = metadata_text.boundingRect().width()
        text_height = metadata_text.boundingRect().height()
        
        # Set padding
        padding = 5
        
        # Distance from edge
        edge_distance = 0
        
        # Position the metadata overlay
        rect_y = image_y + pixmap.height() - text_height - padding * 2 - edge_distance  # Always at bottom
        rect_width = text_width + padding * 2
        rect_height = text_height + padding * 2
        
        if position == "left":
            # Position from bottom left of the image (18px from edges)
            rect_x = image_x + edge_distance
        else:  # "right"
            # Position from bottom right of the image (18px from edges)
            rect_x = image_x + pixmap.width() - text_width - padding * 2 - edge_distance
        
        # Configure rectangle
        metadata_rect.setRect(rect_x, rect_y, rect_width, rect_height)
        opacity = self.config.get('metadata_opacity', 70)
        metadata_rect.setBrush(QBrush(QColor(0, 0, 0, int(opacity * 2.55))))  # Convert 0-100 to 0-255
        
        # Position text
        metadata_text.setPos(rect_x + padding, rect_y + padding)
    
    def hide_overlay(self, ui_components, position="both"):
        """Hide metadata overlay.
        
        Args:
            ui_components: UIComponentManager instance
            position: Which overlay to hide ("left", "right", or "both")
        """
        if position in ["left", "both"]:
            ui_components.metadata_rect_left.setBrush(QBrush(QColor(0, 0, 0, 0)))
            ui_components.metadata_text_left.setPlainText("")
        
        if position in ["right", "both"]:
            ui_components.metadata_rect_right.setBrush(QBrush(QColor(0, 0, 0, 0)))
            ui_components.metadata_text_right.setPlainText("")
    
    def update_for_photo_details(self, ui_components, photo_details):
        """Update metadata overlays based on photo details.
        
        Args:
            ui_components: UIComponentManager instance
            photo_details: Dictionary with photo details
        """
        # Hide all metadata first
        self.hide_overlay(ui_components, "both")
        
        # Skip if metadata is disabled
        if not photo_details.get('show_metadata', False):
            return
            
        if photo_details['mode'] == 'single':
            # Update left metadata
            self.update_overlay(
                ui_components,
                photo_details['exif'], 
                photo_details['path'], 
                photo_details['pixmap'], 
                photo_details['image_x'], 
                photo_details['image_y'], 
                "left"
            )
        else:  # 'pair'
            # Update both left and right metadata
            self.update_overlay(
                ui_components,
                photo_details['exif1'], 
                photo_details['path1'], 
                photo_details['pixmap1'], 
                photo_details['image1_x'], 
                photo_details['image1_y'], 
                "left"
            )
            self.update_overlay(
                ui_components,
                photo_details['exif2'], 
                photo_details['path2'], 
                photo_details['pixmap2'], 
                photo_details['image2_x'], 
                photo_details['image2_y'], 
                "right"
            )
