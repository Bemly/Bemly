# AGENTS.md — 像素字 3D 管线与合并心得

本仓库的 README 是一段嵌在 ` ```stl ` 代码围栏里的 ASCII STL：用 fusion-pixel-font 12px（proportional）把文字转成方块 voxel（只取外表面、矩形覆盖共面后三角化），下面站着一个大肥鱼娘低多边形 3D 模型。改字号、换文案、重建模型前先读这份心得；脚本在 `scripts/`。

## 硬约束（实测）

- GitHub 主页渲染 README 约 **500KB 上限**：15MB 实测完全不渲染（见提交历史 `9fedba7`），~300KB 稳定渲染。当前 README 499,758 字节（文字 1932 + 人物 7000 三角形）。
- 单独打开 `.stl` 文件走 GitHub 3D 查看器，上限 ~10MB。
- 旧格式（标准 ASCII STL）每面片约 93–99 字节；现在的"分组格式"（见下节）方块文字约 50 字节/三角形、任意三角网格约 56 字节/三角形。剩下的优化只看**三角形数**和坐标位数。

## GitHub 解析器与省字节格式（2026-10 起）

GitHub 的 ```stl 查看器（viewscreen.githubusercontent.com 的 `3dMarkdown-*.js`）用的是 three.js `STLLoader.parseASCII`，纯正则：
`/solid([\s\S]*?)endsolid/` 里找 `/facet([\s\S]*?)endfacet/`，块内找 `normal x y z` 和所有 `vertex x y z`。于是：

- `outer loop` / `endloop` **根本不读**，删掉。
- 一个 `facet … endfacet` 块里可以放**任意多个顶点**，每 3 个连成一个三角形；块内法线对块里所有顶点生效（顶点数不是 3 只打 debug 日志）。
- 体素/像素字的面只有 6 种法线 → 整个模型只要 **6 个 facet 块**，每个三角形只剩 3 行 `vertex x y z`。
- 材质是 FrontSide 的 Phong，法线参与光照：winding 仍须外法线逆时针，法线不能省。
- 坐标用整数、单位取最小格（1 体素），全非负（不要负号）。
- 风险：这依赖 GitHub 继续用 STLLoader 的宽松解析；哪天换成严格解析器，就退回 `make_readme_stl.to_ascii` 的标准格式（体积约 ×2）。

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
8. **矩形覆盖代替矩形划分**（`voxel_stl.best_cover`）：每个轴向平面算"必须覆盖" R（外露面）和"允许覆盖" A = R ∪ 被实体包住的内部方格（两侧都实心，永远看不见）；矩形可以伸进 A、可以互相重叠（同平面同法线，叠了看不出），每个平面试横向/纵向贪心划分和"新覆盖最多"的贪心覆盖，取矩形最少的。文字 2248 → 1932 三角形。
9. **三角形 vs 四边形**：STL 只有三角形（解析器也只认三角形），一个矩形 = 2 三角形；直接三角化直角多边形要 n−2 个三角形，不比最优矩形划分少，所以都走矩形。
10. **精细模型用减面网格，不用体素**：同样字节下体素一半三角形花在阶梯上；任意三角形虽然每个贵 ~10 字节（坐标 3 位数 + 法线分组开销），但 7000 个 QEM 减面三角形比 7400 个体素三角形精细得多。像素字本身就是方块，所以文字继续走体素。
11. **任意三角形的法线分组**：块内法线对所有顶点生效，所以把三角形按法线聚到球面上 N 个均匀方向（`trimesh_stl.blocks`），每组一个 facet 块、块法线 = 组内平均（两位小数，`.5` / `-.25` 这种省 0 的写法解析器认）。N=256：平均光照误差 4.7°、每块 ~35 字节；N=1024 误差 2.2° 但多 ~26KB。
12. **坐标量化**：人物坐标 = 体素外壳格 ×2 取整（509 单位高，全 3 位数）；×1 省 3% 但量化噪声让法线乱跳，×3.5 多 2.5%。文字按 K = 人物高 / 30 字体像素 放大（K=17，x 到 1632，4 位数也就多 ~1.5KB）。
13. **按行独立计量**：每行文字是独立 band，行间空行天然阻断合并 → 面片成本可按行精确计价，支持"按字节预算从低优先级尾部丢行"的装配（`make_readme_stl.py` 的 drop loop）。

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
| `voxel_stl.py` | 新核心库：体素外表面（柱子表示 `quads` / 任意 3D `quads_occ`）→ 矩形覆盖 → 分组格式 ASCII（`to_stl`）。 |
| `dschan_voxelize.py` | 大肥鱼娘网格 → 实心体素（`voxelize()`，dschan_shell 调用）。输入是 deepseek 播放器里摆好姿势的蒙皮网格（舞蹈 100s 双手叉腰、K帧头发，脚尖方向转到 +z）用 `SkinnedMesh.getVertexPosition` 导出的 Float32 顶点 + Uint32 索引（不进仓库，~37MB）。表面按半格采样 + `binary_fill_holes` 填实（衣服下面的身体等内层自然消失）。 |
| `dschan_shell.py` | `python3 dschan_shell.py pos.f32 idx.u32 256 shell.npz`：256 格高实心体素 → 闭运算、只留最大连通体 → 外壳四边形网格。 |
| `dschan_decimate_blender.py` | `blender -b --python dschan_decimate_blender.py -- shell.npz out.npz 7000`：OpenVDB 重建（体素外壳在边相接处非流形，QEM 减不动，必须先重建）→ 拉普拉斯平滑 6 次 → QEM 塌陷到指定三角形数。 |
| `dschan/dschan_lowpoly.txt` | 选定的人物网格：7000 三角形，顶点 = 外壳格 ×2 取整。首行 `顶点数 三角形数`，然后顶点、三角形索引。换预算就改减面目标重跑上面两步。 |
| `trimesh_stl.py` | 任意三角网格 → 按法线聚类的 facet 块；`to_stl` 输出分组格式（文字和人物共用）。 |
| `make_signature_stl.py` | 当前 README 生成器：`Bemly` / `蓝莓小果冻` / 全宽横线 / `猫害死好奇心。`（字体像素 = K×K×K 方块，`GAP=2`）+ 人物（`FIG_PX=30` 字体像素高、`FIG_GAP=20` 和格言的间距 —— 默认视角下人物完全在文字下方不挡字），超过 500,000 字节直接报错，重跑即再生 README.md。 |
| `fusion12_glyphs.json` | fusion-pixel 12px proportional 所需字符点阵缓存（12 个字符）。 |
| `gz8_glyphs.json` + `rasterize_gz8.swift` | 旧观致 8×8 管线，留作备用（见字体速查）。 |

## 字体速查

- **fusion-pixel-font 12px proportional**（当前）：来自 [TakWolf/fusion-pixel-font](https://github.com/TakWolf/fusion-pixel-font) Releases。CJK 全角 12 列、Latin 半宽（B=7/e=6/m=8/l=4/y=6），行高 12；字形落在像素网格上，超采样后二值化零歧义。换字符：改 charset 重跑 `rasterize_pixel.swift`。
- 观致 8×8（GuanZhi，旧）：CJK 全角 8 列、Latin 半角 4 列；每汉字 ~118 面片（细笔画 1px 字隙，周长大）；`⊗` 缺失。
- 纯位图字体（如方正基础像素）无轮廓数据，CoreText 提取全失败，见上方位图字体坑。
