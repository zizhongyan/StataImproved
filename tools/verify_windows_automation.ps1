<#
.SYNOPSIS
  Checks how Stata Automation behaves on this computer; the Windows backend
  of Stata Improved Editor depends on the answers.

.DESCRIPTION
  Run after registering Stata once from an administrator prompt, e.g.
      & "C:\Program Files\Stata18\StataMP-64.exe" /Register
  Close all Stata windows first, then run (as a normal user):
      powershell -ExecutionPolicy Bypass -File tools\verify_windows_automation.ps1

  It answers:
    1. Does creating the Automation object start Stata, and do DoCommand /
       DoCommandAsync with a quoted do-file path work?
    2. Does a Stata started by Automation keep running when the object is
       released (plugin reload / Sublime Text exit)?
    3. Does a new object attach to a Stata the user opened, or start another?
    4. Does the Stata the user opened keep running when the object is released?
  Stata instances started by this script are closed at the end.
#>
param([string]$ProgId = "stata.StataOLEApp")

$ErrorActionPreference = "Stop"

function Get-StataIds { @(Get-Process | Where-Object { $_.Name -match '^Stata' } | ForEach-Object Id) }

function Release-Com($object) {
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($object)
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}

function Wait-Free($stata) {
    for ($i = 0; $i -lt 60 -and -not $stata.UtilIsStataFree(); $i++) { Start-Sleep -Milliseconds 500 }
}

$clsid = (Get-ItemProperty "Registry::HKEY_CLASSES_ROOT\$ProgId\CLSID" -ErrorAction SilentlyContinue).'(default)'
if (-not $clsid) {
    Write-Host "Stata Automation ($ProgId) is not registered. Run StataXX.exe /Register as administrator first." -ForegroundColor Red
    exit 1
}
$server = (Get-ItemProperty "Registry::HKEY_CLASSES_ROOT\CLSID\$clsid\LocalServer32").'(default)'
Write-Host "Registered server: $server"
$executable = ($server -replace '^"([^"]+)".*$', '$1') -replace '\s+/.*$', ''

$before = Get-StataIds
if ($before.Count -gt 0) {
    Write-Host "Please close all Stata windows first ($($before.Count) running)." -ForegroundColor Yellow
    exit 1
}
$started = @()
$answers = [ordered]@{}

# 1. Create -> starts Stata? Commands work?
$stata = New-Object -ComObject $ProgId
Start-Sleep -Seconds 3
$afterCreate = Get-StataIds
$started += $afterCreate
$answers["1a. Creating the object starts Stata"] = ($afterCreate.Count -eq 1)
$answers["1b. DoCommand returns 0"] = ($stata.DoCommand('global SI_VERIFY "sync"') -eq 0)

$dir = Join-Path $env:TEMP "StataImproved"
New-Item -ItemType Directory -Force $dir | Out-Null
$doFile = Join-Path $dir "verify automation.do"   # a space, like many user names
[IO.File]::WriteAllText($doFile, "global SI_VERIFY `"async`"`n")
[void]$stata.DoCommandAsync("do `"$($doFile -replace '\\', '/')`"")
Start-Sleep -Seconds 1
Wait-Free $stata
# DoCommand does not expand macros, so read the result with MacroValue.
$answers["1c. DoCommandAsync ran the quoted do-file"] = ($stata.MacroValue("SI_VERIFY") -eq "async")

# 2. Release -> does a Stata started by Automation keep running?
Release-Com $stata
Start-Sleep -Seconds 5
$answers["2.  A Stata started by Automation keeps running after release"] = ((Get-StataIds).Count -eq 1)

# 3. Stata opened by the user -> does a new object attach to it?
Get-StataIds | ForEach-Object { Stop-Process -Id $_ -Force }
Start-Sleep -Seconds 2
Start-Process -FilePath $executable
Start-Sleep -Seconds 10
$userStata = Get-StataIds
$started += $userStata
$stata = New-Object -ComObject $ProgId
Start-Sleep -Seconds 5
$afterAttach = Get-StataIds
$started += $afterAttach
$answers["3.  A new object attaches to the Stata the user opened (no 2nd instance)"] = ($afterAttach.Count -eq $userStata.Count)
[void]$stata.DoCommand('global SI_VERIFY "attached"')

# 4. Release -> does the user's Stata keep running?
Release-Com $stata
Start-Sleep -Seconds 5
$answers["4.  The Stata the user opened keeps running after release"] = ((Get-StataIds).Count -eq $userStata.Count)

Write-Host ""
foreach ($k in $answers.Keys) {
    $v = $answers[$k]
    Write-Host ("{0,-75} {1}" -f $k, $(if ($v) { "YES" } else { "NO" })) -ForegroundColor $(if ($v) { "Green" } else { "Yellow" })
}

$started | Sort-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Remove-Item $doFile -ErrorAction SilentlyContinue
