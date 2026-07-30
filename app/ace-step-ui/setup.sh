#!/bin/bash
# ACE-Step UI Setup Script

set -e

echo "=================================="
echo "  ACE-Step UI Setup"
echo "=================================="

# ============= ACE-Step Configuration | ACE-Step 配置 =============
# Set ACE-Step installation path (parent directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACESTEP_PATH="${ACESTEP_PATH:-$(dirname "$SCRIPT_DIR")}"
# Set Python executable path (virtual environment)
if [ -f "$ACESTEP_PATH/.venv/bin/python" ]; then
    PYTHON_PATH="$ACESTEP_PATH/.venv/bin/python"
elif [ -f "$ACESTEP_PATH/venv/bin/python" ]; then
    PYTHON_PATH="$ACESTEP_PATH/venv/bin/python"
else
    PYTHON_PATH=""
fi

echo "ACE-Step Path: $ACESTEP_PATH"
echo "Python Path:   ${PYTHON_PATH:-not found}"
echo ""

if [ ! -d "$ACESTEP_PATH" ]; then
    echo "Error: ACE-Step not found at $ACESTEP_PATH"
    exit 1
fi

if [ -z "$PYTHON_PATH" ]; then
    echo "Warning: ACE-Step venv not found. Please set up ACE-Step first:"
    echo "  cd $ACESTEP_PATH"
    echo "  uv venv && uv pip install -e ."
fi

# Create .env file
echo "Creating .env file..."
cat > .env << EOF
# ACE-Step UI Configuration

# Path to ACE-Step installation
ACESTEP_PATH=$ACESTEP_PATH
PYTHON_PATH=${PYTHON_PATH}

# Server ports
PORT=3001
FRONTEND_PORT=3000

# Database
DATABASE_PATH=./server/data/acestep.db
EOF

# Check Node.js and npm
echo ""
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Installing Node.js 24 LTS..."
    
    # Try nvm first
    if command -v nvm &> /dev/null || [ -f "$HOME/.nvm/nvm.sh" ]; then
        echo "Using nvm to install Node.js 24 LTS..."
        if command -v nvm &> /dev/null; then
            nvm install 24
            nvm use 24
        else
            source "$HOME/.nvm/nvm.sh"
            nvm install 24
            nvm use 24
        fi
    else
        echo "nvm not found. Downloading Node.js 24 LTS binary..."
        NODE_VERSION="24.3.0"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            ARCH=$(uname -m)
            if [[ "$ARCH" == "x86_64" ]]; then
                NODE_ARCH="x64"
            elif [[ "$ARCH" == "aarch64" ]]; then
                NODE_ARCH="arm64"
            fi
            NODE_FILE="node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
            wget -q "https://nodejs.org/dist/v${NODE_VERSION}/${NODE_FILE}" -O /tmp/node.tar.xz
            tar -xf /tmp/node.tar.xz -C /tmp
            sudo cp -r /tmp/node-v${NODE_VERSION}-linux-${NODE_ARCH}/* /usr/local/
            rm -f /tmp/node.tar.xz
            rm -rf /tmp/node-v${NODE_VERSION}-linux-${NODE_ARCH}
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install node@24
            else
                echo "Please install Node.js manually from https://nodejs.org/"
                exit 1
            fi
        fi
    fi
fi

# Verify Node.js version
NODE_VERSION=$(node --version | sed 's/v//')
echo "Node.js version: $NODE_VERSION"

if ! command -v npm &> /dev/null; then
    echo "npm not found. Please check your Node.js installation."
    exit 1
fi

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
npm install

# Install server dependencies
echo ""
echo "Installing server dependencies..."
cd server
npm install
cd ..

# Initialize database
echo ""
echo "Initializing database..."
cd server
npm run migrate 2>/dev/null || echo "Migration script not found, skipping..."
cd ..

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "To start the application:"
echo ""
echo "  # Terminal 1 - Start backend"
echo "  cd server && npm run dev"
echo ""
echo "  # Terminal 2 - Start frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000"
echo ""
