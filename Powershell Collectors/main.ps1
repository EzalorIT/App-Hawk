param (
    [string] $outputPath = "D:\Work\AppHawk\Test\CollectorsData"
)

function Invoke-SequentialExecution {
    param ([string]$OutputPath)

    if (-not (Test-Path -Path $OutputPath)) {
        New-Item -Path $OutputPath -ItemType Directory | Out-Null
    }
    
    $dateString = (Get-Date).ToString('yyyyMMdd')
    $hostname = $env:COMPUTERNAME
    
    function Get-ApplicationEvents {
        $startTime = (Get-Date).AddMinutes(-15)

        # Retrieve the latest 1000 events from the Application log within the time range
        $events = Get-WinEvent -LogName Application -MaxEvents 1000 | Where-Object { $_.TimeCreated -ge $startTime }
    
        $eventData = @()
    
        foreach ($event in $events) {
            $message = $event.Message
    
            if ($message) {
                # Extract details using refined regex patterns
                $productName = if ($message -match 'Product Name:\s*([^\r\n]+)') { $matches[1] -replace '^.*?:\s*', '' -replace '\s*$', '' } else { $null }
                $version = if ($message -match 'Product Version:\s*([\d\.]+)') { $matches[1] } else { $null }
                $deliveryMechanism = if ($message -match 'Delivery Mechanism:\s*([^\r\n]+)') { $matches[1] -replace '^.*?:\s*', '' -replace '\s*$', '' } else { $null }
    
                # Only add entries that have at least one valid field
                if ($productName -or $version -or $deliveryMechanism) {
                    $eventData += [PSCustomObject]@{
                        Name = $productName
                        Version = $version
                        DeliveryMechanism = $deliveryMechanism
                    }
                }
            }
        }
    
        return $eventData
    }
    
    

    function Get-InstalledAppsRegistry {
        $registryPath = "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        $installedApps = @()
        foreach ($hive in @('HKLM', 'HKCU')) {
            try {
                Get-ChildItem -Path "Registry::$hive\$registryPath" -Recurse | ForEach-Object {
                    try {
                        $app = Get-ItemProperty -Path $_.PSPath | Select-Object -Property DisplayName, DisplayVersion, InstallSource
                        if ($app.DisplayName) {
                            $deliveryMechanism = if ($app.InstallSource) {"Manual"} else {"App Provider"}
                            $installedApps += [PSCustomObject]@{ Name = $app.DisplayName; Version = $app.DisplayVersion; DeliveryMechanism = $deliveryMechanism }
                        }
                    } catch {}
                }
            } catch {}
        }
        return $installedApps
    }

    function Get-InstalledAppsWMI {
        $installedApps = @()

        # Fetch apps installed via Windows Installer (MSI)
        $msiApps = Get-WmiObject -Query "SELECT * FROM Win32_Product" |
            Select-Object Name, Version, @{Name="DeliveryMechanism"; Expression={"MSI (Windows Installer)"}}
        $installedApps += $msiApps
    
        # Fetch apps installed via Microsoft Store (AppX/MSIX)
        $appxApps = Get-AppxPackage |
            Select-Object Name, Version, @{Name="DeliveryMechanism"; Expression={"MSIX/AppX (Microsoft Store)"}}
        $installedApps += $appxApps
    
        # Fetch registry-based installed applications (EXE-based or other installers)
        $regPaths = @(
            "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
        )
        
        foreach ($path in $regPaths) {
            if (Test-Path $path) {
                $regApps = Get-ItemProperty $path |
                    Select-Object DisplayName, DisplayVersion, @{Name="DeliveryMechanism"; Expression={"EXE (Registry-based Installation)"}}
                $installedApps += $regApps
            }
        }
    
        return $installedApps | Sort-Object Name
    }
    
    function Get-InstalledAppsWinget {
        $installedApps = @()
        try {
            $output = winget list | Select-String "^(.+?)\s+([0-9]+(\.[0-9]+)*)"
            foreach ($line in $output) {
                $match = $line -match "^(.+?)\s+([0-9]+(\.[0-9]+)*)"
                if ($match) {
                    $installedApps += [PSCustomObject]@{ Name = $matches[1].Trim(); Version = $matches[2]; DeliveryMechanism = "Winget" }
                }
            }
        } catch {}
        return $installedApps
    }
    
    function Get-RunningProcesses {
        $processList = Get-Process | Select-Object ProcessName, Id, Path |
        ForEach-Object {
            try {
                $version = "Unknown"
                if ($_.Path) {
                    $version = (Get-Item $_.Path).VersionInfo.FileVersion
                }
                [PSCustomObject]@{ Name = $_.ProcessName; Version = $version; DeliveryMechanism = "NA" }
            } catch {}
        }
        return $processList
    }

    function Append-ChangedData {
        param ([string]$FilePath, [array]$NewData, [string[]]$UniqueFields)
        $existingDataSet = @{ }
        if (Test-Path $FilePath) {
            Import-Csv -Path $FilePath | ForEach-Object {
                $key = ($UniqueFields | ForEach-Object { $_ + $_.($_) }) -join "_"
                $existingDataSet[$key] = $true
            }
        }
        $newRows = $NewData | Where-Object {
            $key = ($UniqueFields | ForEach-Object { $_ + $_.($_) }) -join "_"
            -not $existingDataSet.ContainsKey($key)
        }
        if ($newRows.Count -gt 0) {
            $newRows | Export-Csv -Path $FilePath -NoTypeInformation -Append
        }
    }

    $events = Get-ApplicationEvents
    $installedAppsRegistry = Get-InstalledAppsRegistry
    $installedAppsWMI = Get-InstalledAppsWMI
    $installedAppsWinget = Get-InstalledAppsWinget
    $runningProcesses = Get-RunningProcesses
    
    Append-ChangedData "$OutputPath\$hostname`_ApplicationEvents.csv" $events @("Name", "Version")
    Append-ChangedData "$OutputPath\$hostname`_InstalledAppsRegistry.csv" $installedAppsRegistry @("Name", "Version")
    Append-ChangedData "$OutputPath\$hostname`_InstalledAppsWMI.csv" $installedAppsWMI @("Name", "Version")
    Append-ChangedData "$OutputPath\$hostname`_InstalledAppsWinget.csv" $installedAppsWinget @("Name", "Version")
    Append-ChangedData "$OutputPath\$hostname`_RunningProcesses.csv" $runningProcesses @("Name", "Version")
}

Invoke-SequentialExecution -OutputPath $outputPath
