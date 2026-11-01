#requires -Version 5.1
# OPS-010 isolated Windows-hosted CI test: no media, no network, no user PC.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\scripts\private_output_acl.ps1')
$testRoot = Join-Path $env:RUNNER_TEMP ("ops010-ntfs-" + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $testRoot -ErrorAction Stop
try {
    $private = Join-Path $testRoot 'private'
    $secured = Initialize-PrivateWindowsDirectory -Path $private
    if ($secured -ne $private) { throw 'Unexpected directory returned.' }
    Assert-PrivateWindowsAcl -Path $private
    $owner = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $identities = @((Get-Acl -LiteralPath $private).Access |
        ForEach-Object { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value })
    foreach ($sid in $identities) {
        if ($sid -notin @($owner, 'S-1-5-18')) { throw "Unexpected ACL SID: $sid" }
    }
    # File inherits the private destination ACL, exercising the copy-security invariant.
    $file = Join-Path $private 'test.bin'
    [IO.File]::WriteAllBytes($file, [byte[]](1,2,3,4))
    Assert-PrivateWindowsAcl -Path $file -AllowInheritedChild
    $null = Initialize-PrivateWindowsDirectory -Path $private

    # An existing folder with explicit Everyone read must fail, without rewriting it.
    $permissive = Join-Path $testRoot 'permissive'
    $null = New-Item -ItemType Directory -Path $permissive
    $bad = Get-Acl -LiteralPath $permissive
    $bad.SetAccessRuleProtection($true, $false)
    # Preserve owner full control so the deliberately unsafe fixture can be cleaned
    # up without requiring elevated permissions on the disposable CI runner.
    $current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $ownerRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $current,
        [System.Security.AccessControl.FileSystemRights]::FullControl,
        [System.Security.AccessControl.InheritanceFlags]::None,
        [System.Security.AccessControl.PropagationFlags]::None,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    $bad.AddAccessRule($ownerRule)
    $world = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')
    $worldRead = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $world,
        [System.Security.AccessControl.FileSystemRights]::ReadAndExecute,
        [System.Security.AccessControl.InheritanceFlags]::None,
        [System.Security.AccessControl.PropagationFlags]::None,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    $bad.AddAccessRule($worldRead)
    Set-Acl -LiteralPath $permissive -AclObject $bad
    $rejected = $false
    try { $null = Initialize-PrivateWindowsDirectory -Path $permissive }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $rejected = $true } else { throw } }
    if (-not $rejected) { throw 'An insecure existing directory was accepted.' }
    $stillWorld = @((Get-Acl -LiteralPath $permissive).Access |
        ForEach-Object { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value }) -contains 'S-1-1-0'
    if (-not $stillWorld) { throw 'Existing insecure directory ACL was mutated.' }

    $uncRejected = $false
    try { $null = Initialize-PrivateWindowsDirectory -Path '\\example.invalid\share\media' }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $uncRejected = $true } else { throw } }
    if (-not $uncRejected) { throw 'UNC path was accepted.' }
    Write-Output 'WINDOWS_NTFS_ACL_TESTS_OK: private directory + inherited file + fail closed + UNC rejection'
}
finally {
    # Only remove isolated, freshly created data on the disposable GitHub runner.
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -LiteralPath $testRoot -Recurse -Force }
}
