$ErrorActionPreference = 'Stop'
$workspacePath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
foreach ($directory in @('backend', 'src', 'tests', 'scripts')) {
    $scanPath = Join-Path $workspacePath $directory
    if (-not (Test-Path -LiteralPath $scanPath)) { continue }
    Get-ChildItem -LiteralPath $scanPath -Directory -Filter '__pycache__' -Recurse | ForEach-Object {
        $cachePath = [System.IO.Path]::GetFullPath($_.FullName)
        if (-not $cachePath.StartsWith($workspacePath + [System.IO.Path]::DirectorySeparatorChar)) {
            throw 'Refusing to clean a path outside the workspace'
        }
        Remove-Item -LiteralPath $cachePath -Recurse -Force
    }
}
