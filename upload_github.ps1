# FinPilot AI - Automated GitHub Repository Creator and Publisher
$ErrorActionPreference = "Stop"

$code = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public class CredManager {
    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr credentialPtr);

    [DllImport("advapi32.dll", EntryPoint = "CredFree", SetLastError = true)]
    public static extern void CredFree(IntPtr cred);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREDENTIAL {
        public int Flags;
        public int Type;
        public string TargetName;
        public string Comment;
        public long LastWritten;
        public int CredentialBlobSize;
        public IntPtr CredentialBlob;
        public int Persist;
        public int AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    public static string GetPassword(string target) {
        IntPtr credPtr;
        if (CredRead(target, 1, 0, out credPtr)) {
            CREDENTIAL cred = (CREDENTIAL)Marshal.PtrToStructure(credPtr, typeof(CREDENTIAL));
            byte[] blob = new byte[cred.CredentialBlobSize];
            Marshal.Copy(cred.CredentialBlob, blob, 0, cred.CredentialBlobSize);
            CredFree(credPtr);
            return Encoding.UTF8.GetString(blob);
        }
        return null;
    }
}
'@

if (-not ([System.Management.Automation.PSTypeName]'CredManager').Type) {
    Add-Type -TypeDefinition $code -Language CSharp
}

$token = [CredManager]::GetPassword("GitHub - https://api.github.com/GAUTAMX05")
if (-not $token) {
    throw "GitHub access token could not be retrieved from Windows Credential Manager."
}

Write-Host "=================================================================="
Write-Host "      FINPILOT AI -- GITHUB REPOSITORY DEPLOYMENT PIPELINE       "
Write-Host "=================================================================="

# 1. Verify User Profile via GitHub API
Write-Host "`n--- 1. Authenticating with GitHub API ---"
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept"        = "application/vnd.github.v3+json"
    "User-Agent"    = "FinPilot-AI-Publisher"
}

$userProfile = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method GET
$username = $userProfile.login
Write-Host "Authenticated as GitHub User: $username ($($userProfile.html_url)) [OK]"

# 2. Create Public Repository on GitHub
$repoName = "FinPilot-Ai"
Write-Host "`n--- 2. Creating New Public Repository: $repoName ---"

$repoPayload = @{
    name        = $repoName
    description = "FinPilot AI - Financial Digital Twin and Multi-Agent Autonomous Decision Operating System"
    private     = $false
    has_issues  = $true
    has_wiki    = $true
} | ConvertTo-Json

try {
    $createRes = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $headers -Method POST -Body $repoPayload -ContentType "application/json"
    Write-Host "Created new public repository: $($createRes.html_url) [CREATED]"
    $repoUrl = $createRes.html_url
} catch {
    $errStr = $_.Exception.Message
    if ($errStr -match "already exists" -or $errStr -match "422") {
        Write-Host "Repository '$repoName' already exists on user account. Proceeding to synchronize files..."
        $repoUrl = "https://github.com/$username/$repoName"
    } else {
        try {
            $existingRepo = Invoke-RestMethod -Uri "https://api.github.com/repos/$username/$repoName" -Headers $headers -Method GET
            Write-Host "Target repository confirmed: $($existingRepo.html_url) [OK]"
            $repoUrl = $existingRepo.html_url
        } catch {
            throw "Failed to create or verify repository: $errStr"
        }
    }
}

# 3. Setup Git and Push Project Files
Write-Host "`n--- 3. Staging and Committing FinPilot AI Codebase ---"
$gitBin = "C:\Users\gauta\AppData\Local\GitHubDesktop\app-3.6.4\resources\app\git\cmd\git.exe"

$projectDir = $PSScriptRoot
Set-Location $projectDir

# Initialize or reinitialize git repo
if (Test-Path "$projectDir\.git") {
    Remove-Item -Path "$projectDir\.git" -Recurse -Force
}

& $gitBin init -b main
& $gitBin config user.name "Gautam Chauhan"
& $gitBin config user.email "S24CSEU0777@BENNETT.EDU.IN"

# Stage files
& $gitBin add .
& $gitBin commit -m "feat(core): Initial release of FinPilot AI - Financial Digital Twin, 7-Agent Orchestrator, and Causal Decision Platform"

# Remote setup with token authentication
$authenticatedRemote = "https://$($username):$($token)@github.com/$username/$repoName.git"
& $gitBin remote add origin $authenticatedRemote

Write-Host "`n--- 4. Pushing Codebase to GitHub (main branch) ---"
& $gitBin push -u origin main --force

# Remove embedded token from remote URL for security
& $gitBin remote set-url origin "https://github.com/$username/$repoName.git"

# Clean up upload script before final commit if needed
Write-Host "`n=================================================================="
Write-Host "SUCCESS! FINPILOT AI REPOSITORY IS LIVE AT:"
Write-Host "$repoUrl"
Write-Host "Walkthrough and Architecture Guide: $repoUrl/blob/main/WALKTHROUGH.md"
Write-Host "=================================================================="
