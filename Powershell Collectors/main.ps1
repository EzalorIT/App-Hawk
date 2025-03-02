param (
    [string] $outputPath = "D:\Work\AppHawk\Test\CollectorsData"
)

function Invoke-SequentialExecution {
    param (
        [string]$OutputPath
    )

    if (-not (Test-Path -Path $OutputPath)) {
        Write-Host "Output path does not exist. Creating directory at $OutputPath"
        New-Item -Path $OutputPath -ItemType Directory
    }
    
    $dateString = (Get-Date).ToString('ddMMyyyy')
    $hostname = $env:COMPUTERNAME
    
    function Extract-ApplicationEvents {

        param ([string]$LogType = 'Application')
        Write-Host "Starting Extract-ApplicationEvents function to extract logs from $LogType log..."        
        $events = Get-WinEvent -LogName $LogType | Where-Object { $_.TimeCreated -gt (Get-Date).AddDays(-1) }
        Write-Host "Completed Extract-ApplicationEvents function with $($events.Count) events retrieved."
        
        return $events
    }
    
    function Get-InstalledAppsRegistry {
        Write-Host "Starting Get-InstalledAppsRegistry function to retrieve installed applications from the Windows registry..."
        $registryPath = "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        $installedApps = @()
        $hives = @('HKLM', 'HKCU')

        foreach ($hive in $hives) {
            try {
                $keyPath = "$hive\$registryPath"
                $keys = Get-ChildItem -Path "Registry::$keyPath" -Recurse
                foreach ($key in $keys) {
                    try {
                        $appName = (Get-ItemProperty -Path $key.PSPath).DisplayName
                        $appVersion = (Get-ItemProperty -Path $key.PSPath).DisplayVersion
                        $installedApps += [PSCustomObject]@{ Name = $appName; Version = $appVersion; DeliveryMechanism = "App Provider" }
                    } 
                    catch {
                        continue
                    }
                }
            } 
            catch {
                continue
            }
        }

        Write-Host "Completed Get-InstalledAppsRegistry function with $($installedApps.Count) applications retrieved."
        return $installedApps
    }

    
    function Get-InstalledAppsWMI {
        Write-Host "Starting Get-InstalledAppsWMI function to retrieve installed applications using WMI..."

        $installedApps = @()
        $wmiQuery = "SELECT * FROM Win32_Product"
        $products = Get-WmiObject -Query $wmiQuery

        foreach ($product in $products) {
            try {
                $installedApps += [PSCustomObject]@{
                    Name = $product.Name
                    Version = $product.Version
                    Manufacturer = $product.Manufacturer
                    DeliveryMechanism = "App Provider"
                }
            } 
            catch 
            {
                continue
            }
        }

        Write-Host "Completed Get-InstalledAppsWMI function with $($installedApps.Count) applications retrieved."
        return $installedApps
    }

    
    function Get-InstalledAppsWinget {
        Write-Host "Starting Get-InstalledAppsWinget function to retrieve installed applications via WinGet..."

        $installedApps = @()
        try {    
            $output = winget list
            $lines = $output -split "`r`n"
            
            foreach ($line in $lines[3..$lines.Length]) {
                $appInfo = $line -split '\s+'
                if ($appInfo.Length -ge 2) {
                    $installedApps += [PSCustomObject]@{ Name = $appInfo[0]; Version = $appInfo[1]; DeliveryMechanism = "WinGet" }
                }
            }
        } 
        catch {
            Write-Host "Error running WinGet: $_"
        }

        Write-Host "Completed Get-InstalledAppsWinget function with $($installedApps.Count) applications retrieved."
        return $installedApps
    }

    

    function Append-ChangedData {
        param (
            [string]$FilePath,
            [array]$NewData,
            [string[]]$UniqueFields
        )

        $existingDataSet = @{}
        
        if (Test-Path $FilePath) {            
            $existingData = Import-Csv -Path $FilePath

            foreach ($row in $existingData) {                
                $key = ""
                foreach ($field in $UniqueFields) {
                    $key += [string]$row.$field + "_"
                }         

                $key = $key.TrimEnd('_')
                $existingDataSet[$key] = $true
            }

            Write-Host "Loaded existing data. Found $($existingDataSet.Count) unique entries in $FilePath."
        } else {
            Write-Host "File $FilePath does not exist, creating new file."
        }
        
        $newRows = @()
        foreach ($row in $NewData) {
            $key = ""
            foreach ($field in $UniqueFields) {
                $key += [string]$row.$field + "_"
            }        
            $key = $key.TrimEnd('_')

            if (-not $existingDataSet.ContainsKey($key)) {
                $newRows += $row
            }
        }

        if ($newRows.Count -gt 0) {
            $newRows | Export-Csv -Path $FilePath -NoTypeInformation -Append
            Write-Host "$($newRows.Count) new rows appended to $FilePath"
        } 
        else 
        {
            Write-Host "No new data to append to $FilePath"
        }
    }


    Write-Host "Starting sequential execution..."

    $events = Extract-ApplicationEvents
    $installedAppsRegistry = Get-InstalledAppsRegistry
    $installedAppsWMI = Get-InstalledAppsWMI
    $installedAppsWinget = Get-InstalledAppsWinget

    if (-not (Test-Path -Path $OutputPath)) {
        Write-Host "Output path does not exist. Creating directory at $OutputPath"
        New-Item -Path $OutputPath -ItemType Directory
    }

    $eventsFilePath = "$OutputPath\$hostname`_ApplicationEvents_$dateString.csv"
    $installedAppsRegistryFilePath = "$OutputPath\$hostname`_InstalledAppsRegistry_$dateString.csv"
    $installedAppsWMIFilePath = "$OutputPath\$hostname`_InstalledAppsWMI_$dateString.csv"
    $installedAppsWingetFilePath = "$OutputPath\$hostname`_InstalledAppsWinget_$dateString.csv"

    $uniqueFields = @('Name', 'Version')

    Append-ChangedData -FilePath $eventsFilePath -NewData $events -UniqueFields $uniqueFields
    Append-ChangedData -FilePath $installedAppsRegistryFilePath -NewData $installedAppsRegistry -UniqueFields $uniqueFields
    Append-ChangedData -FilePath $installedAppsWMIFilePath -NewData $installedAppsWMI -UniqueFields $uniqueFields
    Append-ChangedData -FilePath $installedAppsWingetFilePath -NewData $installedAppsWinget -UniqueFields $uniqueFields
}

Invoke-SequentialExecution -OutputPath $outputPath
