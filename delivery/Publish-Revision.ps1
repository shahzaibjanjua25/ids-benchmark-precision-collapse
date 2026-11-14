[CmdletBinding()]
param(
    [switch]$VerifyOnly,
    [string]$CheckoutRoot = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'

function Invoke-CheckedGit {
    param([string[]]$Arguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $result = & git @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($exitCode -ne 0) {
        throw "git $($Arguments[0]) failed (exit $exitCode): $($result -join [Environment]::NewLine)"
    }
    return @($result | ForEach-Object { $_.ToString() })
}

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required on PATH.' }
    $expectedRemote = 'https://github.com/shahzaibjanjua25/ids-benchmark-precision-collapse.git'
    $expectedBranch = 'research/publication-ready-revision'
    $manifestPath = Join-Path $PSScriptRoot 'delivery-manifest.json'
    $bundlePath = Join-Path $PSScriptRoot 'research-revision.bundle'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Keep delivery-manifest.json beside this script.' }
    if (-not (Test-Path -LiteralPath $bundlePath -PathType Leaf)) { throw 'Keep research-revision.bundle beside this script (extract the complete package).' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.remote -ne $expectedRemote -or $manifest.branch -ne $expectedBranch) { throw 'Unexpected repository or branch in delivery manifest.' }
    if ($manifest.commit -notmatch '^[0-9a-f]{40}$') { throw 'Invalid expected commit.' }
    $actualHash = (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $manifest.bundle_sha256) { throw 'Bundle checksum does not match delivery manifest.' }
    $bundleHeads = Invoke-CheckedGit -Arguments @('bundle', 'list-heads', $bundlePath)
    if (-not ($bundleHeads -contains "$($manifest.commit) refs/heads/$expectedBranch")) { throw 'Expected branch tip is absent from bundle.' }
    if (-not (Test-Path -LiteralPath $CheckoutRoot)) { New-Item -ItemType Directory -Path $CheckoutRoot | Out-Null }
    $checkoutName = 'ids-revision-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
    $checkoutPath = Join-Path (Resolve-Path -LiteralPath $CheckoutRoot).Path $checkoutName
    if (Test-Path -LiteralPath $checkoutPath) { throw 'Refusing to reuse an existing checkout.' }
    $cloneSource = if ($VerifyOnly) { $bundlePath } else { $expectedRemote }
    Invoke-CheckedGit -Arguments @('clone', '--no-checkout', $cloneSource, $checkoutPath) | Write-Host
    Push-Location -LiteralPath $checkoutPath
    try {
        if ($VerifyOnly) {
            Invoke-CheckedGit -Arguments @('remote', 'set-url', 'origin', $expectedRemote) | Write-Host
        }
        $origin = (Invoke-CheckedGit -Arguments @('remote', 'get-url', 'origin')) -join ''
        if ($origin.TrimEnd('/') -ne $expectedRemote) { throw "Unexpected origin: $origin" }
        Invoke-CheckedGit -Arguments @('bundle', 'verify', $bundlePath) | Write-Host
        Invoke-CheckedGit -Arguments @('fetch', $bundlePath, "refs/heads/$expectedBranch") | Write-Host
        $importedTip = ((Invoke-CheckedGit -Arguments @('rev-parse', 'FETCH_HEAD')) -join '').Trim()
        if ($importedTip -ne $manifest.commit) { throw 'Imported commit differs from delivery manifest.' }
        Invoke-CheckedGit -Arguments @('merge-base', '--is-ancestor', $manifest.original_commit, $importedTip) | Out-Null
        Invoke-CheckedGit -Arguments @('config', '--local', 'user.name', 'Shah Zaib Sajid') | Out-Null
        Invoke-CheckedGit -Arguments @('config', '--local', 'user.email', 'shahzaibjanjua25@gmail.com') | Out-Null
        & git show-ref --verify --quiet "refs/heads/$expectedBranch"
        if ($LASTEXITCODE -eq 0) {
            Invoke-CheckedGit -Arguments @('checkout', $expectedBranch) | Write-Host
            Invoke-CheckedGit -Arguments @('merge', '--ff-only', $importedTip) | Write-Host
        } else {
            Invoke-CheckedGit -Arguments @('checkout', '-b', $expectedBranch, $importedTip) | Write-Host
        }
        $branch = ((Invoke-CheckedGit -Arguments @('branch', '--show-current')) -join '').Trim()
        if ($branch -ne $expectedBranch) { throw 'Incorrect checked-out branch.' }
        if ((Invoke-CheckedGit -Arguments @('status', '--porcelain')).Count -gt 0) { throw 'Checkout is unexpectedly dirty.' }
        if ($VerifyOnly) {
            Write-Host "Offline bundle verification passed: $importedTip"
            Write-Host "Verified checkout: $checkoutPath"
        } else {
            $remoteHeads = Invoke-CheckedGit -Arguments @('ls-remote', '--heads', 'origin', "refs/heads/$expectedBranch")
            if ($remoteHeads.Count -gt 0) {
                Invoke-CheckedGit -Arguments @('fetch', 'origin', "refs/heads/${expectedBranch}:refs/remotes/origin/$expectedBranch") | Write-Host
                & git merge-base --is-ancestor "refs/remotes/origin/$expectedBranch" $importedTip
                if ($LASTEXITCODE -ne 0) {
                    & git merge-base --is-ancestor $importedTip "refs/remotes/origin/$expectedBranch"
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host 'The remote branch already contains this revision.'
                        Write-Host "https://github.com/shahzaibjanjua25/ids-benchmark-precision-collapse/tree/$expectedBranch"
                        exit 0
                    }
                    throw 'Remote research branch has divergent commits. Nothing was pushed; merge review is required. Existing work is preserved.'
                }
            }
            Invoke-CheckedGit -Arguments @('push', '--set-upstream', 'origin', "HEAD:refs/heads/$expectedBranch") | Write-Host
            Write-Host "https://github.com/shahzaibjanjua25/ids-benchmark-precision-collapse/tree/$expectedBranch"
            Write-Host "https://github.com/shahzaibjanjua25/ids-benchmark-precision-collapse/commit/$importedTip"
        }
    } finally { Pop-Location }
} catch {
    Write-Error "Publication stopped safely: $($_.Exception.Message)" -ErrorAction Continue
    exit 1
}
