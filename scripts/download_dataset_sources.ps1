param(
    [string]$Destination = (Join-Path $PSScriptRoot "..\data\external"),
    [switch]$SkipOpenImagesMetadata
)

$ErrorActionPreference = "Stop"
$Destination = [System.IO.Path]::GetFullPath($Destination)

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-VerifiedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Sha256
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    if (Test-Path -LiteralPath $Path) {
        $actual = Get-Sha256 -Path $Path
        if ($actual -eq $Sha256.ToUpperInvariant()) {
            Write-Host "Verified existing file: $Path"
            return
        }
        throw "Checksum mismatch for existing file: $Path"
    }

    $partialPath = "$Path.part"
    if (Test-Path -LiteralPath $partialPath) {
        Remove-Item -LiteralPath $partialPath -Force
    }

    Write-Host "Downloading: $Url"
    & curl.exe --fail --location --retry 3 --silent --show-error --output $partialPath $Url
    if ($LASTEXITCODE -ne 0) {
        throw "Download failed with curl exit code $LASTEXITCODE`: $Url"
    }

    $actual = Get-Sha256 -Path $partialPath
    if ($actual -ne $Sha256.ToUpperInvariant()) {
        throw "Checksum mismatch after download: $partialPath"
    }
    Move-Item -LiteralPath $partialPath -Destination $Path
    Write-Host "Downloaded and verified: $Path"
}

$icubDownloads = Join-Path $Destination "icubworld\downloads"
$icubExtracted = Join-Path $Destination "icubworld\extracted"

$icubImages = Join-Path $icubDownloads "Sequences_images.tar.gz"
$icubAnnotations = Join-Path $icubDownloads "Sequences_annotations.tar.gz"

Get-VerifiedFile `
    -Url "https://zenodo.org/api/records/835510/files/Sequences_images.tar.gz/content" `
    -Path $icubImages `
    -Sha256 "834543A8F8A40E0974520628F506A0B5C67485F17025696ED878FCE977749343"

Get-VerifiedFile `
    -Url "https://zenodo.org/api/records/835510/files/Sequences_annotations.tar.gz/content" `
    -Path $icubAnnotations `
    -Sha256 "60F38FADDA2DF462FF05991A467A8DA324D6B2CF703CB8385976FA2F01E5C03D"

New-Item -ItemType Directory -Force -Path $icubExtracted | Out-Null
tar.exe -xzf $icubImages -C $icubExtracted
tar.exe -xzf $icubAnnotations -C $icubExtracted
Write-Host "Extracted iCubWorld subset to: $icubExtracted"

if (-not $SkipOpenImagesMetadata) {
    $oiMetadata = Join-Path $Destination "openimages\metadata"

    Get-VerifiedFile `
        -Url "https://storage.googleapis.com/openimages/v7/oidv7-class-descriptions-boxable.csv" `
        -Path (Join-Path $oiMetadata "oidv7-class-descriptions-boxable.csv") `
        -Sha256 "1839E0E7E84130AE281F7F67413768601B031581C0C42E7FC17527B8E2A99AA9"

    Get-VerifiedFile `
        -Url "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv" `
        -Path (Join-Path $oiMetadata "validation-annotations-bbox.csv") `
        -Sha256 "D8BBD59410AF14835D7733165A7BB8A3F0213981B22DD5077B0B9F7878991FF2"
}

$fpiDestination = Join-Path $Destination "fpi_det\downloads"
New-Item -ItemType Directory -Force -Path $fpiDestination | Out-Null

Write-Host ""
Write-Host "Automatic downloads complete."
Write-Host "FPI-Det requires a signed-in manual download from:"
Write-Host "https://drive.google.com/file/d/1Heb2N4hRcJH2s9tLdpTzacSj0APbUDdD/view?usp=sharing"
Write-Host "Save the original archive under: $fpiDestination"
