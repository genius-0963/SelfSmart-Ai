#!/bin/bash

# SmartShelf AI - Docker PATH Setup Script
# Adds Docker CLI to your shell PATH permanently

echo "🐳 Setting up Docker PATH..."

# Add Docker to PATH for current session
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

# Add to .zshrc for permanent setup
if ! grep -q "Docker.app/Contents/Resources/bin" ~/.zshrc; then
    echo "" >> ~/.zshrc
    echo "# Docker PATH setup" >> ~/.zshrc
    echo "export PATH=\"/Applications/Docker.app/Contents/Resources/bin:\$PATH\"" >> ~/.zshrc
    echo "✅ Added Docker to ~/.zshrc"
else
    echo "✅ Docker PATH already configured in ~/.zshrc"
fi

# Test Docker commands
echo "🔍 Testing Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker command not found"
fi

if docker compose version &> /dev/null; then
    echo "✅ Docker Compose: $(docker compose version)"
else
    echo "❌ Docker Compose command not found"
fi

echo ""
echo "🎯 Docker is now ready! Run this to apply changes to your current terminal:"
echo "   source ~/.zshrc"
echo ""
echo "🚀 Then deploy SmartShelf AI with:"
echo "   ./scripts/deploy-enhanced.sh deploy"
