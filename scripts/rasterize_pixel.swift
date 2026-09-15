import Foundation
import CoreText
import CoreGraphics

// usage: rasterize_pixel.swift <task.json> <out.json> <px> <font.ttf>
// task.json: {"charset": "..."} — space is blank 4-px advance, handled by the layout side.
// Rasterizes every char on a shared px-grid via glyph outline paths (CTLineDraw is unreliable).
// All glyphs share one canvas origin (font bounding box), then get globally cropped to ink,
// so baselines stay aligned across chars. Advance width is calibrated from a fullwidth ref char,
// so it works regardless of the font's unitsPerEm.

setbuf(stdout, nil)

let args = CommandLine.arguments
let taskPath = args.count > 1 ? args[1] : "pixel_task.json"
let outPath = args.count > 2 ? args[2] : "glyphs.json"
let N = args.count > 3 ? Int(args[3]) ?? 12 : 12
let fontPath = args[4]

let url = URL(fileURLWithPath: fontPath) as CFURL
guard let descs = CTFontManagerCreateFontDescriptorsFromURL(url) as? [CTFontDescriptor],
      let desc = descs.first else { fatalError("cannot load font") }
let font = CTFontCreateWithFontDescriptor(desc, 120, nil)

var ref16 = Array("猫".utf16)
var refGlyph: CGGlyph = 0
guard CTFontGetGlyphsForCharacters(font, &ref16, &refGlyph, 1) else { fatalError("ref char missing") }
let advRef = CTFontGetAdvancesForGlyphs(font, .horizontal, [refGlyph], nil, 1)
let unit = advRef / CGFloat(N)          // font units per design px
let SS = 8.0                            // canvas px per design px
let k = SS / unit
let bb = CTFontGetBoundingBox(font)
let H = Int(ceil(bb.height / unit))
print("font units/px=\(unit)  canvas=\(H) design rows  bbox=\(bb)")

func raster(_ ch: Character) -> (cols: Int, grid: [[Int]])? {
    var u16 = Array(String(ch).utf16)
    var glyph: CGGlyph = 0
    guard CTFontGetGlyphsForCharacters(font, &u16, &glyph, 1), glyph != 0,
          let p = CTFontCreatePathForGlyph(font, glyph, nil) else { return nil }
    let adv = CTFontGetAdvancesForGlyphs(font, .horizontal, [glyph], nil, 1)
    let cols = max(1, Int((adv / unit).rounded()))
    var t = CGAffineTransform(a: k, b: 0, c: 0, d: k, tx: -bb.minX * k, ty: -bb.minY * k)
    guard let moved = p.copy(using: &t) else { return nil }
    let W = cols * Int(SS), Hc = H * Int(SS)
    var buf = [UInt8](repeating: 0, count: W * Hc)
    guard let ctx = CGContext(data: &buf, width: W, height: Hc, bitsPerComponent: 8,
                              bytesPerRow: W, space: CGColorSpaceCreateDeviceGray(),
                              bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return nil }
    ctx.setFillColor(gray: 1.0, alpha: 1.0)
    ctx.addPath(moved)
    ctx.fillPath()
    var grid = [[Int]](repeating: [Int](repeating: 0, count: cols), count: H)
    for gy in 0..<H {
        for gx in 0..<cols {
            var sum = 0
            for dy in 0..<Int(SS) { for dx in 0..<Int(SS) { sum += Int(buf[(gy * Int(SS) + dy) * W + gx * Int(SS) + dx]) } }
            grid[gy][gx] = sum >= Int(SS) * Int(SS) * 255 / 2 ? 1 : 0
        }
    }
    return (cols, grid)
}

guard let data = try? String(contentsOfFile: taskPath, encoding: .utf8),
      let obj = try? JSONSerialization.jsonObject(with: Data(data.utf8)),
      let task = obj as? [String: Any],
      let charset = task["charset"] as? String else { fatalError("cannot read task json") }

var raw: [Character: (cols: Int, grid: [[Int]])] = [:]
var missing: [String] = []
for ch in charset where ch != " " {
    if let r = raster(ch), r.grid.flatMap({ $0 }).reduce(0, +) > 0 {
        raw[ch] = r
    } else {
        missing.append(String(ch))
    }
}
print("rasterized: \(raw.count)  missing: \(missing.map { "'\($0)'" }.joined(separator: " "))")

// global ink-row crop keeps baselines aligned across chars
var minY = Int.max, maxY = -1
for r in raw.values {
    for (y, row) in r.grid.enumerated() where row.contains(1) {
        minY = min(minY, y); maxY = max(maxY, y)
    }
}
print("ink rows: \(minY)...\(maxY) (height \(maxY - minY + 1))")

var out = "{\n"
var first = true
for (ch, r) in raw {
    let rows = r.grid[minY...maxY].map { "\"" + $0.map { String($0) }.joined() + "\"" }.joined(separator: ",")
    if !first { out += ",\n" }
    let esc = ch == "\"" ? "\\\"" : String(ch)
    out += "\"\(esc)\":{\"cols\":\(r.cols),\"rows\":[\(rows)]}"
    first = false
}
out += "\n}\n"
try! out.write(toFile: outPath, atomically: true, encoding: .utf8)
print("saved \(outPath)")
