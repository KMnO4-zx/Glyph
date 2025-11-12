#!/usr/bin/env python3
"""
简化版文本转图片函数
提供更简洁的API接口，便于直接使用
"""

from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from pdf2image import pdfinfo_from_bytes, convert_from_bytes
from reportlab.lib.units import inch

import io
import os
import re
import json
import numpy as np
from xml.sax.saxutils import escape


# 页面尺寸映射
PAGE_SIZE_MAP = {
    'A4': A4,
    'LETTER': LETTER,
    'A3': (16.5 * inch, 11.7 * inch),
}

# 对齐方式映射
ALIGN_MAP = {
    'LEFT': TA_LEFT,
    'CENTER': TA_CENTER,
    'RIGHT': TA_RIGHT,
    'JUSTIFY': TA_JUSTIFY,
}


def load_config_from_file(config_path):
    """
    从配置文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        dict: 配置字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 转换特殊格式字段
    if 'page-size' in config and isinstance(config['page-size'], str):
        if ',' in config['page-size']:
            config['page-size'] = tuple(map(float, config['page-size'].split(',')))
        else:
            config['page-size'] = PAGE_SIZE_MAP.get(config['page-size'].upper(), A4)

    if 'alignment' in config and isinstance(config['alignment'], str):
        config['alignment'] = ALIGN_MAP.get(config['alignment'], TA_JUSTIFY)

    # 转换颜色格式
    color_fields = ['font-color', 'page-bg-color', 'para-bg-color', 'para-border-color']
    for field in color_fields:
        if field in config and isinstance(config[field], str):
            config[field] = colors.HexColor(config[field])

    return config


def convert_text_to_images(
    text,
    output_path,
    font_path,
    font_size=9,
    dpi=72,
    page_size='A4',
    margin=5,
    text_color='#000000',
    bg_color='#FFFFFF',
    alignment='JUSTIFY',
    auto_crop=False,
    auto_crop_to_content=False,  # 新增：自动裁剪到文本内容最小尺寸
    config=None,
    config_path=None
):
    """
    将文本转换为图片 - 简化版接口

    Args:
        text: 输入的文本内容
        output_path: 输出图片路径（如：'output.png'）或输出目录
        font_path: 字体文件路径（必需）
        font_size: 字体大小（默认11）
        dpi: 图片分辨率DPI（默认200）
        page_size: 页面尺寸（默认'A4'，支持'A4', 'LETTER'）
        margin: 页面边距（默认20）
        text_color: 文本颜色（十六进制，默认'#000000'）
        bg_color: 背景颜色（十六进制，默认'#FFFFFF'）
        alignment: 文本对齐方式（默认'JUSTIFY'，可选'LEFT', 'CENTER', 'RIGHT'）
        auto_crop: 是否自动裁剪边缘空白（默认False）
        auto_crop_to_content: 是否自动裁剪到文本最小尺寸（默认False，短文本时建议设为True）
        config: 高级配置字典（可选，用于覆盖其他参数）

    Returns:
        list: 生成的图片路径列表

    Examples:
        # 基本用法
        images = convert_text_to_images(
            text="Hello World\\nThis is a test.",
            output_path="./output.png",
            font_path="./fonts/arial.ttf",
            font_size=12,
            dpi=300
        )

        # 高级配置
        images = convert_text_to_images(
            text="中文测试文本",
            output_path="./output.png",
            font_path="./fonts/songti.ttf",
            config={'first-line-indent': 20, 'space-after': 10}
        )
    """
    # 验证参数
    if not config_path and not font_path:
        raise ValueError("Must provide either font_path or config_path")

    # 从配置文件加载配置（如果有）
    file_config = {}
    if config_path:
        file_config = load_config_from_file(config_path)
        # 如果配置文件中有字体路径，使用它
        if 'font-path' in file_config and not font_path:
            font_path = file_config['font-path']
        elif not font_path:
            raise ValueError("No font path provided in config file or function argument")
    elif not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    # 创建基础配置（优先级：显式参数 > config参数 > 配置文件 > 默认值）
    base_config = {}

    # 应用配置文件（如果有）
    if file_config:
        base_config.update(file_config)

    # 应用显式参数（覆盖配置文件）
    base_config.update({
        'font-path': font_path,
        'font-size': font_size,
        'dpi': dpi,
        'page-size': PAGE_SIZE_MAP.get(page_size.upper(), A4),
        'margin-x': margin,
        'margin-y': margin,
        'font-color': colors.HexColor(text_color),
        'page-bg-color': colors.HexColor(bg_color),
        'para-bg-color': colors.HexColor(bg_color),
        'para-border-color': colors.HexColor(bg_color),
        'alignment': ALIGN_MAP.get(alignment.upper(), TA_JUSTIFY),
        'auto-crop-last-page': auto_crop,
        'auto-crop-width': auto_crop,
        'horizontal-scale': 1.0,
    })

    # 如果提供了config，覆盖基础配置
    if config:
        # 处理config中的字符串颜色值
        if 'font-color' in config and isinstance(config['font-color'], str):
            config['font-color'] = colors.HexColor(config['font-color'])
        if 'page-bg-color' in config and isinstance(config['page-bg-color'], str):
            config['page-bg-color'] = colors.HexColor(config['page-bg-color'])
        if 'alignment' in config and isinstance(config['alignment'], str):
            config['alignment'] = ALIGN_MAP.get(config['alignment'], TA_JUSTIFY)

        # 合并配置
        base_config.update(config)

    # 确定输出目录
    if output_path.endswith('.png') or output_path.endswith('.jpg'):
        output_dir = os.path.dirname(output_path) or './'
        base_name = os.path.splitext(os.path.basename(output_path))[0]
    else:
        output_dir = output_path
        # 生成基于文本内容的唯一ID
        import hashlib
        base_name = hashlib.md5(text.encode()).hexdigest()[:12]

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 注册字体
    font_name = os.path.basename(font_path).split('.')[0]
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except:
        pass  # 字体已注册

    # 创建PDF
    buf = io.BytesIO()
    page_width, page_height = base_config['page-size']

    doc = SimpleDocTemplate(
        buf,
        pagesize=base_config['page-size'],
        leftMargin=base_config['margin-x'],
        rightMargin=base_config['margin-x'],
        topMargin=base_config['margin-y'],
        bottomMargin=base_config['margin-y'],
    )

    # 创建段落样式
    styles = getSampleStyleSheet()
    RE_CJK = re.compile(r'[\u4E00-\u9FFF]')

    custom_style = ParagraphStyle(
        name="Custom",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=base_config['font-size'],
        leading=base_config.get('line-height', font_size + 2),
        textColor=base_config['font-color'],
        backColor=base_config['para-bg-color'],
        borderColor=base_config['para-border-color'],
        borderWidth=base_config.get('border-width', 0),
        borderPadding=base_config.get('border-padding', 0),
        firstLineIndent=base_config.get('first-line-indent', 0),
        wordWrap="CJK" if RE_CJK.search(text) else None,
        leftIndent=base_config.get('left-indent', 0),
        rightIndent=base_config.get('right-indent', 0),
        alignment=base_config['alignment'],
        spaceBefore=base_config.get('space-before', 0),
        spaceAfter=base_config.get('space-after', 0),
    )

    # 处理文本
    def replace_spaces(s):
        return re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group()), s)

    text = text.replace('\xad', '').replace('\u200b', '')
    processed_text = replace_spaces(escape(text))
    parts = processed_text.split('\n')

    # 批量创建段落
    story = []
    turns = 30
    newline_markup = base_config.get('newline-markup', '<br/>')

    for i in range(0, len(parts), turns):
        tmp_text = newline_markup.join(parts[i:i + turns])
        story.append(Paragraph(tmp_text, custom_style))

    # 构建PDF
    doc.build(
        story,
        onFirstPage=lambda c, d: (
            c.saveState(),
            c.setFillColor(base_config['page-bg-color']),
            c.rect(0, 0, page_width, page_height, stroke=0, fill=1),
            c.restoreState()
        ),
        onLaterPages=lambda c, d: (
            c.saveState(),
            c.setFillColor(base_config['page-bg-color']),
            c.rect(0, 0, page_width, page_height, stroke=0, fill=1),
            c.restoreState()
        )
    )

    pdf_bytes = buf.getvalue()
    buf.close()

    # 创建输出目录
    out_root = os.path.join(output_dir, base_name)
    os.makedirs(out_root, exist_ok=True)

    # 将PDF转换为图像
    info = pdfinfo_from_bytes(pdf_bytes)
    num_pages = total = info["Pages"]
    batch = 20
    image_paths = []

    for start in range(1, total + 1, batch):
        end = min(start + batch - 1, total)
        images = convert_from_bytes(pdf_bytes, dpi=base_config['dpi'], first_page=start, last_page=end)

        for offset, img in enumerate(images, start=start):
            w, h = img.size

            # 水平缩放
            horizontal_scale = base_config.get('horizontal-scale', 1.0)
            if horizontal_scale != 1.0:
                img = img.resize((int(w * horizontal_scale), h))

            # 自动裁剪到文本最小尺寸（处理短文本情况）
            if auto_crop_to_content:
                # 转换为灰度图
                gray = np.array(img.convert("L"))
                # 检测背景颜色（取左上角）
                bg_gray = np.median(gray[:10, :10])
                # 设置容差，找出非背景区域（文本）
                tolerance = 8
                mask = np.abs(gray - bg_gray) > tolerance

                # 找到文本边界
                rows = np.where(mask.any(axis=1))[0]
                cols = np.where(mask.any(axis=0))[0]

                if rows.size and cols.size:
                    # 添加边距
                    top = max(0, rows[0] - 10)
                    bottom = min(img.height, rows[-1] + 10)
                    left = max(0, cols[0] - 10)
                    right = min(img.width, cols[-1] + 10)

                    # 确保裁剪区域有效
                    if bottom > top and right > left:
                        img = img.crop((left, top, right, bottom))

            # 自适应裁剪（保持原有功能）
            elif base_config['auto-crop-width'] or (base_config['auto-crop-last-page'] and offset == num_pages):
                gray = np.array(img.convert("L"))
                bg_gray = np.median(gray[:2, :2])
                tolerance = 5
                mask = np.abs(gray - bg_gray) > tolerance

                if base_config['auto-crop-width']:  # 水平裁剪
                    cols = np.where(mask.any(axis=0))[0]
                    if cols.size:
                        rightmost_col = cols[-1] + 1
                        right = min(img.width, rightmost_col + base_config['margin-x'])
                        img = img.crop((0, 0, right, img.height))

                if base_config['auto-crop-last-page'] and offset == num_pages:  # 最后一页垂直裁剪
                    rows = np.where(mask.any(axis=1))[0]
                    if rows.size:
                        last_row = rows[-1]
                        lower = min(img.height, last_row + base_config['margin-y'])
                        img = img.crop((0, 0, img.width, lower))

            out_path = os.path.join(out_root, f"{base_name}_{offset:03d}.png")
            img.save(out_path, 'PNG')
            image_paths.append(os.path.abspath(out_path))
            img.close()

        images.clear()
        del images

    del pdf_bytes
    import gc
    gc.collect()

    return image_paths


def convert_single_page(
    text,
    output_path,
    font_path,
    font_size=12,
    dpi=300,
    width=800,
    height=1000,
    text_color='#000000',
    bg_color='#FFFFFF',
    margin=20
):
    """
    将文本转换为单页图片（不自动分页）

    Args:
        text: 输入文本
        output_path: 输出图片路径
        font_path: 字体文件路径
        font_size: 字体大小（默认12）
        dpi: 分辨率（默认300）
        width: 图片宽度（默认800）
        height: 图片高度（默认1000）
        text_color: 文本颜色（默认#000000）
        bg_color: 背景颜色（默认#FFFFFF）
        margin: 边距（默认20）

    Returns:
        str: 输出图片路径
    """
    from PIL import ImageDraw, ImageFont

    # 加载字体
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        raise FileNotFoundError(f"Cannot load font: {font_path}")

    # 创建图片
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 文本换行处理
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        line = ''
        for word in words:
            test_line = line + word + ' '
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width < width - 2 * margin:
                line = test_line
            else:
                if line:
                    lines.append(line.strip())
                line = word + ' '
        if line:
            lines.append(line.strip())
        lines.append('')  # 段落间空行

    # 绘制文本
    y = margin
    line_height = font_size + 5

    for line in lines:
        if line:
            draw.text((margin, y), line, font=font, fill=text_color)
        y += line_height

        if y > height - margin:
            break

    # 保存图片
    img.save(output_path, dpi=(dpi, dpi))
    return os.path.abspath(output_path)


if __name__ == '__main__':
    # 使用示例
    print("文本转图片简化版函数示例")
    print("=" * 50)

    # 示例1：基本用法
    print("\n示例1：基本用法")
    print("-" * 30)
    print("代码：")
    print("""
from text_to_image import convert_text_to_images

images = convert_text_to_images(
    text="Hello World!\\nThis is a test.",
    output_path="./output.png",
    font_path="./fonts/arial.ttf",
    font_size=12,
    dpi=300
)
print(f"生成图片：{images}")
""")

    # 示例2：中文文本
    print("\n示例2：中文文本")
    print("-" * 30)
    print("代码：")
    print("""
images = convert_text_to_images(
    text="这是一段中文测试文本。\\n可以包含多行内容。",
    output_path="./chinese_output.png",
    font_path="./fonts/songti.ttf",
    font_size=14,
    dpi=200
)
""")

    # 示例3：使用高级配置
    print("\n示例3：使用高级配置")
    print("-" * 30)
    print("代码：")
    print("""
images = convert_text_to_images(
    text="Custom styled text",
    output_path="./styled.png",
    font_path="./fonts/arial.ttf",
    config={
        'first-line-indent': 20,
        'space-after': 10,
        'alignment': 'LEFT'
    }
)
""")

    # 示例4：单页模式（不自动分页）
    print("\n示例4：单页模式")
    print("-" * 30)
    print("代码：")
    print("""
from text_to_image import convert_single_page

output_path = convert_single_page(
    text="Short text for single page",
    output_path="./single_page.png",
    font_path="./fonts/arial.ttf",
    width=800,
    height=600
)
""")
