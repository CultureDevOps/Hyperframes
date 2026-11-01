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

    # No real video: a fake .mp4 verifies byte integrity, NTFS destination
    # inheritance, no-overwrite, and failed-copy cleanup on hosted Windows.
    $source = Join-Path $testRoot 'fake-mp4-source.mp4'
    $bytes = [byte[]](1,2,3,7,13,21,34,55,89)
    [IO.File]::WriteAllBytes($source, $bytes)
    $final = Join-Path $private 'fake-final.mp4'
    $result = Copy-PrivateWindowsMedia -Source $source -Destination $final
    if ($result -ne $final) { throw 'Unexpected final media destination.' }
    Assert-PrivateWindowsAcl -Path $final -AllowInheritedChild
    $expected = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $final -Algorithm SHA256).Hash -ne $expected) {
        throw 'Copied media bytes differ.'
    }
    if (@(Get-ChildItem -LiteralPath $private -Filter '*.partial').Count -ne 0) {
        throw 'Partial copy remained after successful promotion.'
    }
    # The final file must never be silently overwritten or deleted.
    $rejectedExisting = $false
    try { $null = Copy-PrivateWindowsMedia -Source $source -Destination $final }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $rejectedExisting = $true } else { throw } }
    if (-not $rejectedExisting) { throw 'Existing final was overwritten.' }
    if ((Get-FileHash -LiteralPath $final -Algorithm SHA256).Hash -ne $expected) {
        throw 'Existing final changed after failed copy.'
    }
    # Wrong expected digest forces a failure AFTER the temporary file is copied.
    $mismatch = Join-Path $private 'failed-hash.mp4'
    $rejectedHash = $false
    try {
        $null = Copy-PrivateWindowsMedia -Source $source -Destination $mismatch -ExpectedSha256 ('0' * 64)
    } catch {
        if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $rejectedHash = $true } else { throw }
    }
    if (-not $rejectedHash) { throw 'Expected SHA256 mismatch was accepted.' }
    if (Test-Path -LiteralPath $mismatch) { throw 'Failed hash copy left final media.' }
    if (@(Get-ChildItem -LiteralPath $private -Filter '*.partial').Count -ne 0) {
        throw 'Failed hash copy left private partial files.'
    }
    # Missing source must fail before touching the target directory.
    $missing = Join-Path $testRoot 'missing-source.mp4'
    $missingTarget = Join-Path $private 'missing-target.mp4'
    $rejectedMissing = $false
    try { $null = Copy-PrivateWindowsMedia -Source $missing -Destination $missingTarget }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $rejectedMissing = $true } else { throw } }
    if (-not $rejectedMissing -or (Test-Path -LiteralPath $missingTarget)) {
        throw 'Missing source did not fail cleanly.'
    }

    # A real locked source triggers a filesystem IOException. No destination
    # or new partial must appear, and the lock must be released by the test.
    $lockedSource = Join-Path $testRoot 'locked-source.mp4'
    [IO.File]::WriteAllBytes($lockedSource, $bytes)
    $lockedDest = Join-Path $private 'locked-dest.mp4'
    $stream = [IO.File]::Open($lockedSource, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $lockedRejected = $false
    try {
        try { $null = Copy-PrivateWindowsMedia -Source $lockedSource -Destination $lockedDest }
        catch {
            # PowerShell 5.1 wraps .NET File.Copy IOException as
            # MethodInvocationException; PowerShell 7 can differ.
            $outer = $_.Exception
            if (($outer -is [System.IO.IOException]) -or
                ($outer.InnerException -is [System.IO.IOException])) {
                $lockedRejected = $true
            } else {
                throw
            }
        }
    } finally {
        $stream.Dispose()
    }
    if (-not $lockedRejected -or (Test-Path -LiteralPath $lockedDest)) {
        throw 'Locked source was not rejected safely.'
    }
    if (@(Get-ChildItem -LiteralPath $private -Filter '*.partial').Count -ne 0) {
        throw 'Locked-source failure left an OPS-010 partial.'
    }

    # Simulated hard termination: create a stale partial that PowerShell's
    # finally could NOT clean up. The read-only inspector must report only
    # a sufficiently old, correctly named file; must NOT remove anything.
    $staleName = '.ops010-copy-' + [Guid]::NewGuid().ToString('N') + '.partial'
    $stale = Join-Path $private $staleName
    [IO.File]::WriteAllBytes($stale, [byte[]](9,8,7))
    [IO.File]::SetLastWriteTimeUtc($stale, [DateTime]::UtcNow.AddHours(-3))
    $recent = Join-Path $private ('.ops010-copy-' + [Guid]::NewGuid().ToString('N') + '.partial')
    [IO.File]::WriteAllBytes($recent, [byte[]](1))
    $unrelated = Join-Path $private '.ops010-copy-user-file.partial'
    [IO.File]::WriteAllBytes($unrelated, [byte[]](6))
    [IO.File]::SetLastWriteTimeUtc($unrelated, [DateTime]::UtcNow.AddHours(-3))
    $reported = @(Get-PrivateWindowsInterruptedCopies -Directory $private -MinimumAgeMinutes 60)
    if ($reported.Count -ne 1 -or $reported[0] -ne $stale) {
        throw 'Interrupted-copy inspector selected incorrect files.'
    }
    foreach ($path in @($stale, $recent, $unrelated)) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw 'Read-only orphan inspection deleted a file.'
        }
    }
    # Existing, older orphan must not be touched by another successful copy.
    $anotherFinal = Join-Path $private 'after-interruption.mp4'
    $null = Copy-PrivateWindowsMedia -Source $source -Destination $anotherFinal
    if (-not (Test-Path -LiteralPath $stale)) {
        throw 'A newer copy removed an unrelated interrupted copy.'
    }
    # Simulated stop is test-only; clean only the exact synthetic fixtures.
    foreach ($path in @($stale, $recent, $unrelated)) {
        Remove-Item -LiteralPath $path -Force -ErrorAction Stop
    }

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
    $permissiveTarget = Join-Path $permissive 'should-not-exist.mp4'
    $rejectedPermissiveCopy = $false
    try { $null = Copy-PrivateWindowsMedia -Source $source -Destination $permissiveTarget }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $rejectedPermissiveCopy = $true } else { throw } }
    if (-not $rejectedPermissiveCopy -or (Test-Path -LiteralPath $permissiveTarget)) {
        throw 'Copy wrote into an insecure existing directory.'
    }

    $uncRejected = $false
    try { $null = Initialize-PrivateWindowsDirectory -Path '\\example.invalid\share\media' }
    catch { if ($_.Exception.Message -like '*NTFS_UNSAFE*') { $uncRejected = $true } else { throw } }
    if (-not $uncRejected) { throw 'UNC path was accepted.' }
    Write-Output 'WINDOWS_NTFS_ACL_TESTS_OK: fake copy/hash + locked source + stale interruption audit + no overwrite + failure cleanup + ACL/UNC refusal'
}
finally {
    # Only remove isolated, freshly created data on the disposable GitHub runner.
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -LiteralPath $testRoot -Recurse -Force }
}
