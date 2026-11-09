param(
  [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\assets')
)

$ErrorActionPreference = 'Stop'
[System.Drawing.Color]$Background = [System.Drawing.Color]::FromArgb(8, 10, 12)
[System.Drawing.Color]$Panel = [System.Drawing.Color]::FromArgb(17, 18, 22)
[System.Drawing.Color]$Amber = [System.Drawing.Color]::FromArgb(214, 164, 67)
[System.Drawing.Color]$Solar = [System.Drawing.Color]::FromArgb(255, 191, 71)
[System.Drawing.Color]$Text = [System.Drawing.Color]::FromArgb(244, 240, 232)
[System.Drawing.Color]$Muted = [System.Drawing.Color]::FromArgb(150, 145, 138)
[System.Drawing.Color]$Hairline = [System.Drawing.Color]::FromArgb(56, 49, 41)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Drawing.Common -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

function New-PropertyItem([int]$Id, [int]$Type, [byte[]]$Value) {
  $item = [System.Runtime.Serialization.FormatterServices]::GetUninitializedObject([System.Drawing.Imaging.PropertyItem])
  $item.Id = $Id
  $item.Type = $Type
  $item.Len = $Value.Length
  $item.Value = $Value
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
  for ($index = 1; $index -lt $Frames.Count; $index += 1) {
    $first.SaveAdd($Frames[$index], $parameters)
  }
  $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::SaveFlag, [long][System.Drawing.Imaging.EncoderValue]::Flush)
  $first.SaveAdd($parameters)
  $parameters.Dispose()
  foreach ($frame in $Frames) { $frame.Dispose() }
}

function New-Graphics([System.Drawing.Bitmap]$Bitmap) {
  $graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  $graphics.Clear($Background)
  return $graphics
}

function Draw-Label($Graphics, [string]$Value, [float]$X, [float]$Y, [float]$Size, [System.Drawing.Color]$Color) {
  $font = [System.Drawing.Font]::new('Consolas', $Size, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $brush = [System.Drawing.SolidBrush]::new($Color)
  $Graphics.DrawString($Value, $font, $brush, $X, $Y)
  $brush.Dispose(); $font.Dispose()
}

function New-CoreFrame([int]$Frame, [int]$Count) {
  $bitmap = New-Object System.Drawing.Bitmap(480, 270)
  $graphics = New-Graphics $bitmap
  $graphics.ScaleTransform(0.75, 0.75)
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new($Panel), 18, 18, 604, 324)
  $graphics.DrawRectangle([System.Drawing.Pen]::new($Hairline, 1), 18, 18, 603, 323)
  Draw-Label $graphics 'SINAG // CORE-01' 38 34 11 $Amber
  Draw-Label $graphics 'ORBITAL SYSTEM ONLINE' 414 34 10 $Muted
  $graphics.DrawLine((New-Object System.Drawing.Pen($Hairline, 1)), 38, 57, 602, 57)
  $cx = 320; $cy = 184; $phase = (2 * [Math]::PI * $Frame / $Count)
  foreach ($orbit in @(@(194, 60, 18), @(152, 112, -28), @(102, 148, 72))) {
    $state = $graphics.Save()
    $graphics.TranslateTransform($cx, $cy)
    $graphics.RotateTransform($orbit[2] + ($Frame * 360 / $Count) * ($orbit[0] % 3 - 1) * 0.08)
    $graphics.DrawEllipse([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(110, $Amber), 1.2), -$orbit[0], -$orbit[1], $orbit[0] * 2, $orbit[1] * 2)
    $graphics.Restore($state)
  }
  $points = New-Object System.Collections.Generic.List[System.Drawing.PointF]
  for ($node = 0; $node -lt 8; $node += 1) {
    $angle = $phase + ($node * [Math]::PI / 4)
    $radiusX = 194 - (($node % 3) * 26)
    $radiusY = 60 + (($node % 3) * 26)
    $x = $cx + [Math]::Cos($angle) * $radiusX
    $y = $cy + [Math]::Sin($angle) * $radiusY
    $points.Add([System.Drawing.PointF]::new([float]$x, [float]$y))
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new($Solar), $x - 3, $y - 3, 6, 6)
  }
  for ($node = 0; $node -lt $points.Count; $node += 1) {
    $next = ($node + 1) % $points.Count
    $graphics.DrawLine([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(95, $Amber), 1), $points[$node], $points[$next])
  }
  for ($ring = 1; $ring -le 5; $ring += 1) {
    $radius = 9 + $ring * 8 + [Math]::Sin($phase) * 2
    $alpha = 42 + $ring * 15
    $graphics.FillEllipse([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb($alpha, $Solar)), $cx - $radius, $cy - $radius, $radius * 2, $radius * 2)
  }
  $graphics.FillEllipse([System.Drawing.SolidBrush]::new($Solar), $cx - 10, $cy - 10, 20, 20)
  $graphics.DrawLine([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(120, $Solar), 1), 72, 300, 568, 300)
  Draw-Label $graphics 'NODE DENSITY 08' 38 313 10 $Muted
  Draw-Label $graphics 'MCP / RAG / POLICY' 238 313 10 $Text
  Draw-Label $graphics ('CYCLE ' + ('{0:d2}' -f $Frame) + ' / ' + ('{0:d2}' -f $Count)) 488 313 10 $Muted
  $graphics.Dispose()
  return $bitmap
}

function New-TypingFrame([int]$Frame, [string[]]$Phrases) {
  $bitmap = New-Object System.Drawing.Bitmap(720, 108)
  $graphics = New-Graphics $bitmap
  $graphics.ScaleTransform(0.818, 0.818)
  $graphics.FillRectangle([System.Drawing.SolidBrush]::new($Panel), 1, 1, 878, 130)
  $graphics.DrawRectangle([System.Drawing.Pen]::new($Hairline, 1), 1, 1, 878, 130)
  Draw-Label $graphics 'SINAG.SYS // FOCUS' 28 18 10 $Amber
  $phraseIndex = [Math]::Floor($Frame / 10) % $Phrases.Count
  $phrase = $Phrases[$phraseIndex]
  $visible = [Math]::Min($phrase.Length, [Math]::Max(0, ($Frame % 10) * [Math]::Ceiling($phrase.Length / 9)))
  $cursor = if (($Frame % 4) -lt 2) { '_' } else { ' ' }
  Draw-Label $graphics ($phrase.Substring(0, $visible) + $cursor) 28 50 23 $Text
  Draw-Label $graphics ('0' + ($phraseIndex + 1) + ' / 05') 780 56 10 $Muted
  Draw-Label $graphics 'BUILDING SYSTEMS THAT MATTER' 28 103 10 $Muted
  $graphics.Dispose()
  return $bitmap
}

$coreFrames = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($frame = 0; $frame -lt 32; $frame += 1) { $coreFrames.Add((New-CoreFrame $frame 32)) }
Save-Gif $coreFrames (Join-Path $OutputDirectory 'sinag-core.gif') 7

$phrases = @('AI SECURITY ENGINEERING', 'FULL-STACK DEVELOPMENT', 'AI AGENTS & AUTOMATION', 'CLOUD & DEVOPS', 'BUILDING SYSTEMS THAT MATTER')
$typingFrames = New-Object System.Collections.Generic.List[System.Drawing.Bitmap]
for ($frame = 0; $frame -lt ($phrases.Count * 10); $frame += 1) { $typingFrames.Add((New-TypingFrame $frame $phrases)) }
Save-Gif $typingFrames (Join-Path $OutputDirectory 'sinag-typing.gif') 10

Write-Output "Generated sinag-core.gif and sinag-typing.gif in $OutputDirectory"
