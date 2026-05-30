# Build the DivisorWavePlotter C# project
# Run from c-sharp-graphics/ folder:
#   .\build.ps1
# Or from project root:
#   .\c-sharp-graphics\build.ps1

$proj = "$PSScriptRoot\DivisorWavePlotter\DivisorWavePlotter.csproj"

Write-Host "Building DivisorWavePlotter (Release, win-x64)..." -ForegroundColor Cyan
dotnet publish $proj -c Release -r win-x64 --self-contained false

if ($LASTEXITCODE -eq 0) {
    $exe = "$PSScriptRoot\DivisorWavePlotter\bin\Release\net8.0-windows\win-x64\DivisorWavePlotter.exe"
    Write-Host "`nBuild succeeded!" -ForegroundColor Green
    Write-Host "Executable: $exe" -ForegroundColor Gray
    Write-Host "`nTo test standalone (no Electron embedding):" -ForegroundColor Yellow
    Write-Host "  & `"$exe`"" -ForegroundColor Gray
} else {
    Write-Host "`nBuild FAILED (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
