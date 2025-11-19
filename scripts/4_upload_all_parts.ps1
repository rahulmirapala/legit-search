# 4_upload_all_parts.ps1

# Define variables
$ES_URI = "http://localhost:9200/_bulk"
$DATA_PATH = "../data/bulk_parts"

Write-Host "Starting bulk upload of all parts..."

# Get all files matching the pattern bulk_part_*.jsonl, sorted numerically
$Files = Get-ChildItem -Path $DATA_PATH -Filter "bulk_part_*.jsonl" | Sort-Object { [int]($_ -split '_' -replace '\.jsonl$')[2] }

if ($Files.Count -eq 0) {
    Write-Host "Error: No bulk_part_*.jsonl files found in $DATA_PATH."
} else {
    Write-Host "Found $($Files.Count) files. Uploading..."
    foreach ($File in $Files) {
        $FilePath = $File.FullName
        $FileName = $File.Name
        Write-Host "  -> Uploading $FileName ..." -NoNewline
        
        # The core upload command using Invoke-WebRequest (aliased as curl)
        try {
            Invoke-WebRequest `
                -Uri $ES_URI `
                -Method POST `
                -ContentType "application/x-ndjson" `
                -InFile $FilePath `
                -ErrorAction Stop `
                -TimeOutSec 60
            
            # If successful, print confirmation
            Write-Host " Success." -ForegroundColor Green
        } catch {
            Write-Host " FAILED with error: $($_.Exception.Message)" -ForegroundColor Red
            # Break the loop on failure
            break
        }
    }
}
Write-Host "--- Upload Process Finished ---"