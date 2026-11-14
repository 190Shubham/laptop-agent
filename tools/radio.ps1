param([string]$Kind, [string]$State)
$ErrorActionPreference = 'Stop'
try {
  Add-Type -AssemblyName System.Runtime.WindowsRuntime
  [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
  [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
  [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
  $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
  function Await($task, $type) {
    $t = $asTask.MakeGenericMethod($type).Invoke($null, @($task))
    $t.Wait(-1) | Out-Null
    $t.Result
  }
  $null = Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
  $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
  $radio = $radios | Where-Object { "$($_.Kind)" -eq $Kind } | Select-Object -First 1
  if (-not $radio) { Write-Output 'NOT_FOUND'; exit 0 }
  $result = Await ($radio.SetStateAsync($State)) ([Windows.Devices.Radios.RadioAccessStatus])
  Write-Output "$result"
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
}