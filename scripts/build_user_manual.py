#!/usr/bin/env python3
"""Build the final Word user manual from the current project baseline.

The document is intentionally generated from repository assets so screenshots,
diagrams, page fields, bookmarks and the clickable directory stay reproducible.
"""

from __future__ import annotations

import shutil
import zipfile
from datetime import date
from html import escape
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "第4组 基于Spark的高校智慧就业大数据分析平台"
OUT_FILE = OUT_DIR / "7.用户使用手册.docx"
ASSET_DIR = ROOT / "docs/assets/project-documentation"
GEN_DIR = ROOT / "docs/assets/user-manual-generated"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
EMU = 914400


def font(size: int, bold: bool = False):
    paths = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]
    for path in paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=1 if bold else 0)
            except OSError:
                continue
    return ImageFont.load_default()


def rounded(draw, box, fill, outline=None, radius=18, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, text, fnt, fill, spacing=6):
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = left + (right - left - (bbox[2] - bbox[0])) / 2
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def arrow(draw, x1, y1, x2, y2, color="#8bc6c0", width=7):
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 > x1 else -1
        draw.polygon([(x2, y2), (x2 - sign * 18, y2 - 11), (x2 - sign * 18, y2 + 11)], fill=color)
    else:
        sign = 1 if y2 > y1 else -1
        draw.polygon([(x2, y2), (x2 - 11, y2 - sign * 18), (x2 + 11, y2 - sign * 18)], fill=color)


def canvas(title: str, subtitle: str):
    image = Image.new("RGB", (1600, 900), "#f6f8fa")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 122), fill="#102a43")
    draw.rectangle((0, 118, 1600, 122), fill="#20a39e")
    draw.text((72, 36), title, font=font(42, True), fill="#ffffff")
    draw.text((76, 88), subtitle, font=font(21), fill="#b9d9d6")
    return image, draw


def diagram_role_flow(path: Path):
    image, draw = canvas("平台使用闭环", "公开岗位数据经过 Spark 分析后，为学生、高校和管理员提供各自的操作入口")
    cards = [
        (92, 260, 390, 550, "学生端", "注册登录\n岗位筛选\n画像与推荐", "#3156a3"),
        (651, 230, 950, 580, "就业雷达", "统一登录与权限\n实时业务服务\n可解释分析", "#16807a"),
        (1210, 260, 1508, 550, "高校与管理员", "市场分析\n学生分层\n账号维护", "#c76f3d"),
    ]
    for x1, y1, x2, y2, title, detail, color in cards:
        rounded(draw, (x1, y1, x2, y2), "#ffffff", color, 24, 4)
        draw.rectangle((x1, y1, x2, y1 + 70), fill=color)
        center_text(draw, (x1, y1 + 10, x2, y1 + 60), title, font(30, True), "#ffffff")
        center_text(draw, (x1 + 20, y1 + 95, x2 - 20, y2 - 20), detail, font(28), "#243b53", 15)
    arrow(draw, 410, 405, 625, 405)
    arrow(draw, 970, 405, 1190, 405)
    rounded(draw, (380, 660, 1220, 780), "#e8f5f3", "#9dd5d0", 18, 2)
    center_text(draw, (420, 677, 1180, 760), "每次使用都基于当前可用岗位批次；推荐分反映画像与岗位证据的接近程度，不预测录用结果。", font(25), "#174e4a")
    image.save(path)


def diagram_recommendation(path: Path):
    image, draw = canvas("学生推荐的解释路径", "先过滤不适合的岗位，再返回最多 10 条可追溯的比较结果")
    steps = [
        (70, "学生画像", "学历、经历、期望\n技能作为画像记录"),
        (386, "候选岗位", "近期有效岗位\n不接受异地时限城市"),
        (702, "规则匹配", "学历硬过滤\n经历、方向、城市、薪资、行业、时效"),
        (1018, "Top10 结果", "总分排序\n命中词与六维依据"),
    ]
    colors = ["#3156a3", "#43826f", "#7a6aa6", "#c76f3d"]
    for index, (x, title, detail) in enumerate(steps):
        rounded(draw, (x, 280, x + 250, 570), "#ffffff", colors[index], 20, 4)
        draw.ellipse((x + 92, 212, x + 158, 278), fill=colors[index])
        center_text(draw, (x + 96, 217, x + 154, 272), str(index + 1), font(26, True), "#ffffff")
        center_text(draw, (x + 20, 310, x + 230, 390), title, font(30, True), colors[index])
        center_text(draw, (x + 20, 402, x + 230, 530), detail, font(22), "#243b53", 10)
        if index < 3:
            arrow(draw, x + 255, 425, x + 300, 425, "#7ab8b2", 6)
    rounded(draw, (130, 660, 1470, 780), "#fff5e8", "#e8ba73", 18, 2)
    center_text(draw, (165, 680, 1435, 760), "没有足够资料或没有满足硬条件的候选时，页面会说明缺少的资料或过滤原因；系统不以随机岗位填充结果。", font(25), "#704b16")
    image.save(path)


def diagram_batch(path: Path):
    image, draw = canvas("新岗位批次发布流程", "Raw 原始层可追溯，只有通过质量检查的完整计算结果才会进入在线服务")
    nodes = [
        (82, 320, "Raw", "公开岗位文件\n按来源/日期入库", "#3156a3"),
        (402, 320, "Spark 清洗", "去重、字段标准化\n岗位分类", "#43826f"),
        (722, 320, "统计提取", "市场统计\n技能信号", "#7a6aa6"),
        (1042, 320, "发布校验", "数量、字段、日期\n页面冒烟", "#c76f3d"),
        (1362, 320, "MySQL", "在线快照\n前端可查询", "#16807a"),
    ]
    for index, (x, y, title, detail, color) in enumerate(nodes):
        rounded(draw, (x, y, x + 190, y + 235), "#ffffff", color, 18, 4)
        center_text(draw, (x + 15, y + 24, x + 175, y + 85), title, font(25, True), color)
        center_text(draw, (x + 14, y + 105, x + 176, y + 205), detail, font(20), "#243b53", 8)
        if index < 4:
            arrow(draw, x + 198, y + 116, x + 305, y + 116, "#7ab8b2", 6)
    rounded(draw, (230, 675, 1370, 790), "#e8f5f3", "#9dd5d0", 18, 2)
    center_text(draw, (270, 692, 1330, 772), "发生作业失败、数据日期错误或抽样异常时，不发布半成品；在线端继续读取上一份完整的 MySQL 快照。", font(25), "#174e4a")
    image.save(path)


def diagram_troubleshooting(path: Path):
    image, draw = canvas("故障定位顺序", "先定位用户可见现象，再向服务、数据与基础设施逐层收敛")
    columns = [
        (85, "现象", ["无法登录", "岗位为空", "图表不显示", "学生页变慢"], "#3156a3"),
        (455, "接口与日志", ["/api/health", "浏览器网络请求", "Spring Boot 日志", "权限与 Token"], "#43826f"),
        (825, "数据与缓存", ["MySQL 当前批次", "筛选条件", "Redis PING / TTL", "统计日期"], "#7a6aa6"),
        (1195, "基础服务", ["HDFS 与 Spark", "MySQL 连接", "Redis 服务", "端口与代理"], "#c76f3d"),
    ]
    for index, (x, title, lines, color) in enumerate(columns):
        rounded(draw, (x, 210, x + 300, 650), "#ffffff", color, 20, 4)
        draw.rectangle((x, 210, x + 300, 290), fill=color)
        center_text(draw, (x, 220, x + 300, 280), title, font(29, True), "#ffffff")
        for row, line in enumerate(lines):
            top = 323 + row * 72
            rounded(draw, (x + 24, top, x + 276, top + 48), "#f3f6f8", "#d5e0e5", 10, 1)
            center_text(draw, (x + 32, top + 7, x + 268, top + 42), line, font(20), "#243b53")
        if index < 3:
            arrow(draw, x + 305, 430, x + 350, 430, "#7ab8b2", 6)
    draw.text((80, 755), "处理原则：保留原始数据与错误信息；未经验证不要直接删除缓存、覆盖 Raw 数据或修改生产凭据。", font=font(25), fill="#243b53")
    image.save(path)


def build_diagrams():
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    builders = {
        "01-role-flow.png": diagram_role_flow,
        "02-recommendation-flow.png": diagram_recommendation,
        "03-batch-release.png": diagram_batch,
        "04-troubleshooting.png": diagram_troubleshooting,
    }
    for name, builder in builders.items():
        builder(GEN_DIR / name)


def run(text: str, bold: bool = False, size: int | None = None, color: str | None = None):
    props = ""
    if bold:
        props += "<w:b/>"
    if size:
        props += f'<w:sz w:val="{size}"/>'
    if color:
        props += f'<w:color w:val="{color}"/>'
    return f"<w:r><w:rPr>{props}</w:rPr><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def paragraph(text: str = "", style: str = "BodyText", align: str | None = None,
              page_break: bool = False, bookmark: str | None = None, size: int | None = None):
    # Heading text remains unnumbered. Word can apply its own multilevel
    # numbering when the document is reused in a different template.
    if style.startswith("Heading"):
        text = re.sub(r"^(?:\d+(?:\.\d+)*|[A-Z]\.\d+)\s+", "", text)
    props = [f'<w:pStyle w:val="{style}"/>']
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    if style == "BodyText":
        props.append('<w:spacing w:after="110" w:line="360" w:lineRule="auto"/>')
        props.append('<w:ind w:firstLine="420"/>')
    if style.startswith("Heading"):
        props.append("<w:keepNext/>")
    bookmark_xml = ""
    if bookmark:
        bookmark_xml = f'<w:bookmarkStart w:id="{abs(hash(bookmark)) % 100000}" w:name="{bookmark}"/>'
        bookmark_xml += f'<w:bookmarkEnd w:id="{abs(hash(bookmark)) % 100000}"/>'
    page_break_xml = '<w:r><w:br w:type="page"/></w:r>' if page_break else ""
    return f"<w:p><w:pPr>{''.join(props)}</w:pPr>{page_break_xml}{bookmark_xml}{run(text, size=size)}</w:p>"


def bullet(text: str):
    return f'<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:after="70" w:line="330"/><w:ind w:left="500" w:hanging="250"/></w:pPr>{run("• ", True, 21, "16807A")}{run(text)}</w:p>'


def table(headers: list[str], rows: list[list[str]], widths: list[int] | None = None):
    widths = widths or [int(9360 / len(headers))] * len(headers)
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    border = '<w:top w:val="single" w:sz="6" w:color="7393A7"/><w:left w:val="single" w:sz="6" w:color="7393A7"/><w:bottom w:val="single" w:sz="6" w:color="7393A7"/><w:right w:val="single" w:sz="6" w:color="7393A7"/><w:insideH w:val="single" w:sz="4" w:color="B8C7D1"/><w:insideV w:val="single" w:sz="4" w:color="B8C7D1"/>'
    def cell(value: str, width: int, header: bool):
        shade = '<w:shd w:val="clear" w:fill="DCEBF0"/>' if header else ""
        content = f'<w:p><w:pPr><w:spacing w:after="0" w:line="260"/></w:pPr>{run(value, header, 19 if header else 18, "102A43" if header else None)}</w:p>'
        return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}<w:tcMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:start w:w="100" w:type="dxa"/><w:end w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>{content}</w:tc>'
    all_rows = [headers] + rows
    rendered = []
    for index, row in enumerate(all_rows):
        rendered.append("<w:tr>" + "".join(cell(value, widths[i], index == 0) for i, value in enumerate(row)) + "</w:tr>")
    return f'<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders>{border}</w:tblBorders><w:tblLook w:firstRow="1" w:val="04A0"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(rendered)}</w:tbl>'


def image_paragraph(rel_id: str, name: str, width_in: float = 6.3, height_in: float | None = None, doc_id: int = 1):
    path = IMAGES[rel_id]
    with Image.open(path) as image:
        ratio = image.height / image.width
    height_in = height_in or width_in * ratio
    cx, cy = int(width_in * EMU), int(height_in * EMU)
    return f'''<w:p><w:pPr><w:jc w:val="center"/><w:keepNext/></w:pPr><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{doc_id}" name="{escape(name)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{escape(name)}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''


def caption(text: str):
    return paragraph(text, "Caption", "center")


def toc_line(label: str, anchor: str, page: int):
    page_ref = (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> PAGEREF {anchor} \\h </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f'<w:r><w:t>{page}</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )
    return f'<w:p><w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:pos="9000" w:leader="dot"/></w:tabs></w:pPr><w:hyperlink w:anchor="{anchor}" w:history="1">{run(label, color="102A43")}</w:hyperlink><w:r><w:tab/></w:r>{page_ref}</w:p>'


def cover():
    items = [
        paragraph("项目编号：HD20260710SR018", "Normal", "right", size=20),
        paragraph("基于 Spark 的高校智慧就业大数据分析平台", "Title", "center", size=42),
        paragraph("用 户 使 用 手 册", "Subtitle", "center", size=34),
        paragraph("Version: Build 3.0", "Subtitle", "center", size=24),
        paragraph("", "Normal"),
        paragraph("项目承担部门：第4组", "Normal", "center", size=22),
        paragraph("撰写人：韩磊", "Normal", "center", size=22),
        paragraph("完成日期：2026-07-16", "Normal", "center", size=22),
        paragraph("适用对象：学生用户、高校就业工作人员、系统管理员、维护人员", "Normal", "center", size=20),
        paragraph("四川华迪信息技术有限公司", "Subtitle", "center", size=22),
    ]
    return "".join(items)


def front_matter():
    history = table(
        ["日期", "版本", "说明", "作者"],
        [
            ["2026-07-10", "Build0.1", "确定项目范围、角色边界与基础工程目录", "韩磊"],
            ["2026-07-11", "Build1.0", "贯通采集、HDFS、Spark、MySQL、后端与双端原型", "韩磊"],
            ["2026-07-15", "Build2.0", "完成认证、学生分层、Redis 优化及全链路回归", "韩磊"],
            ["2026-07-16", "Build3.0", "扩展完整使用、运维与故障处理说明，补充可跳转目录和图文索引", "韩磊"],
        ], [1700, 1400, 4700, 1500])
    info = table(["项目", "内容"], [
        ["文档名称", "基于 Spark 的高校智慧就业大数据分析平台用户使用手册"],
        ["适用版本", "Build3.0；以 2026-07-15 的代码、文档和测试基线为准"],
        ["岗位数据口径", "2026-07-11 公开岗位批次；当前有效岗位 12,000 条"],
        ["学生数据口径", "学生自主填写、授权匿名导入或明确标记的模拟数据；本演示队列为 100 名模拟学生"],
        ["使用限制", "不输出真实就业率、培养质量结论或录用概率；市场图表表示当前批次信号"],
    ], [2200, 7100])
    toc = "".join([
        toc_line("手册说明", "chapter1", 5),
        toc_line("登录、角色与通用规则", "chapter2", 6),
        toc_line("学生端使用说明", "chapter3", 7),
        toc_line("高校端使用说明", "chapter4", 11),
        toc_line("管理员端使用说明", "chapter5", 14),
        toc_line("运行维护与新批次发布", "chapter6", 15),
        toc_line("常见问题与故障定位", "chapter7", 17),
        toc_line("附录 A  演示账号、数据口径与检查清单", "appendix", 19),
    ])
    return "".join([
        paragraph("文档信息", "Heading1", page_break=True, bookmark="docinfo"), info,
        paragraph("修订文档历史记录", "Heading1", page_break=True, bookmark="history"), history,
        paragraph("目 录", "Title", "center", page_break=True, bookmark="toc", size=32),
        paragraph("提示：按住 Ctrl 键并单击目录条目可直接跳转到相应章节。目录页码和页脚由 Word 自动域维护；编辑后可使用“全选—更新域”同步。", "Normal", "left", size=18), toc,
    ])


def chapter1():
    return "".join([
        paragraph("1  手册说明", "Heading1", page_break=True, bookmark="chapter1"),
        paragraph("本手册面向实际使用和课程项目验收，说明如何在“学生能力与就业期望—公开岗位需求—高校就业指导”这一闭环中完成操作。它以仓库中的最新实现为依据：岗位数据由公开来源采集后进入 HDFS，经过 Pandas 与 Spark 清洗、统计和技能提取，发布到 MySQL，最终由 Spring Boot API 和 Vue 页面提供给三类角色。手册关注用户能做什么、页面结果如何理解、发生异常时先检查什么，不把尚未建设的就业跟踪或长期预测写成系统能力。"),
        paragraph("平台当前的真实主数据是公开招聘岗位。学生端的个人信息、技能、经历和就业期望只用于本人画像维护和高校在授权范围内的汇总观察；没有真实学生数据时，系统使用明确标记的模拟学生队列做流程验证。因此，岗位数量、城市热度、行业结构和薪资区间都只表示 2026-07-11 这一批公开岗位的当前信号。推荐总分反映学生已填写证据与岗位条件的接近程度，不是面试结果、录用概率或就业质量判断。"),
        image_paragraph("rIdImg01", "平台使用闭环", 6.45, doc_id=1), caption("图 1-1  学生、高校与管理员的使用闭环"),
        paragraph("1.1 适用对象", "Heading2", bookmark="c1_1"),
        table(["对象", "主要目标", "完成后可得到的结果"], [
            ["学生用户", "比较当前岗位、维护求职材料、查看推荐依据", "岗位列表、收藏、完整画像、Top10 推荐与差距提示"],
            ["高校就业工作人员", "观察市场结构、定位资料不完整学生、安排指导动作", "市场总览、需求图表、地区行业证据、学生分层与匹配证据"],
            ["系统管理员", "维护登录账号及其可用状态", "学生账号检索、启停、密码重置和高校统一账号维护"],
            ["维护人员", "保证数据批次、服务与缓存处于可用状态", "启动检查、数据发布质量门禁和故障定位线索"],
        ], [1500, 3700, 4160]),
        paragraph("1.2 使用前条件", "Heading2", bookmark="c1_2"),
        bullet("浏览器建议使用近期版本的 Chrome、Edge 或 Firefox；页面在桌面与移动宽度下均可使用，但高校多图表分析更适合桌面屏幕。"),
        bullet("访问系统前确认前端、后端和数据库已按第 6 章启动。开发环境默认前端地址为 http://localhost:5173，API 健康检查为 http://localhost:8082/api/health。"),
        bullet("学生登录需使用本人学号与密码；演示环境的模拟学生以 SIM2026001 至 SIM2026100 为账号范围。高校和管理员账号仅由维护人员提供，不能通过学生注册页面创建。"),
        bullet("首次使用学生端时，先完成基本资料、技能、经历与就业期望。推荐页面并不强迫每一项都填写，但资料缺失会降低可解释性，也可能导致系统明确显示“未计算”。"),
        paragraph("1.3 结果解释边界", "Heading2", bookmark="c1_3"),
        paragraph("学生看到的岗位市场和热门技能来自岗位文本的结构化统计，不能据此断言某项技能是唯一就业门槛。高校端“重点支持”表示基本画像、技能、经历、就业期望四类资料中缺失三至四类；“待完善”表示缺失一至两类；“资料完整”表示四类均存在。该分层是为了安排资料完善与就业指导优先级，不能作为对学生能力、家庭情况或就业困难程度的标签。资料完整学生的“匹配较好”或“常规跟进”同样只来自当前岗位匹配结果。"),
        paragraph("本手册所有示例均避免展示真实个人敏感信息。若学校后续接入授权数据，应在组织层面明确数据来源、授权范围、可见角色、保留期限和导出审批；不得将开发演示账号、默认密码或数据库密码带入生产环境。"),
    ])


def chapter2():
    return "".join([
        paragraph("2  登录、角色与通用规则", "Heading1", page_break=True, bookmark="chapter2"),
        paragraph("系统按角色隔离页面与接口权限。学生从 /login/student 进入，可使用学号和密码登录，也可以在未注册时使用“注册”页创建学生账号；高校就业工作人员从 /login/university 使用高校统一账号登录；管理员从 /admin 进入账号管理页。成功登录后，浏览器会保存登录会话并在后续 API 请求中自动携带 Bearer Token。退出登录、账号被停用或管理员重置密码后，旧 Token 会失效，用户需要重新认证。"),
        table(["角色", "入口", "登录后的起始页面", "可访问范围"], [
            ["学生", "/login/student", "岗位市场或我的工作台", "岗位、技能、地区、个人画像、Top10 推荐"],
            ["高校", "/login/university", "市场总览", "市场总览、岗位需求、地区行业、薪资技能、学生情况"],
            ["管理员", "/admin", "账号管理", "学生账号和高校统一账号维护"],
        ], [1300, 2100, 2700, 3260]),
        paragraph("2.1 学生注册与登录", "Heading2", bookmark="c2_1"),
        paragraph("在学生登录页选择“注册”，依次输入学号、姓名和至少 6 位密码后提交。注册成功即创建学生账号和基础档案，并进入学生工作台。重复学号、缺失姓名、短密码或服务端校验失败会在表单附近显示错误提示；请先改正输入而不是反复刷新。已有账号时切换回“登录”，输入学号和密码即可进入。学生不能通过登录页自行转换为高校或管理员角色。"),
        paragraph("若页面出现“正在验证”后没有立即跳转，前端会在错误密码、服务不可达或请求超过 15 秒时结束加载状态并显示可恢复提示。此时应确认账号角色是否正确，再检查 /api/health 是否返回正常。如果健康检查正常而仍无法登录，维护人员应查看后端认证日志和账号启用状态。不要把密码写入截图、工单标题或公共群聊。"),
        paragraph("2.2 高校与管理员登录", "Heading2", bookmark="c2_2"),
        paragraph("高校端只接受统一的高校账号；登录后默认进入市场总览，顶部标签可切换到其他分析页面。管理员登录入口与门户入口分离，避免普通用户误进入账号维护功能。管理员页面会先验证管理员密码，再加载账号列表。任何角色使用浏览器后退、前进或刷新时，系统会根据 URL 恢复当前页面、标签和页码，例如学生岗位市场的第几页或高校学生情况的第几页。若会话已经过期，系统会回到相应登录入口。"),
        paragraph("2.3 通用页面交互", "Heading2", bookmark="c2_3"),
        bullet("筛选项通常会改变列表或图表的查询范围。岗位市场修改关键词、城市或岗位方向后会回到第 1 页，避免原页码在新结果中失效。"),
        bullet("列表分页不会强制跳回页面顶部；高校学生情况在加载下一页时保留当前列表并显示覆盖式加载状态，减少页面高度变化。"),
        bullet("岗位详情使用右侧抽屉展示。点击岗位卡片打开，按 Esc 或点击关闭按钮退出；原岗位链接会在新页面打开，链接可用性由公开来源决定。"),
        bullet("收藏仅保存在当前浏览器的本地存储中，用于个人浏览偏好；清除浏览器数据、更换浏览器或设备后收藏不会自动迁移。"),
        paragraph("2.4 数据状态与提示", "Heading2", bookmark="c2_4"),
        paragraph("页面会尽量把数据状态说清楚。正常接口返回时展示当前批次的真实统计；开发联调中如果后端不可达，部分学生市场组件可能展示明确标识的演示数据，提示不会把演示数据伪装成真实市场结果。高校端市场分析的页面说明会给出统计日期和数据来源；发现数据日期不一致、岗位总数突然为零或图表与列表明显不一致时，应停止基于该页面做结论，并按第 7 章先检查批次发布状态。"),
    ])


def chapter3():
    return "".join([
        paragraph("3  学生端使用说明", "Heading1", page_break=True, bookmark="chapter3"),
        paragraph("学生端的推荐使用顺序是“先看市场，再补充画像，最后比较推荐依据”。岗位列表提供主动探索入口，个人画像提供可修改的个人证据，推荐页面把这些证据与当前有效岗位进行匹配。建议每次新增项目、实习、获奖或改变期望城市后重新进入推荐页观察结果变化；不建议为了提高分数编造经历，系统需要的是可解释、可核对的求职准备信息。"),
        paragraph("3.1 岗位市场与组合筛选", "Heading2", bookmark="c3_1"),
        paragraph("进入“岗位市场”后，页面按卡片展示岗位名称、企业、城市、岗位方向、薪资、学历和经验要求。用户可以输入关键词，并按城市和岗位方向组合筛选。关键词适合填写岗位名称、技术词或公司名称的一部分；城市和方向适合缩小范围。筛选条件提交后，系统以 12 条为一页展示岗位。若结果少于预期，先清除一个限制条件，再逐步增加关键词，而不是在多个互斥条件下直接判断“没有岗位”。"),
        image_paragraph("rIdImg02", "学生岗位市场", 6.45, doc_id=2), caption("图 3-1  学生岗位市场、关键词与组合筛选"),
        paragraph("点击任一岗位卡片会打开详情抽屉。详情中包含岗位基础信息、岗位描述和原岗位链接；建议重点对照岗位职责、学历门槛、经验要求和薪资区间。薪资缺失或无法稳定解析时，系统以“薪资面议”或缺失状态呈现，不应自行按零薪资理解。岗位可能被来源方下架，原链接不能打开时不影响平台内的历史展示，但不代表该岗位仍在招聘。"),
        paragraph("学生可点击收藏按钮标记需要复看的岗位。收藏的作用是辅助个人比较，并不向企业投递简历，也不影响推荐排序。使用岗位市场时应把列表理解为当前公开信息集合，而不是学校保证的职位名册；后续投递、沟通和隐私保护仍需由学生在公开平台或企业官方渠道完成。"),
        paragraph("3.2 热门技能与地区机会", "Heading2", bookmark="c3_2"),
        paragraph("“技能信号”页面将岗位文本中提取到的热门技能按分页展示，每页 8 项。点击某项技能可以查看其在当前批次中的相对热度。该页面用于帮助学生理解市场经常出现的技术或能力词，并不能证明所有目标岗位都要求该技能，也不会根据岗位文本自动判断学生是否掌握该能力。学生应结合专业方向、岗位详情和自身学习计划决定是否补强。"),
        paragraph("“地区机会”页面用于比较不同省市在当前批次的岗位量和薪资范围。页面的颜色、柱形或数值只反映公开岗位记录的分布，可能受到采集来源、发布时间和字段完整度影响。地区岗位多不等于录用机会必然更高，薪资上限也不能替代生活成本、岗位要求或个人意愿。比较地区时，建议先关注目标城市的岗位方向和学历要求，再查看薪资区间作为辅助信息。"),
        image_paragraph("rIdImg03", "学生地区机会", 6.45, doc_id=3), caption("图 3-2  学生端地区机会分布与市场信号"),
        paragraph("3.3 维护基本画像", "Heading2", bookmark="c3_3"),
        paragraph("进入“我的工作台”的“画像与期望”标签，先补齐姓名、学院、专业、学历和毕业年份等基本信息。基本信息是推荐中的学历筛选和方向解释的基础。学历字段要与在读或已获得的实际学历一致；毕业年份用于帮助学校识别队列状态，但不会把学生自动归入某种就业结论。保存后重新进入页面，应能看到已保存字段；若没有保存成功，先检查网络错误提示，再避免连续点击提交。"),
        paragraph("技能以 1 至 5 级维护，等级含义应按个人可证明的熟练程度填写。例如，能够独立完成课程项目、阅读文档并定位常见问题的技能可填写较高等级；仅接触过概念或没有实践证据的技能应如实填写较低等级。系统保存技能是为了形成个人准备记录和高校指导线索；当前推荐服务不会把岗位技能抽取结果直接当作学生能力的负面判定。技能列表支持分页，添加、编辑和删除后均应检查列表是否已刷新。"),
        image_paragraph("rIdImg04", "学生完整画像", 6.45, doc_id=4), caption("图 3-3  个人信息、技能、实践经历与就业期望维护"),
        paragraph("3.4 添加项目、实习与获奖经历", "Heading2", bookmark="c3_4"),
        paragraph("实践与成果区域支持项目、实习和获奖三类结构化经历。新增时填写标题、角色或岗位、起止时间和成果描述。描述应尽量写清自己负责的任务、使用的工具或方法、可核对的产出和协作范围，例如“负责 Spark 清洗规则验证，完成字段缺失率统计并输出质量报告”，而不是只写“参加项目”。经历可编辑或删除，日期选择器用于减少格式不一致；开始时间不能晚于结束时间。"),
        paragraph("推荐中的经历相关性会读取经历标题、角色和成果描述中的领域词，并将命中的词作为解释证据之一。因此，真实、具体的描述既便于学生复盘，也使推荐理由更容易理解。奖项不应被描述成虚构工作经验；如果经历尚未完成，可在描述中说明当前阶段和成果。保存后，学生可回到推荐页观察命中词和经历分是否发生合理变化。"),
        paragraph("3.5 设置就业期望", "Heading2", bookmark="c3_5"),
        paragraph("就业期望包含目标岗位、期望城市、期望行业、最低月薪以及是否接受异地。最低月薪表示学生可接受的下限，不是期望区间的最大值；请不要填写没有现实依据的极端数值。若选择不接受异地，候选岗位会先受城市条件约束，结果可能明显减少。期望岗位和行业用于解释推荐中的方向与行业维度，不应使用过于宽泛、彼此矛盾的表述。保存后，系统会在下一次请求中使用最新的期望。"),
        paragraph("3.6 查看 Top10 推荐与依据", "Heading2", bookmark="c3_6"),
        paragraph("切换到“Top10 推荐”后，系统最多返回 10 条岗位。候选池只读取当前有效岗位；学历不满足要求时直接排除。其余岗位按经历 40 分、方向 30 分、城市 10 分、最低期望薪资 10 分、行业 5 分、时效 5 分构成的六维总分排序。总分相同的岗位按稳定键排序，避免每次打开页面都无原因改变顺序。技能不进入当前排序分，但仍可作为学生自我完善和市场观察的资料。"),
        image_paragraph("rIdImg05", "学生推荐", 6.45, doc_id=5), caption("图 3-4  学生 Top10 推荐、六维得分与经历命中依据"),
        image_paragraph("rIdImg06", "推荐解释流程", 6.45, doc_id=6), caption("图 3-5  推荐从候选生成到可解释 Top10 的流程"),
        paragraph("展开某条推荐可查看推荐依据、经历命中词和六维得分。正确的使用方式是比较多条岗位为什么不同，而不是只追逐最高分：一条岗位可能方向相近但薪资下限不足，另一条岗位可能城市符合但经历证据较弱。若页面显示“未计算”，应查看缺项原因，通常是基本画像、技能、经历或就业期望未达到计算条件，或者学历与城市等硬条件使候选为空。补全真实资料或适当调整期望后再试，不要把空结果误认为系统故障。"),
        paragraph("3.7 学生端建议操作节奏", "Heading2", bookmark="c3_7"),
        table(["时点", "建议动作", "检查重点"], [
            ["首次登录", "浏览岗位市场，保存基本画像", "账号、专业、学历、毕业年份是否正确"],
            ["完成课程项目或实习后", "补充经历、技能与成果描述", "角色、日期、技术和结果是否可核对"],
            ["准备投递前", "设置期望并查看 Top10", "学历、城市、最低薪资、推荐依据是否符合实际"],
            ["每次新批次发布后", "重新比较市场与推荐", "统计日期是否变化，原收藏是否仍需要复看"],
        ], [1900, 3900, 3560]),
    ])


def chapter4():
    return "".join([
        paragraph("4  高校端使用说明", "Heading1", page_break=True, bookmark="chapter4"),
        paragraph("高校端不是就业结果统计系统，而是面向就业指导工作者的“当前岗位需求 + 学生准备状态”观察工具。使用时应先确认数据日期、来源和筛选范围，再根据岗位结构形成就业信息推送、课程实践、咨询安排或校企对接的工作线索。高校端现保留市场总览、岗位需求、地区行业、薪资技能和学生情况五个板块；已移除没有可靠数据基础的“专业方向”独立板块，因此不要在该版本中寻找该入口。"),
        paragraph("4.1 市场总览", "Heading2", bookmark="c4_1"),
        paragraph("高校登录后默认打开市场总览。页面集中展示岗位总量、企业数量、城市数、行业数、薪资概况、应届友好岗位、热门地区、行业、学历要求、企业规模、岗位大类和热门技能等指标。首先查看统计日期和数据来源，确认页面读取的是当前有效批次；再结合筛选条件判断指标是否只代表某个城市、行业或学历层级。页面中的建议是由当前岗位结构推导的辅助提示，应由就业工作人员结合学校专业设置、毕业生规模和本地产业政策进一步验证。"),
        image_paragraph("rIdImg07", "高校市场总览", 6.45, doc_id=7), caption("图 4-1  高校端市场总览与数据质量说明"),
        paragraph("数据质量区域可查看原始记录数、清洗后记录数、剔除数量、重复岗位标识、字段缺失率、薪资解析状态和统计说明。该区域的用途是提醒用户结论依赖什么样的数据质量，而不是用一张图掩盖字段缺失。若筛选后样本量很小，图表的相对变化可能被放大，应回到总量和日期判断后再做工作安排。所有高校结论都应避免写成“就业率已提高”“某专业就业困难”等超出当前公开岗位数据支持范围的陈述。"),
        paragraph("4.2 岗位需求多视图", "Heading2", bookmark="c4_2"),
        paragraph("进入“岗位需求”后，可在排行、树图、流向、气泡、热力和雷达之间切换。顶部筛选条件会联动影响当前图表。排行适合快速识别数量靠前的岗位；树图适合比较岗位大类和细分方向的面积关系；流向图展示“大类—细分方向—需求层级”的链路；气泡图适合同时观察需求量与薪资或其他数值；热力图用于发现地区、行业或类别的密集组合。切换图表时，先确认图例与 Tooltip 中的单位，避免把颜色深浅直接理解为比例。"),
        image_paragraph("rIdImg08", "高校岗位需求", 6.45, doc_id=8), caption("图 4-2  岗位需求多视图与联动筛选"),
        paragraph("雷达图使用当前 Top20 岗位的相对指数，维度包括需求热度、薪资下限、薪资中位、薪资上限和薪资跨度，统一转换为 0 至 100 的相对尺度。其目的是帮助比较同一筛选范围内的岗位，不是展示真实百分比。鼠标悬停提示会同时展示原始值与指数，做汇报或指导时应优先引用原始薪资和岗位数量，并把“相对指数”解释为可视化比较尺度。Sankey 流向图的节点使用唯一 ID，已避免“其他→其他”自环；若图表不显示，按第 7 章检查接口响应和浏览器控制台。"),
        paragraph("4.3 地区与行业分析", "Heading2", bookmark="c4_3"),
        paragraph("地区与行业页面以中国地图、城市指标、地区岗位结构占比、行业热力等方式展示公开岗位分布。点击或选择地区后，页面会同步显示该地区的岗位量、薪资区间和行业特点。系统还列出区域产业与高校工作提示，但这些提示是公开岗位与公开地区资料形成的观察框架，不是学校毕业去向数据。用于就业指导时，可将“岗位密集地区”作为信息推送或校企调研的优先级，将“学历门槛和方向结构”作为课程实践或辅导主题，而不是将它们直接等同于学生就业结果。"),
        paragraph("4.4 薪资、学历与技能", "Heading2", bookmark="c4_4"),
        paragraph("“薪资技能”板块显示十大行业薪资分布，按岗位名称和岗位描述关键词依次归入金融、商贸与消费、医药生物、科技、制造业、农业与食品、服务业、建筑与房地产、教育和其他十类。图中的岗位量、有效薪资样本、平均月薪及薪资桶可随地区联动。薪资采用月薪上下限中位等统一口径，缺失薪资的岗位不会被当作零薪资；因此解释某行业时，要同时查看岗位量和有效薪资样本数，不能只比较一条平均线。"),
        paragraph("学历和热门技能区块适合与岗位类别一起阅读。学历统计反映招聘文本中出现的教育要求，不能替代学校的培养目标；热门技能来自岗位文本的提取，适合帮助就业中心组织专题讲座、实训资源或岗位信息标签。任何培训建议都应结合学生实际课程、问卷或授权画像数据，不应只因某项技能出现频率高就要求所有学生同一方向学习。"),
        paragraph("4.5 学生情况、搜索与互斥分层", "Heading2", bookmark="c4_5"),
        paragraph("“学生情况”页面用于查看学生已保存的基本画像、技能、经历与就业期望是否足以支持推荐与指导。页面支持按姓名、学号、学院或专业搜索，并可按状态筛选。当前 100 名模拟学生按互斥规则分层：四类资料缺 3 至 4 类的为“重点支持”，缺 1 至 2 类的为“待完善”，四类都存在的为“资料完整”。资料完整后，再依据当前岗位匹配分显示“匹配较好”或“常规跟进”；资料不完整的学生不应被强行计算匹配分。"),
        image_paragraph("rIdImg09", "高校重点支持学生", 6.45, doc_id=9), caption("图 4-3  高校端重点支持学生、缺项原因与搜索筛选"),
        image_paragraph("rIdImg10", "高校资料完整学生", 6.45, doc_id=10), caption("图 4-4  高校端资料完整学生、最佳岗位和匹配证据"),
        paragraph("每页显示 10 名学生。对重点支持或待完善学生，应优先查看页面列出的缺项原因，例如未维护基本画像、技能清单、实践经历或就业期望，并以补充资料、个别咨询和资源推荐为主要动作。对资料完整学生，可查看最佳岗位、Top5 平均分和已有证据，用来准备有针对性的岗位推送或模拟面试建议。显示“未计算”时应保留原因，不要把它归结为学生能力不足。高校端展示的是学生最后一次保存的资料，页面不提供批量修改学生画像的功能。"),
        paragraph("4.6 缓存与刷新预期", "Heading2", bookmark="c4_6"),
        paragraph("高校学生情况采用服务端真实分页，并使用 Redis 缓存完整的分页响应。缓存键包含版本号、页码、每页数量、状态和搜索词摘要，默认 TTL 为 5 分钟。学生注册、修改画像、技能、经历、就业期望或账号启用状态后，系统在数据库事务提交后递增版本号，旧缓存自然失效；因此重新查询时可能看到较短的加载过程。Redis 不可用时系统自动回源 MySQL，页面仍应可用，只是首次查询会更慢。不要为了刷新页面直接使用 Redis 的 KEYS 或批量删除全部缓存。"),
        paragraph("4.7 高校端建议工作流", "Heading2", bookmark="c4_7"),
        table(["工作场景", "建议查看顺序", "产出示例"], [
            ["周度市场观察", "数据日期 → 总览 → 需求排行 → 地区行业", "本周岗位方向与地区信息推送主题"],
            ["专题就业指导", "岗位需求 → 学历/薪资/技能 → 学生情况搜索", "面向目标学院的辅导问题清单"],
            ["资料完善提醒", "学生情况 → 重点支持/待完善 → 缺项原因", "需要补充画像、经历或期望的学生名单"],
            ["校企对接准备", "地区行业 → 热门岗位 → 企业规模与薪资样本", "待进一步核验的产业、企业和岗位方向线索"],
        ], [1900, 4000, 3460]),
    ])


def chapter5():
    return "".join([
        paragraph("5  管理员端使用说明", "Heading1", page_break=True, bookmark="chapter5"),
        paragraph("管理员端的职责是维护平台账号与登录状态，不承担批量编辑学生画像、手工修改岗位统计或绕过高校权限查看不必要数据。管理员从 /admin 登录后可检索学生与高校统一账号、查看账号状态、启用或停用账号、重置密码以及维护高校统一账号凭据。所有密码在后端以 BCrypt 哈希保存，界面与数据库不应记录明文密码。"),
        image_paragraph("rIdImg11", "管理员账号管理", 6.45, doc_id=11), caption("图 5-1  管理员端学生与高校账号维护"),
        paragraph("5.1 查询与分页", "Heading2", bookmark="c5_1"),
        paragraph("进入管理端后，可在搜索框中按学生姓名、学号或账号检索，并按启用状态筛选。账号列表支持分页，避免一次加载全部账号。查询到目标账号后先核对显示名称、角色、学号关联和最后更新时间，再执行状态或密码动作。演示数据中的 SIM2026 前缀明确表示模拟学生，不应把它作为真实学号口径。高校账号应使用统一命名，避免多人共用不受控的管理员账号。"),
        paragraph("5.2 启用、停用与会话失效", "Heading2", bookmark="c5_2"),
        paragraph("停用学生账号后，系统会立即删除该账号的旧会话，已登录的用户在下一次请求时需要重新认证；重新启用后用户也需重新登录。停用动作适合处理账号误建、演示队列清理或临时权限冻结，不应用于对学生求职状态作结论。执行前应确认账号身份，执行后可在列表状态和重新登录行为中验证结果。若停用后仍可持续访问，优先检查 Token 缓存、后端会话删除日志和是否操作了正确环境。"),
        paragraph("5.3 重置密码与高校账号维护", "Heading2", bookmark="c5_3"),
        paragraph("重置密码会写入新的 BCrypt 哈希并使旧 Token 失效。管理员应通过安全渠道把临时密码通知给本人，并要求其首次登录后修改为不与其他系统重复的密码；不要把密码写入群公告、截图或长期文档。高校统一账号可修改用户名和密码，但应保证与学校授权的使用人员一致。管理员不能通过此页面批量改写学生技能、经历和就业期望，避免用账号管理功能替代学生本人或授权流程。"),
        paragraph("5.4 管理操作后的核验", "Heading2", bookmark="c5_4"),
        table(["操作", "立即检查", "预期结果"], [
            ["搜索账号", "关键词、角色、分页和筛选状态", "只返回匹配账号，列表不溢出页面"],
            ["停用账号", "列表状态、旧会话、重新访问受限页面", "账号显示停用，旧会话失效"],
            ["启用账号", "状态与登录页", "账号可重新登录，旧会话不自动恢复"],
            ["重置密码", "安全通知、旧 Token、本人重新登录", "原密码失效，新密码可认证"],
            ["维护高校账号", "账号名称、角色与授权人员", "高校端只能在有效统一账号下访问"],
        ], [1800, 3900, 3660]),
    ])


def chapter6():
    return "".join([
        paragraph("6  运行维护与新批次发布", "Heading1", page_break=True, bookmark="chapter6"),
        paragraph("本章面向维护人员。平台采用“离线大数据处理 + 在线业务查询”的组合：HDFS 保存原始数据与计算结果，Spark 批量清洗、统计和提取，MySQL 保存前端查询的结构化快照，Redis 保存会话与高频分页响应，Spring Boot 提供统一 API，Vue 负责交互展示。浏览器不直接查询 HDFS，也不会在每次打开页面时运行 Spark。这样的分层使原始数据可追溯、清洗规则可重算、在线查询可分页，并在 Redis 故障时回源 MySQL。"),
        paragraph("6.1 启动顺序与成功标志", "Heading2", bookmark="c6_1"),
        table(["顺序", "操作", "成功标志", "常用检查"], [
            ["1", "启动 HDFS 与 Spark Master/Worker", "jps 可见核心进程；9870、8080/8081 可访问", "hdfs dfsadmin -report；Spark Master Web UI"],
            ["2", "检查 MySQL 与 Redis", "MySQL 可连接；Redis PING 返回 PONG", "数据库连接测试；redis-cli ping"],
            ["3", "启动 Spring Boot", "/api/health 正常；端口 8082 监听", "后端启动日志与健康检查"],
            ["4", "启动 Vue/Vite", "端口 5173 可访问；/api 代理连通", "浏览器网络请求与前端控制台"],
            ["5", "三角色冒烟", "登录、岗位、推荐、高校学生页和账号管理可用", "学生/高校/管理员各一条核心路径"],
        ], [700, 2600, 3100, 2960]),
        paragraph("当前单虚拟机演示中，HDFS NameNode RPC 默认使用 9000，NameNode Web 使用 9870，Spark Master 使用 7077，Spark Master Web 使用 8080，Spring Boot 固定使用 8082，MySQL 使用 3306，Redis 使用 6379，Vite 开发服务使用 5173。后端不使用 8080，是为了避免与 Spark Master Web UI 冲突。数据库账号、密码和 JDBC 地址仅通过环境变量传入服务，仓库中不保存真实凭据。"),
        paragraph("6.2 发布新的岗位数据批次", "Heading2", bookmark="c6_2"),
        paragraph("发布前应为每一来源确定明确日期，并把原始文件和必要字典放入 HDFS Raw 的 source/date 分区。Raw 层是追溯和重算的依据，不能为了节省空间直接覆盖。之后依次执行 job_cleaning.py、market_statistics.py、skill_extraction.py、export_to_mysql.py。清洗任务负责统一字段、标准化地区和行业、去重并生成可用于业务的岗位快照；统计与技能任务生成市场分析指标；导出任务将完整结果写入 MySQL。任何一个关键作业失败时，不发布半成品。"),
        image_paragraph("rIdImg12", "岗位批次发布", 6.45, doc_id=12), caption("图 6-1  新岗位批次从 Raw 到在线 MySQL 快照的发布门禁"),
        paragraph("发布完成后至少核对四组结果：第一，来源总量、清洗后总量和剔除量是否能解释；第二，岗位名称、企业、城市、薪资、学历、行业等核心字段抽样是否正确；第三，技能明细和市场统计数量是否生成；第四，MySQL 中的数据日期、岗位列表、市场总览和高校图表是否一致。当前已记录的 2026-07-11 基线为四源统一有效岗位 12,000 条、岗位技能明细 2,505 条、市场统计明细 588 条。新的批次不必等于该数量，但需要能说明差异原因。"),
        paragraph("6.3 缓存、会话与数据一致性", "Heading2", bookmark="c6_3"),
        paragraph("Redis 只用于会话和高频结果缓存，不是正式数据的唯一存储。高校学生情况的缓存 TTL 为 5 分钟，键包含版本号、页码、数量、状态和搜索词摘要。学生资料或账号状态变化后，服务在事务提交后递增版本号，让旧条目自然过期；新岗位批次发布后，应清除市场统计和高校统计缓存，使页面读取新快照。Redis 读写异常时，后端回源 MySQL，不应导致核心页面完全不可用。维护时不要使用 KEYS 扫描大范围键，也不要把 Redis 当作永久历史库。"),
        paragraph("会话使用 Token 哈希在 Redis 中保存。退出、停用或密码重置都会使旧会话失效。若用户报告“退出后仍显示已登录”，应先确认浏览器本地保存的状态是否被前端清除，再验证后端是否拒绝旧 Token；不要仅凭页面按钮状态判断认证是否已经结束。测试和演示账号的默认密码只能用于本地环境，部署到多人可访问环境前必须替换。"),
        paragraph("6.4 发布后的回归检查", "Heading2", bookmark="c6_4"),
        bullet("学生端：登录后确认岗位总数、关键词筛选、岗位详情抽屉、地区页、完整画像和 Top10 推荐均能返回当前批次结果。"),
        bullet("高校端：确认总览日期、岗位需求六种视图、地区行业、十大行业薪资和学生情况分页均无接口错误；雷达 Tooltip 能显示原始值和指数口径。"),
        bullet("管理员端：确认账号列表查询、状态筛选、启停和密码重置路径正常；不要在生产环境以默认演示密码完成验收。"),
        bullet("服务与日志：确认 Redis 可用时缓存命中与回源日志合理；停止 Redis 后高校学生页仍能查询；恢复 Redis 后缓存会由请求自动重建。"),
        paragraph("6.5 数据安全与变更记录", "Heading2", bookmark="c6_5"),
        paragraph("每次数据发布应记录数据日期、来源、原始数量、清洗数量、剔除原因、任务命令、校验人和发布结论。规则变化需要保留变更说明，并从对应 Raw 分区重算，而不是仅在 MySQL 手工改数。学生数据只在学生本人维护或学校授权的范围内使用；日志与截图应避免出现密码、Token、数据库连接串和可识别个人信息。课程演示与真实运行环境应分开管理，演示环境的 SIM2026 数据可按提供的 SQL 清理脚本独立删除。"),
    ])


def chapter7():
    return "".join([
        paragraph("7  常见问题与故障定位", "Heading1", page_break=True, bookmark="chapter7"),
        paragraph("出现问题时，应从用户可见现象开始，依次检查接口、日志、数据和基础服务，而不是直接重启所有进程或删除数据。先记录发生时间、角色、访问 URL、筛选条件、浏览器报错和是否可复现，再在安全范围内做最小检查。对于涉及账号、密码、个人信息或生产数据的问题，优先保留证据并联系有权限的维护人员，避免在不明原因下清除会话、缓存或 Raw 数据。"),
        image_paragraph("rIdImg13", "故障定位顺序", 6.45, doc_id=13), caption("图 7-1  从现象到基础服务的故障定位顺序"),
        paragraph("7.1 登录失败或反复回到登录页", "Heading2", bookmark="c7_1"),
        paragraph("先确认访问的入口与账号角色一致：学生使用 /login/student，高校使用 /login/university，管理员使用 /admin。检查账号是否被停用、密码是否已重置，以及 /api/health 是否正常。若健康检查不可用，问题通常位于后端、端口或代理；若健康检查正常但登录返回 401，检查账号、密码与后端认证日志；若登录成功后马上跳回入口，检查 Token 保存、Redis 会话和系统时间。前端已对超时进行恢复处理，用户不需要不断刷新页面。"),
        paragraph("7.2 岗位列表为空、总数异常或筛选不生效", "Heading2", bookmark="c7_2"),
        paragraph("先清除关键词、城市和岗位方向，验证是否能看到基础列表；再检查浏览器网络请求中的 /api/jobs 参数和响应。若接口返回空数据，维护人员应核对 MySQL 当前有效岗位数量、数据日期、job_status 和发布任务是否完成。岗位市场的筛选修改后会回到第 1 页，这属于正常行为；如果用户仍停留在很大的旧页码，检查 URL 同步和前端状态。不要通过直接修改前端展示数字来掩盖发布失败。"),
        paragraph("7.3 推荐未计算、结果很少或排序与预期不同", "Heading2", bookmark="c7_3"),
        paragraph("学生应先检查基本画像、技能、实践经历和就业期望是否已保存。推荐需要在当前有效岗位中找到满足学历硬门槛的候选；选择不接受异地会限制城市，过高最低薪资或非常窄的期望方向也可能减少候选。结果页会展示缺项或过滤原因，应以该说明为准。排序由经历、方向、城市、薪资、行业和时效六维共同决定，最高分不等于唯一合适岗位。技能记录不会直接进入当前排序分，因此仅增加一项技能后结果不一定变化。"),
        paragraph("7.4 高校学生情况变慢或刚更新资料仍显示旧数据", "Heading2", bookmark="c7_4"),
        paragraph("高校学生页只计算当前页推荐，并使用 Redis 分页缓存。先检查请求是否命中正确页码、状态和搜索词，随后检查 Redis PING、TTL、后端的 cache hit/cache miss 日志和 MySQL 查询耗时。学生资料更新后会通过版本号让旧缓存失效，下一次查询可能比缓存命中慢，但不应长期显示过期内容。Redis 不可用时回源 MySQL 是预期降级，页面可用但响应时间会增加；不要因为变慢就删除所有缓存键。"),
        paragraph("7.5 图表空白、Sankey 无法渲染或地图数据异常", "Heading2", bookmark="c7_5"),
        paragraph("先查看浏览器控制台和对应高校接口响应，确认统计日期、筛选参数和数组结构存在。岗位需求图表的流向节点使用唯一 ID，若再次出现自环或节点重复，需要检查后端数据归并而不是手工修改画布。雷达图的 0 至 100 是相对指数，Tooltip 应同时有原始值；如果 Tooltip 缺失，检查图表配置与前端构建版本。地图数据异常时检查地区名称标准化和 china.geo.json 是否被正确加载。任何图表故障都不应通过虚构默认数值伪装为正常。"),
        paragraph("7.6 Spark、HDFS、MySQL 或 Redis 不可用", "Heading2", bookmark="c7_6"),
        table(["现象", "优先检查", "处理原则"], [
            ["Spark 无 Worker", "Spark Master Web UI、jps、Worker 日志、spark:// 地址", "确认 Worker 注册与资源，不发布失败作业结果"],
            ["HDFS 目录或文件不可见", "NameNode、hdfs dfs -ls、权限、source/date 路径", "保留 Raw，纠正路径后重跑目标日期计算"],
            ["MySQL 连接失败", "服务状态、环境变量、端口 3306、连接池日志", "不要把真实密码写入命令历史或仓库"],
            ["Redis 不可用", "redis-cli ping、端口 6379、后端回源日志", "允许回源 MySQL，恢复后等待请求重建缓存"],
            ["前端 API 失败", "Vite 代理、8082 健康检查、浏览器网络面板", "先定位前端、代理或后端边界再重启"],
        ], [1850, 4100, 3410]),
        paragraph("7.7 提交问题时应附带的信息", "Heading2", bookmark="c7_7"),
        bullet("发生时间、使用角色、访问页面 URL、操作步骤与是否每次都能复现。"),
        bullet("浏览器版本、网络请求状态码和不含密码/Token 的错误截图。"),
        bullet("当前数据日期、筛选条件、页码，以及问题发生前是否刚发布新批次或修改学生资料。"),
        bullet("后端、Spark、Redis 或数据库相关日志的最小必要片段，注意脱敏连接串与个人信息。"),
    ])


def appendix():
    return "".join([
        paragraph("附录 A  演示账号、数据口径与检查清单", "Heading1", page_break=True, bookmark="appendix"),
        paragraph("A.1 演示账号", "Heading2", bookmark="a1"),
        paragraph("本项目提供 100 名用于本地验证的模拟学生，账号范围为 SIM2026001 至 SIM2026100，初始密码为 Student@123。该密码只用于本地演示与开发，不得用于生产环境或真实学生账号。模拟学生覆盖信息工程、大数据、经管、智能制造等学院和多种资料完整度，用于验证注册、画像、推荐、高校分页和管理操作。高校与管理员账号不在本手册中写入明文，应由环境维护人员通过受控渠道提供。"),
        paragraph("A.2 当前数据基线", "Heading2", bookmark="a2"),
        table(["项目", "当前基线", "解释"], [
            ["公开岗位", "12,000 条", "四源统一后的当前有效岗位，随新批次变化"],
            ["NCSS 原始合并", "10,834 条", "2026-07-11 原始合并记录"],
            ["NCSS 第一版清洗", "10,809 条，剔除 25 条", "用于说明清洗质量而非长期趋势"],
            ["岗位技能明细", "2,505 条", "从岗位文本提取的市场信号"],
            ["市场统计明细", "588 条", "用于高校市场图表和聚合指标"],
            ["模拟学生", "100 人", "明确标记的演示队列，不代表真实毕业生去向"],
        ], [2200, 2600, 4560]),
        paragraph("A.3 最小验收清单", "Heading2", bookmark="a3"),
        bullet("学生：可注册或登录、可筛选岗位、可打开详情、可保存画像和期望、可查看解释型 Top10 推荐。"),
        bullet("高校：可看到标明日期的市场总览、切换岗位需求视图、查看地区行业与薪资技能、搜索并分页查看学生情况。"),
        bullet("管理员：可登录、检索账号、完成启停与密码重置，并验证旧会话失效。"),
        bullet("维护：可从 Raw 数据运行 Spark 处理并发布 MySQL 快照；Redis 中断时高校学生页能够回源查询。"),
        paragraph("A.4 文档维护说明", "Heading2", bookmark="a4"),
        paragraph("本手册由 scripts/build_user_manual.py 生成，真实页面截图来自 docs/assets/project-documentation，统一风格的操作图由脚本生成至 docs/assets/user-manual-generated。功能、数据口径或入口发生变化时，应先更新 README、最新项目文档和测试，再修改本脚本中相应章节并重新生成 DOCX。目录条目是 Word 内部超链接；页脚使用 PAGE 字段。若在不同版本 Word 中打开后字段未立即刷新，可执行“全选—更新域”使页码字段重新计算。"),
    ])


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
  <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/><w:sz w:val="21"/></w:rPr></w:rPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:eastAsia="宋体"/><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="正文"/><w:basedOn w:val="Normal"/><w:rPr><w:rFonts w:eastAsia="宋体"/><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="标题"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="240" w:after="220"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:color w:val="102A43"/><w:sz w:val="42"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="副标题"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="160"/></w:pPr><w:rPr><w:rFonts w:eastAsia="宋体"/><w:color w:val="3156A3"/><w:sz w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="标题 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="260" w:after="150"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:color w:val="102A43"/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="标题 2"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="210" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:color w:val="16807A"/><w:sz w:val="25"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="题注"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="150"/></w:pPr><w:rPr><w:rFonts w:eastAsia="宋体"/><w:i/><w:color w:val="4B6575"/><w:sz w:val="18"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="目录 1"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="100"/></w:pPr><w:rPr><w:rFonts w:eastAsia="宋体"/><w:sz w:val="22"/></w:rPr></w:style>
</w:styles>'''


def footer_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="center"/></w:pPr>{run("第 ", size=18, color="4B6575")}<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>{run("1", size=18, color="4B6575")}<w:r><w:fldChar w:fldCharType="end"/></w:r>{run(" 页", size=18, color="4B6575")}</w:p></w:ftr>'''


def document_rels(image_paths: list[Path]):
    parts = [
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
        '<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>',
        '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
    ]
    for index, path in enumerate(image_paths, 1):
        parts.append(f'<Relationship Id="rIdImg{index:02}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{path.name}"/>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(parts) + "</Relationships>"


def build_docx():
    global IMAGES
    build_diagrams()
    image_paths = [
        GEN_DIR / "01-role-flow.png",
        ASSET_DIR / "01-student-job-market.png",
        ASSET_DIR / "02-student-region.png",
        ASSET_DIR / "07-student-profile.png",
        ASSET_DIR / "08-student-recommendations.png",
        GEN_DIR / "02-recommendation-flow.png",
        ASSET_DIR / "03-university-overview.png",
        ASSET_DIR / "04-university-demand.png",
        ASSET_DIR / "05-university-student-focus.png",
        ASSET_DIR / "06-university-student-complete.png",
        ASSET_DIR / "09-admin-accounts.png",
        GEN_DIR / "03-batch-release.png",
        GEN_DIR / "04-troubleshooting.png",
    ]
    IMAGES = {f"rIdImg{index:02}": path for index, path in enumerate(image_paths, 1)}
    body = cover() + front_matter() + chapter1() + chapter2() + chapter3() + chapter4() + chapter5() + chapter6() + chapter7() + appendix()
    # A single final section lets Word calculate PAGE fields continuously and
    # avoids section-break-created blank pages.
    final_section = '<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1260" w:bottom="1260" w:left="1260" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>{body}{final_section}</w:body></w:document>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>基于Spark的高校智慧就业大数据分析平台用户使用手册</dc:title><dc:creator>韩磊</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">2026-07-16T00:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-07-16T00:00:00Z</dcterms:modified></cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Office Word</Application><Company>第4组</Company></Properties>'''
    settings = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="{W}"><w:zoom w:percent="100"/><w:updateFields w:val="true"/></w:settings>'''
    temp = OUT_FILE.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/app.xml", app)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles_xml())
        archive.writestr("word/settings.xml", settings)
        archive.writestr("word/footer1.xml", footer_xml())
        archive.writestr("word/_rels/document.xml.rels", document_rels(image_paths))
        for path in image_paths:
            archive.write(path, f"word/media/{path.name}")
    shutil.move(temp, OUT_FILE)


if __name__ == "__main__":
    build_docx()
    print(OUT_FILE)
