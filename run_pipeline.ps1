param(
    [string]$Url,
    [string]$Title,
    [int]$Index = 0,
    [switch]$All
)

# Check if environment variables are set, if not try to load from .env
if (-not (Get-Item -Path env:EXA_API_KEY -ErrorAction SilentlyContinue)) {
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "EXA_API_KEY=(.+)") {
                $env:EXA_API_KEY = $matches[1].Trim()
            }
        }
    }
}

if (-not (Get-Item -Path env:EXA_API_KEY -ErrorAction SilentlyContinue)) {
    Write-Warning "EXA_API_KEY environment variable not found and not in .env. Please set it using: `$env:EXA_API_KEY='your_key'"
    exit
}

$jobsToProcess = @()

if ($Url -and $Title) {
    $jobsToProcess += [PSCustomObject]@{
        url = $Url
        title = $Title
    }
    Write-Host "--- Using Provided Job: $Title ---" -ForegroundColor Yellow
} else {
    # 1. Search for jobs (only if data/jobs_found.json doesn't exist or we want fresh ones)
    if (-not (Test-Path "data/jobs_found.json")) {
        Write-Host "--- Step 1: Job Search ---" -ForegroundColor Green
        python scripts/search_jobs.py "AI Machine Learning Engineer" "Remote or Germany"
    } else {
        Write-Host "--- Using existing search results in data/jobs_found.json ---" -ForegroundColor Gray
        Write-Host "(Delete the file if you want a fresh search)" -ForegroundColor Gray
    }

    if (-not (Test-Path "data/jobs_found.json")) {
        Write-Error "Jobs file not found."
        exit
    }

    $jobs = Get-Content "data/jobs_found.json" | ConvertFrom-Json
    if ($jobs.Count -eq 0) {
        Write-Warning "No jobs found in the list."
        exit
    }

    if ($All) {
        $jobsToProcess = $jobs
        Write-Host "--- Processing ALL $($jobs.Count) jobs ---" -ForegroundColor Yellow
    } else {
        if ($Index -ge $jobs.Count) {
            Write-Error "Index $Index is out of range. Only $($jobs.Count) jobs available."
            exit
        }
        $jobsToProcess += $jobs[$Index]
        Write-Host "--- Processing Job Index $Index of $($jobs.Count - 1) ---" -ForegroundColor Yellow
    }
}

foreach ($job in $jobsToProcess) {
    $jobUrl = $job.url
    $jobTitle = $job.title -replace '[^a-zA-Z0-9]', ''
    
    Write-Host "`n>>> Starting Pipeline for: $jobTitle <<" -ForegroundColor Cyan -BackgroundColor DarkBlue

    # 3. Scrape JD
    Write-Host "--- Step 2: Scrape JD ---" -ForegroundColor Green
    python scripts/scrape_jd.py "$jobUrl" "$jobTitle"

    # 4. Tailor Resume (using Gemini CLI + LaTeX)
    Write-Host "--- Step 3: Tailor Resume (LaTeX & Gemini) ---" -ForegroundColor Green
    $masterCvPath = "data/master_cv.tex"
    $jdPath = "data/raw_jds/$jobTitle.md"
    $tailoredResumePathTex = "data/tailored_outputs/$jobTitle`_CV.tex"

    python scripts/tailor_resume_lossless.py "$masterCvPath" "$jdPath" "$tailoredResumePathTex"

    if (Test-Path $tailoredResumePathTex) {
        Write-Host "Tailored resume saved to: $tailoredResumePathTex (and compiled to PDF)" -ForegroundColor Cyan
        
        # 5. Networker
        Write-Host "--- Step 4: Networking & Outreach ---" -ForegroundColor Green
        # Extract root domain (e.g., siemens.com instead of jobs.siemens.com)
        $domainParts = ($jobUrl -split '/')[2] -split '\.'
        if ($domainParts.Count -ge 2) {
            $domain = "$($domainParts[-2]).$($domainParts[-1])"
        } else {
            $domain = ($jobUrl -split '/')[2]
        }
        python scripts/networker.py "$domain" "$jobTitle" "$tailoredResumePathTex"

    } else {
        Write-Warning "Tailoring failed for $jobTitle. Skipping networking."
    }
}

Write-Host "`nPipeline batch completed." -ForegroundColor Yellow
