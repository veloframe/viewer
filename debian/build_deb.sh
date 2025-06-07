#!/bin/bash
set -e

# Configuration
PACKAGE_NAME="veloframe"
VERSION=$(python3 -c "import setuptools; exec(open('setup.py').read()); print(__version__)" 2>/dev/null || echo "0.1.0")
MAINTAINER="Martin Maisey"
DESCRIPTION="A beautiful, full-screen photo frame application"
ARCHITECTURE="all"
DEPENDS="python3 (>= 3.8), python3-pyside6, python3-pil, python3-yaml, python3-numpy"

# Create build directories
mkdir -p "dist"
BUILD_DIR="build/deb-build"
mkdir -p "$BUILD_DIR"

# Create the package directory structure
PKG_DIR="$BUILD_DIR/$PACKAGE_NAME-$VERSION"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/lib/python3/dist-packages/$PACKAGE_NAME"
mkdir -p "$PKG_DIR/etc/veloframe"
mkdir -p "$PKG_DIR/lib/systemd/system"

# Create control file
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCHITECTURE
Depends: $DEPENDS
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 A beautiful, full-screen photo frame application
 for displaying photos with transitions and overlays.
EOF

# Create postinst script
cat > "$PKG_DIR/DEBIAN/postinst" << EOF
#!/bin/bash
set -e
chmod 755 /usr/bin/veloframe
systemctl daemon-reload
echo "VeloFrame has been installed. To enable the service, run:"
echo "sudo systemctl enable --now veloframe.service"
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Copy application files
cp -r veloframe "$PKG_DIR/usr/lib/python3/dist-packages/"
cp config.yaml.example "$PKG_DIR/etc/veloframe/"
cp debian/veloframe.service "$PKG_DIR/lib/systemd/system/"

# Copy fonts directory if it exists
if [ -d "fonts" ]; then
  mkdir -p "$PKG_DIR/usr/share/veloframe/fonts"
  cp -r fonts/* "$PKG_DIR/usr/share/veloframe/fonts/"
fi

# Create executable script
cat > "$PKG_DIR/usr/bin/veloframe" << EOF
#!/bin/bash
# Check for config file
CONFIG_FILE="\$HOME/.config/veloframe/config.yaml"
SYSTEM_CONFIG="/etc/veloframe/config.yaml"

if [ ! -f "\$CONFIG_FILE" ]; then
  # Create user config directory if it doesn't exist
  mkdir -p "\$HOME/.config/veloframe"
  
  # If user doesn't have a config file, copy from system or example
  if [ -f "\$SYSTEM_CONFIG" ]; then
    cp "\$SYSTEM_CONFIG" "\$CONFIG_FILE"
  else
    cp "/etc/veloframe/config.yaml.example" "\$CONFIG_FILE"
  fi
  
  echo "Created default configuration at \$CONFIG_FILE"
fi

# Update font paths in config to use system paths
sed -i 's|./fonts/|/usr/share/veloframe/fonts/|g' "\$CONFIG_FILE" 2>/dev/null || true

# Run the application
exec python3 -m veloframe.viewer.photo_frame "\$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/veloframe"

# Build the package
dpkg-deb --build "$PKG_DIR"

# Move the package to dist directory
mv "$BUILD_DIR/$PACKAGE_NAME-$VERSION.deb" "dist/"

# Validate the package
echo "Validating package with lintian..."
lintian "dist/$PACKAGE_NAME-$VERSION.deb" || true

echo "Package created: dist/$PACKAGE_NAME-$VERSION.deb"
