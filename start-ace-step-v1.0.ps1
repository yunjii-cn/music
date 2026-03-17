#!/usr/bin/env powershell
# ACE-Step Launcher v1.0
# Command line launcher with embedded console

Write-Host "=========================================" -ForegroundColor Green
Write-Host "ACE-Step Launcher v1.0" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Get current script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Show menu
function Show-Menu {
    Write-Host "Please select a service to start:" -ForegroundColor Cyan
    Write-Host "1. Start Music Arena (http://127.0.0.1:7860/)" -ForegroundColor Yellow
    Write-Host "2. Start Qinglong LoRA Trainer (http://localhost:3000/)" -ForegroundColor Yellow
    Write-Host "3. Exit" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "Please enter your choice (1-3)"
    return $choice
}

# Check environment
function Check-Environment {
    Write-Host "Checking environment..." -ForegroundColor Cyan
    
    # Check if uv is installed
    $uv_path = "$HOME\.local\bin\uv.exe"
    $env_exists = Test-Path $uv_path
    
    if (-not $env_exists) {
        Write-Host "Environment not installed, installing..." -ForegroundColor Yellow
        
        # Run installation script
        & "$scriptDir\1、install-uv-qinglong.ps1"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installation failed, please check error messages" -ForegroundColor Red
            return $false
        }
        
        Write-Host "Environment installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Environment already installed" -ForegroundColor Green
    }
    
    # Check bitsandbytes
    $bitsandbytes_installed = $false
    try {
        $output = & $uv_path pip list | Select-String "bitsandbytes"
        if ($output) {
            $bitsandbytes_installed = $true
        }
    } catch {
        # Ignore errors
    }
    
    if (-not $bitsandbytes_installed) {
        Write-Host "Installing bitsandbytes..." -ForegroundColor Yellow
        & $uv_path pip install bitsandbytes
        Write-Host "bitsandbytes installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "bitsandbytes already installed" -ForegroundColor Green
    }
    
    return $true
}

# Start Music Arena
function Start-MusicArena {
    Write-Host "Starting Music Arena..." -ForegroundColor Cyan
    
    # Start Gradio Web UI
    Write-Host "Starting Gradio Web UI..." -ForegroundColor Yellow
    
    # Start in current window
    & "$scriptDir\2、run_gradio.ps1"
}

# Start Qinglong LoRA Trainer
function Start-LoraTrainer {
    Write-Host "Starting Qinglong LoRA Trainer..." -ForegroundColor Cyan
    
    # Start NPM GUI
    Write-Host "Starting NPM GUI..." -ForegroundColor Yellow
    
    # Start in current window
    & "$scriptDir\4、run_npmgui.ps1"
}

# Main loop
while ($true) {
    $choice = Show-Menu
    
    switch ($choice) {
        "1" {
            if (Check-Environment) {
                Start-MusicArena
            }
            break
        }
        "2" {
            Start-LoraTrainer
            break
        }
        "3" {
            Write-Host "Exiting launcher..." -ForegroundColor Cyan
            exit
            break
        }
        default {
            Write-Host "Invalid choice, please try again" -ForegroundColor Red
            break
        }
    }
    
    Write-Host ""
    Write-Host "Press any key to continue..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Write-Host ""
}
