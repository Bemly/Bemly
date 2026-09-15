import Foundation
import CoreText
import CoreGraphics

setbuf(stdout, nil)

let taskPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "pixel_task.json"
let outPath = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "gz8_glyphs.json"

let path = "/Volumes/备份/像素字体/观致 8×8 像素字体.ttf"
let url = URL(fileURLWithPath: path) as CFURL
guard let descs = CTFontManagerCreateFontDescriptorsFromURL(url) as? [CTFontDescriptor],
      let desc = descs.first else { fatalError("cannot load font") }
let SIZE: CGFloat = 64
let font = CTFontCreateWithFontDescriptor(desc, SIZE, nil)
let bb = CTFontGetBoundingBox(font)
let SCALE = Int(SIZE / 8)

func rasterize(_ ch: Character) -> (cols: Int, grid: [[Int]])? {
    var u16 = Array(String(ch).utf16)
    var glyph: CGGlyph = 0
    guard CTFontGetGlyphsForCharacters(font, &u16, &glyph, 1), glyph != 0,
          let p = CTFontCreatePathForGlyph(font, glyph, nil) else { return nil }
    let adv = CTFontGetAdvancesForGlyphs(font, .horizontal, [glyph], nil, 1)
    let cols = max(1, Int((adv / SIZE * 8).rounded()))
    let W = cols * SCALE, H = 8 * SCALE
    var t = CGAffineTransform(translationX: -bb.origin.x, y: -bb.origin.y)
    guard let moved = p.copy(using: &t) else { return nil }
    var buf = [UInt8](repeating: 0, count: W * H)
    guard let ctx = CGContext(data: &buf, width: W, height: H, bitsPerComponent: 8,
                              bytesPerRow: W, space: CGColorSpaceCreateDeviceGray(),
                              bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return nil }
    ctx.setFillColor(gray: 1.0, alpha: 1.0)
    ctx.addPath(moved)
    ctx.fillPath()
    var grid = [[Int]]()
    for gy in stride(from: 0, to: H, by: SCALE) {
        var row = [Int]()
        for gx in stride(from: 0, to: W, by: SCALE) {
            var sum = 0
            for dy in 0..<SCALE { for dx in 0..<SCALE { sum += Int(buf[(gy + dy) * W + gx + dx]) } }
            row.append(sum >= SCALE * SCALE * 255 / 2 ? 1 : 0)
        }
        grid.append(row)
    }
    return (cols, grid)
}

guard let data = try? String(contentsOfFile: taskPath, encoding: .utf8),
      let obj = try? JSONSerialization.jsonObject(with: Data(data.utf8)),
      let task = obj as? [String: Any],
      let charset = task["charset"] as? String else { fatalError("cannot read pixel_task.json") }

var out = "{\n"
var missing: [String] = []
var first = true
for ch in charset {
    guard ch != " " else { continue }  // space handled as blank advance
    if ch == "\"" || ch == "\\" { missing.append(String(ch)); continue }
    if let (cols, grid) = rasterize(ch) {
        if grid.flatMap({ $0 }).reduce(0, +) == 0 { missing.append(String(ch)); continue }
        let rows = grid.map { "\"" + $0.map { String($0) }.joined() + "\"" }.joined(separator: ",")
        if !first { out += ",\n" }
        out += "\"\(ch)\":{\"cols\":\(cols),\"rows\":[\(rows)]}"
        first = false
    } else {
        missing.append(String(ch))
    }
}
out += "\n}\n"
try! out.write(toFile: outPath, atomically: true, encoding: .utf8)
print("rasterized:", !first ? "ok" : "none", " missing:", missing.map { "'\($0)' (\($0.unicodeScalars.first!.value))" }.joined(separator: " "))
