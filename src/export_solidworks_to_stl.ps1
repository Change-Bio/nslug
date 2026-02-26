param(
    [Parameter(Mandatory)] [string]$InputFile,
    [string]$OutPathOrDir
)

$ErrorActionPreference = "Stop"

# ---------- path handling ----------

function Resolve-ExistingFile([string]$p) {
    if ([IO.Path]::IsPathRooted($p)) { return (Resolve-Path $p).Path }
    return (Resolve-Path (Join-Path (Get-Location).Path $p)).Path
}

$inputPath = Resolve-ExistingFile $InputFile
$baseName  = [IO.Path]::GetFileNameWithoutExtension($inputPath)

function Resolve-OutStlPath([string]$outArg, [string]$baseName, [string]$inputPath) {

    # default: same dir as input
    if ([string]::IsNullOrWhiteSpace($outArg)) {
        return Join-Path (Split-Path $inputPath) ($baseName + ".stl")
    }

    $ext = [IO.Path]::GetExtension($outArg).ToLowerInvariant()

    # full .stl path
    if ($ext -eq ".stl") {
        $leaf   = [IO.Path]::GetFileName($outArg)
        $parent = Split-Path $outArg -Parent

        if ([string]::IsNullOrWhiteSpace($parent)) {
            $parent = (Get-Location).Path
        } elseif (-not [IO.Path]::IsPathRooted($parent)) {
            $parent = Join-Path (Get-Location).Path $parent
        }

        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        $parent = (Resolve-Path $parent).Path
        return Join-Path $parent $leaf
    }

    # directory
    $dir = $outArg
    if (-not [IO.Path]::IsPathRooted($dir)) {
        $dir = Join-Path (Get-Location).Path $dir
    }

    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $dir = (Resolve-Path $dir).Path
    return Join-Path $dir ($baseName + ".stl")
}

$outPath = Resolve-OutStlPath $OutPathOrDir $baseName $inputPath

# Create a temporary copy name based on the STL name (same folder as input)
$inputDir   = Split-Path $inputPath -Parent
$inputExt   = [IO.Path]::GetExtension($inputPath)
$tmpBase    = [IO.Path]::GetFileNameWithoutExtension($outPath)   # "new name"
$tmpPath    = Join-Path $inputDir ($tmpBase + $inputExt)         # new-name.SLDPRT/SLDASM/etc

# Ensure we don't clobber an existing file with that name
if (Test-Path $tmpPath) {
    $tmpPath = Join-Path $inputDir ("{0}.{1}{2}" -f $tmpBase, [Guid]::NewGuid().ToString("N"), $inputExt)
}

Copy-Item -LiteralPath $inputPath -Destination $tmpPath -Force

# ---------- SolidWorks interop resolution ----------

function Find-InteropDll([string]$name) {
    $scriptDir = Split-Path $PSCommandPath
    $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }

    $candidates = @(
        (Join-Path $scriptDir $name)
    ) + ($roots | ForEach-Object {
        $sw = Join-Path $_ "SOLIDWORKS Corp\SOLIDWORKS"
        @(
            (Join-Path $sw $name),
            (Join-Path $sw "api\redist\$name"),
            (Join-Path $sw "api\$name")
        )
    }) | Where-Object { Test-Path $_ }

    if ($candidates) { return $candidates[0] }

    foreach ($r in $roots) {
        $corp = Join-Path $r "SOLIDWORKS Corp"
        if (-not (Test-Path $corp)) { continue }
        $hit = Get-ChildItem $corp -Recurse -Filter $name -ErrorAction SilentlyContinue |
               Select-Object -First 1 -ExpandProperty FullName
        if ($hit) { return $hit }
    }

    return $null
}

$sldworks = Find-InteropDll "SolidWorks.Interop.sldworks.dll"
$swconst  = Find-InteropDll "SolidWorks.Interop.swconst.dll"
if (-not $sldworks -or -not $swconst) {
    throw "Missing SOLIDWORKS interop DLLs (install SOLIDWORKS API or place DLLs next to script)."
}

# preload all interops from same folder
$interopDir = Split-Path $sldworks
Get-ChildItem $interopDir -Filter "SolidWorks.Interop.*.dll" -ErrorAction SilentlyContinue |
    ForEach-Object { [void][Reflection.Assembly]::LoadFrom($_.FullName) }

# ---------- C# exporter (unique type per run) ----------

$ns = "SwInterop_" + ([Guid]::NewGuid().ToString("N"))
$typeName = "Exporter"
$fullType = "$ns.$typeName"

$src = @"
using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace $ns {
    public static class $typeName {
        public static bool ExportStlFromCopiedDoc(string originalPath, string copiedPath, string outPath) {
            var app = (ISldWorks)Activator.CreateInstance(
                Type.GetTypeFromProgID("SldWorks.Application")
            );
            if (app == null) return false;

            int errs = 0, warns = 0;

            // Open the ORIGINAL (so references resolve correctly)
            var spec = (IDocumentSpecification)app.GetOpenDocSpec(originalPath);
            string ext = System.IO.Path.GetExtension(originalPath).ToLowerInvariant();
            if (ext == ".sldprt") spec.DocumentType = (int)swDocumentTypes_e.swDocPART;
            else if (ext == ".sldasm") spec.DocumentType = (int)swDocumentTypes_e.swDocASSEMBLY;
            else if (ext == ".slddrw") spec.DocumentType = (int)swDocumentTypes_e.swDocDRAWING;


            spec.ReadOnly = false;
            spec.Silent   = true;

            var model = (IModelDoc2)app.OpenDoc7(spec);
            if (model == null) return false;

            // Save-as to COPIED path (this creates the renamed copy in SolidWorks terms)
            bool savedCopy = model.Extension.SaveAs(
                copiedPath,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null, ref errs, ref warns
            );
            if (!savedCopy) {
                app.CloseDoc(model.GetTitle());
                return false;
            }

            // Rebuild, then export STL (from the opened doc, which now corresponds to the copied file on disk)
            model.ForceRebuild3(false);

            int err2 = 0, warn2 = 0;
            bool ok = model.Extension.SaveAs(
                outPath,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null, ref err2, ref warn2
            );

            app.CloseDoc(model.GetTitle());
            return ok;
        }
    }
}
"@

Add-Type -Language CSharp -ReferencedAssemblies @("System.dll", $sldworks, $swconst) -TypeDefinition $src

# ---------- run (and always delete temp copy) ----------

try {
    $ok = Invoke-Expression ("[{0}]::ExportStlFromCopiedDoc('{1}','{2}','{3}')" -f $fullType,
        ($inputPath.Replace("'","''")),
        ($tmpPath.Replace("'","''")),
        ($outPath.Replace("'","''"))
    )

    if (-not ($ok -and (Test-Path $outPath))) {
        throw "Export failed: $outPath"
    }

    "Saved: $outPath"
}
finally {
    if (Test-Path $tmpPath) {
        Remove-Item -LiteralPath $tmpPath -Force -ErrorAction SilentlyContinue
    }
}
