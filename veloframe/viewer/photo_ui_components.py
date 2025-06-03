"""
Manages UI components for the photo display system.
"""
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsOpacityEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor, QBrush, QPen

class UIComponentManager:
    """Manages all UI components for photo display."""
    
    def __init__(self, scene):
        """Initialize UI components for photo display.
        
        Args:
            scene: The QGraphicsScene instance
        """
        self.scene = scene
        
        # Create separate image items for current and next photos
        # Current photos (initially visible)
        self.current_image_left = QGraphicsPixmapItem()
        self.current_image_right = QGraphicsPixmapItem()
        self.scene.addItem(self.current_image_left)
        self.scene.addItem(self.current_image_right)
        
        # Next photos (initially invisible)
        self.next_image_left = QGraphicsPixmapItem()
        self.next_image_right = QGraphicsPixmapItem()
        self.scene.addItem(self.next_image_left)
        self.scene.addItem(self.next_image_right)
        
        # Add opacity effects for fading transitions
        # For current photos
        self.opacity_effect_current_left = QGraphicsOpacityEffect()
        self.opacity_effect_current_right = QGraphicsOpacityEffect()
        self.current_image_left.setGraphicsEffect(self.opacity_effect_current_left)
        self.current_image_right.setGraphicsEffect(self.opacity_effect_current_right)
        self.opacity_effect_current_left.setOpacity(1.0)
        self.opacity_effect_current_right.setOpacity(1.0)
        
        # For next photos
        self.opacity_effect_next_left = QGraphicsOpacityEffect()
        self.opacity_effect_next_right = QGraphicsOpacityEffect()
        self.next_image_left.setGraphicsEffect(self.opacity_effect_next_left)
        self.next_image_right.setGraphicsEffect(self.opacity_effect_next_right)
        self.opacity_effect_next_left.setOpacity(0.0)  # Start invisible
        self.opacity_effect_next_right.setOpacity(0.0)  # Start invisible
        
        # Create metadata overlay items (one set for each image)
        self.metadata_rect_left = QGraphicsRectItem()
        self.metadata_rect_left.setZValue(1)  # Above the image
        self.metadata_rect_left.setBrush(QBrush(QColor(0, 0, 0, 0)))  # Start transparent
        self.metadata_rect_left.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        self.scene.addItem(self.metadata_rect_left)
        
        self.metadata_text_left = QGraphicsTextItem()
        self.metadata_text_left.setZValue(2)  # Above the rectangle
        self.metadata_text_left.setDefaultTextColor(QColor(255, 255, 255))  # White text
        self.scene.addItem(self.metadata_text_left)
        
        self.metadata_rect_right = QGraphicsRectItem()
        self.metadata_rect_right.setZValue(1)  # Above the image
        self.metadata_rect_right.setBrush(QBrush(QColor(0, 0, 0, 0)))  # Start transparent
        self.metadata_rect_right.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        self.scene.addItem(self.metadata_rect_right)
        
        self.metadata_text_right = QGraphicsTextItem()
        self.metadata_text_right.setZValue(2)  # Above the rectangle
        self.metadata_text_right.setDefaultTextColor(QColor(255, 255, 255))  # White text
        self.scene.addItem(self.metadata_text_right)
        
        # Create clock overlay items
        self.clock_rect = QGraphicsRectItem()
        self.clock_rect.setZValue(1)  # Above the image
        self.clock_rect.setBrush(QBrush(QColor(0, 0, 0, 0)))  # Start transparent
        self.clock_rect.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        self.scene.addItem(self.clock_rect)
        
        self.clock_text = QGraphicsTextItem()
        self.clock_text.setZValue(2)  # Above the rectangle
        self.clock_text.setDefaultTextColor(QColor(255, 255, 255))  # White text
        self.scene.addItem(self.clock_text)
    
    def set_scene_rect(self, width, height):
        """Set the scene rectangle to match screen dimensions.
        
        Args:
            width: Width of the scene
            height: Height of the scene
        """
        self.scene.setSceneRect(0, 0, width, height)
    
    def set_single_photo(self, is_current, pixmap, x, y):
        """Set a single photo's pixmap and position.
        
        Args:
            is_current: Whether to set current or next photo
            pixmap: The photo pixmap
            x: X position
            y: Y position
        """
        if is_current:
            self.current_image_left.setPixmap(pixmap)
            self.current_image_left.setPos(x, y)
            self.current_image_right.setPixmap(QPixmap())  # Empty pixmap
        else:
            self.next_image_left.setPixmap(pixmap)
            self.next_image_left.setPos(x, y)
            self.next_image_right.setPixmap(QPixmap())  # Empty pixmap
    
    def set_photo_pair(self, is_current, pixmap1, x1, y1, pixmap2, x2, y2):
        """Set a photo pair's pixmaps and positions.
        
        Args:
            is_current: Whether to set current or next photos
            pixmap1: The left photo pixmap
            x1: Left photo X position
            y1: Left photo Y position
            pixmap2: The right photo pixmap
            x2: Right photo X position
            y2: Right photo Y position
        """
        if is_current:
            self.current_image_left.setPixmap(pixmap1)
            self.current_image_left.setPos(x1, y1)
            self.current_image_right.setPixmap(pixmap2)
            self.current_image_right.setPos(x2, y2)
        else:
            self.next_image_left.setPixmap(pixmap1)
            self.next_image_left.setPos(x1, y1)
            self.next_image_right.setPixmap(pixmap2)
            self.next_image_right.setPos(x2, y2)
    
    def clear_next_photos(self):
        """Clear the next photo pixmaps."""
        self.next_image_left.setPixmap(QPixmap())
        self.next_image_right.setPixmap(QPixmap())
    
    def set_opacity(self, layer, position, value):
        """Set opacity for a photo layer.
        
        Args:
            layer: "current" or "next"
            position: "left" or "right"
            value: Opacity value (0.0-1.0)
        """
        if layer == "current":
            if position == "left":
                self.opacity_effect_current_left.setOpacity(value)
            else:  # "right"
                self.opacity_effect_current_right.setOpacity(value)
        else:  # "next"
            if position == "left":
                self.opacity_effect_next_left.setOpacity(value)
            else:  # "right"
                self.opacity_effect_next_right.setOpacity(value)
    
    def swap_layers(self, mode="single"):
        """Swap current and next layers after transition.
        
        Args:
            mode: "single" or "pair"
        """
        if mode == "single":
            # Get the pixmap from next image
            pixmap = self.next_image_left.pixmap()
            position = self.next_image_left.pos()
            
            # Apply to current image
            self.current_image_left.setPixmap(pixmap)
            self.current_image_left.setPos(position)
            self.current_image_right.setPixmap(QPixmap())  # Clear right image
        else:  # 'pair'
            # Get pixmaps and positions from next images
            pixmap_left = self.next_image_left.pixmap()
            pixmap_right = self.next_image_right.pixmap()
            position_left = self.next_image_left.pos()
            position_right = self.next_image_right.pos()
            
            # Apply to current images
            self.current_image_left.setPixmap(pixmap_left)
            self.current_image_right.setPixmap(pixmap_right)
            self.current_image_left.setPos(position_left)
            self.current_image_right.setPos(position_right)
        
        # Clear next images
        self.next_image_left.setPixmap(QPixmap())
        self.next_image_right.setPixmap(QPixmap())
        
        # Reset opacities
        self.opacity_effect_current_left.setOpacity(1.0)
        self.opacity_effect_current_right.setOpacity(1.0)
        self.opacity_effect_next_left.setOpacity(0.0)
        self.opacity_effect_next_right.setOpacity(0.0)
