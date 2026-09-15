# AGENTS.md — 像素字 3D 管线与合并心得

本仓库的 README 是一段嵌在 ` ```stl ` 代码围栏里的 ASCII STL：用 fusion-pixel-font 12px（proportional）把文字转成方块 voxel，只取外表面、贪心合并共面后三角化。改字号、换文案、重建模型前先读这份心得；脚本在 `scripts/`。

## 硬约束（实测）

- GitHub 主页渲染 README 约 **500KB 上限**：15MB 实测完全不渲染（见提交历史 `9fedba7`），~300KB 稳定渲染。当前签名 77KB。
- 单独打开 `.stl` 文件走 GitHub 3D 查看器，上限 ~10MB。
- 紧凑 ASCII STL 每面片约 **93 字节**。一切优化最终只看**面片数**。

## 合并心得（核心）

1. **面片数 ∝ 表面周长，与体积/尺寸无关**。贪心合并在字体设计空间（格子）完成，SCALE（每格子像素放大倍数）从 2 调到 10，面片数一个不变（实测 800 → 800）。想缩体积：换字体、改文案，调 SCALE 没用。
2. **只输出外表面**：相邻 voxel 的共享面全部剔除，只保留与空格相邻的面。内部面对渲染零贡献，一句 `neighbor in cells` 判断的事，但省一半以上。
3. **贪心合并分两类**（单格深的板）：
   - 顶/底面（±z）：对占格集合做 2D 贪心矩形 —— 先横向延伸，再整行向下延伸，用 covered 集合去重，结束后 assert 覆盖恰好等于原集合。
   - 侧墙（±x/±y）：墙只能在平面内一个方向合并 —— 同列连续行（或同 row 连续列）合并成条带；不同平面之间永远不能合并。
4. **字体选择决定面片数**：细笔画、1px 字隙的字体（观致 8×8）每个汉字 ~118 面片；2px 笔画的 16×16 位图风格（STHeiti）~50。孤立单点 6 面片/格最贵；面片数跟周长/面积比走，粗且连通的字体最省。
5. **膨胀陷阱**：对字形做 1px 膨胀实测可省 ~45% 面片，但观致字隙只有 1px，膨胀直接把字糊成实心色块，不可读，弃用。字隙 ≥2px 的字体才值得考虑。
6. **位图字体没有轮廓**：方正基础像素.ttf 之类的点阵字体只有 EBDT 位图数据，`CTFontCreatePathForGlyph` 返回 nil，全部字形提取失败。只选 outline 字体（`file` 看不出区别，跑一次探测脚本就知道）。
7. **CTLineDraw 渲染缓冲全零的坑**：CoreText 经 CTLineDraw 画进 CGBitmapContext 得到空缓冲（灰度 context，原因未查明）。改用 `CTFontCreatePathForGlyph` 拿 CGPath 再 `fillPath`，稳定 —— 栅格化一律走路径法（`scripts/rasterize_gz8.swift`）。
8. **按行独立计量**：每行文字是独立 band，行间空行天然阻断合并 → 面片成本可按行精确计价，支持"按字节预算从低优先级尾部丢行"的装配（`make_readme_stl.py` 的 drop loop）。

## ASCII STL 压缩

- 缩进全去掉：GitHub 的解析器按 token 读，省 ~20% 字节。
- 坐标以 1 方块为单位、全整数（`fmt()` 里 is_integer 判断）；法线只有 0/±1。
- 面片 winding 必须外法线 CCW：`quad(a,b,c,d)` 的顶点顺序在 `build_facets` 里按六个面逐一验证过，改动前先想清楚。
- `build_facets` 内置面积断言（合并后顶/底面积必须精确等于占格面积），动合并逻辑时别删。

## GitHub 嵌入

- README 中 ` ```stl ` 围栏 + **ASCII** STL = 官方支持的交互式 3D（旋转/线框/实体）。二进制 STL 不行。
- `![alt](xxx.stl)` 图片语法**不会**渲染成 3D，别用。
- 尺寸、单位说明写正文，别指望 alt 文本。

## 脚本（scripts/）

| 文件 | 作用 |
| --- | --- |
| `rasterize_pixel.swift` | 通用 CoreText 路径法栅格化：字符集 JSON → N-px 点阵 JSON。`swift rasterize_pixel.swift task.json out.json 12 字体.ttf`。advance 从整宽参照字（猫）自动校准，不依赖 unitsPerEm；全字符共用画布原点再统一裁剪到墨迹行，基线自然对齐。 |
| `extract_text.py` | 从指定分支 README 提取可读正文（剥徽章/HTML/emoji，LaTeX 公式转文本符号），产出 charset 与行列表。`python3 extract_text.py [repo] [out.json]`。 |
| `make_readme_stl.py` | 核心库 + 预算装配：布局（居中/分隔条/标签）、贪心合并、外表面、紧凑 ASCII。`PLAN` 是文案与优先级，`LIMIT` 是 ```stl 块字节预算，超了自动从尾部丢行。 |
| `make_signature_stl.py` | 当前 README（签名）生成器：`Bemly` / 全宽横线（1 设计像素厚）/ `猫害死好奇心。`，`SCALE=10`、`GAP=2`，重跑即再生 README.md。 |
| `fusion12_glyphs.json` | fusion-pixel 12px proportional 所需字符点阵缓存（12 个字符）。 |
| `gz8_glyphs.json` + `rasterize_gz8.swift` | 旧观致 8×8 管线，留作备用（见字体速查）。 |

## 字体速查

- **fusion-pixel-font 12px proportional**（当前）：来自 [TakWolf/fusion-pixel-font](https://github.com/TakWolf/fusion-pixel-font) Releases。CJK 全角 12 列、Latin 半宽（B=7/e=6/m=8/l=4/y=6），行高 12；字形落在像素网格上，超采样后二值化零歧义。换字符：改 charset 重跑 `rasterize_pixel.swift`。
- 观致 8×8（GuanZhi，旧）：CJK 全角 8 列、Latin 半角 4 列；每汉字 ~118 面片（细笔画 1px 字隙，周长大）；`⊗` 缺失。
- 纯位图字体（如方正基础像素）无轮廓数据，CoreText 提取全失败，见上方位图字体坑。
