param(
  [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\assets')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Drawing.Common -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$background = [System.Drawing.Color]::FromArgb(8, 10, 12)
$panel = [System.Drawing.Color]::FromArgb(17, 18, 22)
$amber = [System.Drawing.Color]::FromArgb(214, 164, 67)
$solar = [System.Drawing.Color]::FromArgb(255, 191, 71)
$text = [System.Drawing.Color]::FromArgb(244, 240, 232)
$muted = [System.Drawing.Color]::FromArgb(150, 145, 138)
$hairline = [System.Drawing.Color]::FromArgb(56, 49, 41)

function New-PropertyItem([int]$Id, [int]$Type, [byte[]]$Value) {
  $item = [System.Runtime.Serialization.FormatterServices]::GetUninitializedObject([System.Drawing.Imaging.PropertyItem])
  $item.Id = $Id; $item.Type = $Type; $item.Len = $Value.Length; $item.Value = $Value
  return $item
}

function Save-Gif([System.Collections.Generic.List[System.Drawing.Bitmap]]$Frames, [string]$Path, [int]$DelayHundredths) {
  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/gif'
  $first = $Frames[0]
  $first.SetPropertyItem((New-PropertyItem 0x5100 4 ([BitConverter]::GetBytes([int]$DelayHundredths))))
  $first.SetPropertyItem((New-PropertyItem 0x5101 3 ([byte[]](0, 0))))
  $parameters = New-Object System.Drawing.Imaging.EncoderParameters 1
  $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::SaveFlag, [long][System.Drawing.Imaging.EncoderValue]::MultiFrame)
  $first.Save($Path, $codec, $parameters)
  $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::SaveFlag, [long][System.Drawing.Imaging.EncoderValue]::FrameDimensionTime)
  for ($index = 1; $index -lt $Frames.Count; $index += 1) { $first.SaveAdd($Frames[$index], $parameters) }
  $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::SaveFlag, [long][System.Drawing.Imaging.EncoderValue]::Flush)
  $first.SaveAdd($parameters); $parameters.Dispose()
  foreach ($frame in $Frames) { $frame.Dispose() }
}

function New-Graphics([System.Drawing.Bitmap]$Bitmap) {
  $graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  $graphics.Clear($background)
  return $graphics
}

function Draw-Label($Graphics, [string]$Value, [float]$X, [float]$Y, [float]$Size, [System.Drawing.Color]$Color) {
  $font = [System.Drawing.Font]::new('Consolas', $Size, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $brush = [System.Drawing.SolidBrush]::new($Color)
  $Graphics.DrawString($Value, $font, $brush, $X, $Y)
  $brush.Dispose(); $font.Dispose()
}

function New-Panel([int]$Width, [int]$Height) {
  $bitmap = New-Object System.Drawing.Bitmap($Width, $Height)
  $graphics = New-Graphics $bitmap
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new($panel), 1, 1, $Width - 2, $Height - 2)
  $graphics.DrawRectangle([System.Drawing.Pen]::new($hairline, 1), 1, 1, $Width - 3, $Height - 3)
  return @{ Bitmap = $bitmap; Graphics = $graphics }
}

function New-SkillsFrame([int]$Frame, [int]$Count) {
  $state = New-Panel 840 72; $bitmap = $state.Bitmap; $graphics = $state.Graphics
  Draw-Label $graphics 'STACK // MODULES' 22 12 11 $amber
  Draw-Label $graphics 'ICONOGRAPHY ONLINE' 638 12 10 $muted
  $graphics.DrawLine([System.Drawing.Pen]::new($hairline, 1), 22, 32, 818, 32)
  $graphics.DrawLine([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(62, $solar), 2), 22, 49, 818, 49)
  $x = 28 + (($Frame * 32) % 760)
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(45, $solar)), $x - 22, 40, 44, 18)
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new($solar), $x, 40, 2, 18)
  for ($dot = 0; $dot -lt 12; $dot += 1) {
    $dotX = 32 + ($dot * 70)
    $alpha = 80 + [int](70 * (1 + [Math]::Sin(($Frame / 4) + $dot)) / 2)
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb($alpha, $amber)), $dotX, 44, 5, 5)
  }
  Draw-Label $graphics ('FLOW ' + ('{0:d2}' -f $Frame) + ' / ' + ('{0:d2}' -f $Count)) 22 55 9 $muted
  $graphics.Dispose(); return $bitmap
}

function New-ResearchFrame([int]$Frame, [int]$Count) {
  $state = New-Panel 900 360; $bitmap = $state.Bitmap; $graphics = $state.Graphics
  Draw-Label $graphics 'AREAS OF INTEREST // 001' 24 18 12 $amber
  Draw-Label $graphics 'LIVE RESEARCH MAP' 736 19 10 $muted
  $graphics.DrawLine([System.Drawing.Pen]::new($hairline, 1), 24, 42, 876, 42)
  $nodes = @(
    @('AI AGENT SECURITY', 150, 92), @('MCP', 375, 72), @('SECURE RAG', 650, 92),
    @('CLOUD NATIVE', 110, 190), @('AGENTIC AI', 760, 190), @('DEV TOOLS', 150, 286),
    @('CYBERSECURITY', 375, 314), @('AUTOMATION', 650, 286), @('DISTRIBUTED SYS', 270, 190), @('HUMAN-CENTERED', 520, 190)
  )
  $center = [System.Drawing.PointF]::new(450, 190)
  $links = @(@(0, 1), @(1, 2), @(0, 3), @(2, 4), @(3, 6), @(4, 7), @(5, 6), @(6, 7), @(8, 9), @(8, 0), @(9, 2), @(8, 6), @(9, 7))
  $pulse = ($Frame % $Count) / [double]$Count
  foreach ($link in $links) {
    $a = $nodes[$link[0]]; $b = $nodes[$link[1]]
    $start = [System.Drawing.PointF]::new($a[1], $a[2]); $end = [System.Drawing.PointF]::new($b[1], $b[2])
    $graphics.DrawLine([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(90, $amber), 1), $start, $end)
    $progress = ($pulse + (($link[0] * 0.11) % 1)) % 1
    $px = $start.X + (($end.X - $start.X) * $progress); $py = $start.Y + (($end.Y - $start.Y) * $progress)
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new($solar), $px - 3, $py - 3, 6, 6)
  }
  foreach ($node in $nodes) {
    $x = [float]$node[1]; $y = [float]$node[2]
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(42, $solar)), $x - 10, $y - 10, 20, 20)
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new($solar), $x - 4, $y - 4, 8, 8)
    $labelX = $x - ($node[0].Length * 3.4); $labelY = $y + 14
    Draw-Label $graphics $node[0] $labelX $labelY 10 $text
  }
  $graphics.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(55, $solar)), $center.X - 28, $center.Y - 28, 56, 56)
  $graphics.FillEllipse([System.Drawing.SolidBrush]::new($solar), $center.X - 7, $center.Y - 7, 14, 14)
  Draw-Label $graphics 'SINAG' 426 221 10 $amber
  Draw-Label $graphics ('NODE DENSITY 10  //  CYCLE ' + ('{0:d2}' -f $Frame)) 24 338 9 $muted
  $graphics.Dispose(); return $bitmap
}

function New-TerminalFrame([int]$Frame, [string[]]$Topics) {
  $state = New-Panel 820 260; $bitmap = $state.Bitmap; $graphics = $state.Graphics
  Draw-Label $graphics 'SINAG / RESEARCH LAB' 24 18 12 $amber
  Draw-Label $graphics '● SYSTEM ONLINE' 628 18 11 $solar
  $graphics.DrawLine([System.Drawing.Pen]::new($hairline, 1), 24, 42, 796, 42)
  $lines = @('initializing research modules...', 'loading agent security protocols...', 'verifying MCP authorization...', 'examining secure retrieval...', 'monitoring agent activity...', 'mapping cloud automation...')
  for ($line = 0; $line -lt $lines.Count; $line += 1) {
    $active = $line -eq ([Math]::Floor($Frame / 4) % $lines.Count)
    $color = if ($active) { $text } else { $muted }
    $prefix = if ($active) { '>' } else { '·' }
    Draw-Label $graphics ($prefix + ' ' + $lines[$line]) 34 (60 + $line * 24) 12 $color
  }
  $topic = $Topics[[Math]::Floor($Frame / 2) % $Topics.Count]
  Draw-Label $graphics 'ACTIVE MODULE:' 486 68 10 $muted
  Draw-Label $graphics $topic 486 90 12 $solar
  Draw-Label $graphics 'STATUS: BUILDING' 486 132 11 $text
  $progress = 486 + (($Frame * 18) % 270)
  $graphics.DrawLine([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(75, $amber), 1), 486, 158, 756, 158)
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new($solar), 486, 156, [Math]::Max(2, $progress - 486), 4)
  $cursor = if (($Frame % 4) -lt 2) { '_' } else { ' ' }
  Draw-Label $graphics ('> pipeline.ready' + $cursor) 34 218 11 $amber
  Draw-Label $graphics ('CYCLE ' + ('{0:d2}' -f $Frame) + ' / 16') 674 218 10 $muted
  $graphics.Dispose(); return $bitmap
}

$skills = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($frame = 0; $frame -lt 16; $frame += 1) { $skills.Add((New-SkillsFrame $frame 16)) }
Save-Gif $skills (Join-Path $OutputDirectory 'skills-scan.gif') 8

$research = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($frame = 0; $frame -lt 16; $frame += 1) { $research.Add((New-ResearchFrame $frame 16)) }
Save-Gif $research (Join-Path $OutputDirectory 'research-network.gif') 8

$topics = @('RUST-NATIVE AI SECURITY', 'MCP AUTHORIZATION', 'SECURE RAG', 'AGENT OBSERVABILITY', 'LOCAL-FIRST INTELLIGENCE', 'CLOUD AUTOMATION')
$terminal = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($frame = 0; $frame -lt 16; $frame += 1) { $terminal.Add((New-TerminalFrame $frame $topics)) }
Save-Gif $terminal (Join-Path $OutputDirectory 'research-terminal.gif') 10

foreach ($asset in @('skills-scan.gif', 'research-network.gif', 'research-terminal.gif')) {
  $path = Join-Path $OutputDirectory $asset
  if (-not (Test-Path $path) -or ((Get-Item $path).Length -lt 1000)) { throw "Asset validation failed: $asset" }
}
Write-Output 'Generated and validated skills-scan.gif, research-network.gif, and research-terminal.gif.'
