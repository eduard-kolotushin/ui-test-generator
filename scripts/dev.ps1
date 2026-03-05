param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Args
)

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $parts = $_ -split '=', 2
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if ($name) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

if ($Args -contains "--no-browser") {
    uv run langgraph dev @Args
} else {
    uv run langgraph dev --no-browser @Args
}

