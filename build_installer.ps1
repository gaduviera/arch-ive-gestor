[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$specFile = Join-Path $projectRoot "ArchIve.spec"
$exePath = Join-Path $projectRoot "dist\ArchIve\ArchIve.exe"
$issFile = Join-Path $projectRoot "installer\arch-ive-setup.iss"
$installerOutput = Join-Path $projectRoot "installer\output\arch-ive-setup-v1.0.0.exe"

try {
    Write-Step "Step 1/4: Building Arch-Ive with PyInstaller..."
    & pyinstaller $specFile --noconfirm
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    Write-Step "Step 2/4: Verifying build output..."
    if (-not (Test-Path $exePath)) {
        throw "Expected executable not found: $exePath"
    }

    Write-Step "Step 3/4: Compiling Inno Setup installer..."
    $innoCandidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    $isccPath = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $isccPath) {
        throw "Inno Setup 6 compiler not found. Checked: $($innoCandidates -join ', ')"
    }

    & $isccPath $issFile
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
    }

    Write-Step "Step 4/4: Finalizing..."
    if (-not (Test-Path $installerOutput)) {
        throw "Installer was not created at expected path: $installerOutput"
    }

    Write-Success "Build completed successfully."
    Write-Success "Installer created at: installer/output/arch-ive-setup-v1.0.0.exe"
}
catch {
    Write-Failure $_.Exception.Message
    exit 1
}
