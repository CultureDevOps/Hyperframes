#requires -Version 5.1
<#
  OPS-010: fail-closed private NTFS directory ACL for local rendering.
  Only called on Windows; never relax an existing directory's ACL.
  Local fixed-volume NTFS only. No network share or publishing.
#>
Set-StrictMode -Version Latest

function Assert-PrivateWindowsAcl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [switch]$AllowInheritedChild
    )
    $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $systemSid = 'S-1-5-18'
    $allowedSids = @($currentSid, $systemSid)
    $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop
    if (-not $AllowInheritedChild -and -not $acl.AreAccessRulesProtected) {
        throw "NTFS_UNSAFE: inherited ACLs on '$Path'. Use a fresh private directory; existing ACLs will NOT be modified."
    }
    $currentHasFullControl = $false
    foreach ($rule in $acl.Access) {
        $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
        if ($sid -notin $allowedSids -or
            $rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) {
            throw "NTFS_UNSAFE: unapproved ACE ($sid) on '$Path'. Existing ACLs are not modified."
        }
        if ($sid -eq $currentSid -and
            (($rule.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -eq
                [System.Security.AccessControl.FileSystemRights]::FullControl)) {
            $currentHasFullControl = $true
        }
    }
    if (-not $currentHasFullControl) { throw "NTFS_UNSAFE: current user lacks full control on '$Path'." }
}

function Initialize-PrivateWindowsDirectory {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)

    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'NTFS ACL configuration can only run on Windows.'
    }
    $full = [IO.Path]::GetFullPath($Path)
    if ($full.StartsWith('\\')) {
        throw 'NTFS_UNSAFE: UNC/device paths are not allowed for private media.'
    }
    $root = [IO.Path]::GetPathRoot($full)
    $drive = New-Object System.IO.DriveInfo($root)
    if ($drive.DriveType -ne [IO.DriveType]::Fixed -or $drive.DriveFormat -ne 'NTFS') {
        throw "NTFS_UNSAFE: output must be on a fixed local NTFS volume ($root)."
    }

    # Reject existing reparse-point ancestors (junctions, symlinks, cloud redirections).
    $cursor = $full
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "NTFS_UNSAFE: reparse point in output path '$cursor'."
            }
        }
        $parent = Split-Path -Path $cursor -Parent
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }

    if (Test-Path -LiteralPath $full) {
        if (-not (Test-Path -LiteralPath $full -PathType Container)) {
            throw "NTFS_UNSAFE: output is not a directory: $full"
        }
        Assert-PrivateWindowsAcl -Path $full
        return $full
    }
    $parentDir = Split-Path -Path $full -Parent
    if (-not (Test-Path -LiteralPath $parentDir -PathType Container)) {
        throw "NTFS_UNSAFE: parent must already exist: $parentDir"
    }
    # Create only the requested leaf directory; do not modify parent ACLs.
    $null = New-Item -ItemType Directory -Path $full -ErrorAction Stop
    $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $systemSid = New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18')
    $acl = Get-Acl -LiteralPath $full -ErrorAction Stop
    $acl.SetAccessRuleProtection($true, $false)
    # Freshly created Windows directories can carry explicit Administrators or
    # Users ACEs even after inherited rules are removed. Strip ALL these
    # inherited-by-template explicit entries only on this newly created leaf.
    foreach ($oldRule in @($acl.Access)) {
        $acl.RemoveAccessRuleSpecific($oldRule)
    }
    foreach ($sid in @($currentSid, $systemSid)) {
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $sid,
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            ([System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
             [System.Security.AccessControl.InheritanceFlags]::ObjectInherit),
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow
        )
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $full -AclObject $acl -ErrorAction Stop
    Assert-PrivateWindowsAcl -Path $full
    return $full
}

function Copy-PrivateWindowsMedia {
    <#
      Copy a local file into a protected NTFS folder with a disposable file in
      the destination folder. Only after SHA-256 and ACL verification is it
      atomically renamed to its final filename. A pre-existing final is NEVER
      overwritten or removed, even when a copy/check fails.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination,
        [ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedSha256 = ''
    )
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'NTFS_UNSAFE: private media copy requires Windows.'
    }
    $sourceFull = [IO.Path]::GetFullPath($Source)
    $finalFull = [IO.Path]::GetFullPath($Destination)
    if (-not (Test-Path -LiteralPath $sourceFull -PathType Leaf)) {
        throw "NTFS_UNSAFE: source is absent or not a file: $sourceFull"
    }
    $sourceItem = Get-Item -LiteralPath $sourceFull -Force
    if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'NTFS_UNSAFE: source cannot be a reparse point.'
    }
    $destinationDir = Split-Path -Path $finalFull -Parent
    $null = Initialize-PrivateWindowsDirectory -Path $destinationDir
    if (Test-Path -LiteralPath $finalFull) {
        throw "NTFS_UNSAFE: final destination already exists; never overwrite: $finalFull"
    }
    $stage = Join-Path $destinationDir ('.ops010-copy-' + [Guid]::NewGuid().ToString('N') + '.partial')
    $published = $false
    $primaryError = $null
    try {
        # Copy INSIDE the private directory; the partial file inherits private
        # ACLs, rather than retaining the permissions of the raw render.
        [IO.File]::Copy($sourceFull, $stage, $false)
        Assert-PrivateWindowsAcl -Path $stage -AllowInheritedChild

        $sourceHash = (Get-FileHash -LiteralPath $sourceFull -Algorithm SHA256 -ErrorAction Stop).Hash
        $stageHash = (Get-FileHash -LiteralPath $stage -Algorithm SHA256 -ErrorAction Stop).Hash
        if ($sourceHash -ne $stageHash) {
            throw 'NTFS_UNSAFE: copied bytes differ from source SHA256.'
        }
        if ($ExpectedSha256 -and $stageHash -ne $ExpectedSha256.ToUpperInvariant()) {
            throw 'NTFS_UNSAFE: copied bytes differ from expected SHA256.'
        }
        # File.Move (without overwrite) fails if another writer creates the
        # final path after the pre-check. Preserve that pre-existing file.
        [IO.File]::Move($stage, $finalFull)
        $published = $true
        Assert-PrivateWindowsAcl -Path $finalFull -AllowInheritedChild
    } catch {
        $primaryError = $_
        # Only a final created by THIS invocation may be rolled back. Never
        # delete a pre-existing final. Preserve the first failure for diagnosis.
        if ($published -and [IO.File]::Exists($finalFull)) {
            try {
                Remove-Item -LiteralPath $finalFull -Force -ErrorAction Stop
            } catch {
                Write-Warning 'NTFS_CLEANUP_INCOMPLETE: unable to roll back newly created private final file.'
            }
        }
    } finally {
        if ([IO.File]::Exists($stage)) {
            try {
                Remove-Item -LiteralPath $stage -Force -ErrorAction Stop
            } catch {
                if ($null -eq $primaryError) {
                    $primaryError = $_
                } else {
                    Write-Warning 'NTFS_CLEANUP_INCOMPLETE: private partial remains after failure; review locally.'
                }
            }
        }
    }
    if ($null -ne $primaryError) { throw $primaryError }
    return $finalFull
}


function Get-PrivateWindowsInterruptedCopies {
    <#
      READ ONLY: candidate orphan partials after an abrupt process termination.
      Exact OPS-010 32-hex GUID filenames; excludes active/recent copies. The
      caller must review them manually. Never auto-delete another invocation's
      partial files; a force-kill cannot execute PowerShell finally.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Directory,
        [ValidateRange(1,525600)][int]$MinimumAgeMinutes = 60
    )
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'NTFS_UNSAFE: interrupted-copy inspection requires Windows.'
    }
    $full = [IO.Path]::GetFullPath($Directory)
    $null = Initialize-PrivateWindowsDirectory -Path $full
    $threshold = [DateTime]::UtcNow.AddMinutes(-$MinimumAgeMinutes)
    foreach ($item in @(Get-ChildItem -LiteralPath $full -Force -File -ErrorAction Stop)) {
        if ($item.Name -cnotmatch '^\.ops010-copy-[0-9a-f]{32}\.partial$') { continue }
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
        if ($item.LastWriteTimeUtc -gt $threshold) { continue }
        Assert-PrivateWindowsAcl -Path $item.FullName -AllowInheritedChild
        # A path is a candidate for explicit human review, NOT automatically
        # deleted and not uploaded. The calling script does not print bytes.
        Write-Output $item.FullName
    }
}
