#!/usr/bin/env python3
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import io
import os
import json
import numpy as np
import gc
from pdf2image import pdfinfo_from_bytes, convert_from_bytes
import re
from multiprocessing import Pool
from tqdm import tqdm
from xml.sax.saxutils import escape
import shutil

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors

# 对齐方式映射
ALIGN_MAP = {
    "LEFT": TA_LEFT,
    "CENTER": TA_CENTER,
    "RIGHT": TA_RIGHT,
    "JUSTIFY": TA_JUSTIFY,
}

# 多进程处理的全局变量
GLOBAL_CONFIG = None
OUTPUT_DIR = None
recover = False


def load_config(config_path):
    """加载配置文件"""
    """加载配置文件并转换特殊格式字段"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 转换颜色格式
    if 'page-bg-color' in config and isinstance(config['page-bg-color'], str):
        config['page-bg-color'] = colors.HexColor(config['page-bg-color'])
    if 'font-color' in config and isinstance(config['font-color'], str):
        config['font-color'] = colors.HexColor(config['font-color'])
    if 'para-bg-color' in config and isinstance(config['para-bg-color'], str):
        config['para-bg-color'] = colors.HexColor(config['para-bg-color'])
    if 'para-border-color' in config and isinstance(config['para-border-color'], str):
        config['para-border-color'] = colors.HexColor(config['para-border-color'])
    
    # 转换对齐方式
    if 'alignment' in config and isinstance(config['alignment'], str):
        config['alignment'] = ALIGN_MAP.get(config['alignment'], TA_JUSTIFY)
    
    # 转换页面尺寸
    if 'page-size' in config and isinstance(config['page-size'], str):
        config['page-size'] = tuple(map(float, config['page-size'].split(',')))
    
    return config


def text_to_images(text, output_dir, config_path=None, config_dict=None, unique_id=None):
    """
    将文本转换为图像 - 推理接口

    Args:
        text: 输入的文本内容
        output_dir: 图像输出目录
        config_path: 配置文件路径 (可选)
        config_dict: 配置字典 (可选，优先级高于config_path)
        unique_id: 唯一标识符 (可选，如果未提供则自动生成)

    Returns:
        list: 生成的图像路径列表

    Example:
        >>> images = text_to_images(
        ...     text="Hello World",
        ...     output_dir="./output",
        ...     config_path="config.json"
        ... )
        >>> print(images)  # ['./output/xxx/page_001.png', ...]
    """
    # 加载配置
    if config_dict is None:
        if config_path is None:
            raise ValueError("Must provide either config_path or config_dict")
        config = load_config(config_path)
    else:
        config = config_dict.copy()
        # 转换配置中的特殊字段
        if 'page-bg-color' in config and isinstance(config['page-bg-color'], str):
            config['page-bg-color'] = colors.HexColor(config['page-bg-color'])
        if 'font-color' in config and isinstance(config['font-color'], str):
            config['font-color'] = colors.HexColor(config['font-color'])
        if 'para-bg-color' in config and isinstance(config['para-bg-color'], str):
            config['para-bg-color'] = colors.HexColor(config['para-bg-color'])
        if 'para-border-color' in config and isinstance(config['para-border-color'], str):
            config['para-border-color'] = colors.HexColor(config['para-border-color'])
        if 'alignment' in config and isinstance(config['alignment'], str):
            config['alignment'] = ALIGN_MAP.get(config['alignment'], TA_JUSTIFY)
        if 'page-size' in config and isinstance(config['page-size'], str):
            config['page-size'] = tuple(map(float, config['page-size'].split(',')))
    
    # 生成唯一ID
    if unique_id is None:
        import hashlib
        unique_id = hashlib.md5(text.encode()).hexdigest()[:16]
    
    # 提取配置参数
    page_size = config.get('page-size', A4)
    margin_x = config.get('margin-x', 20)
    margin_y = config.get('margin-y', 20)
    font_path = config.get('font-path')
    assert font_path, "Must provide font-path"
    
    font_name = os.path.basename(font_path).split('.')[0]
    font_size = config.get('font-size', 9)
    line_height = config.get('line-height') or (font_size + 1)
    
    page_bg_color = config.get('page-bg-color', colors.HexColor('#FFFFFF'))
    font_color = config.get('font-color', colors.HexColor('#000000'))
    para_bg_color = config.get('para-bg-color', colors.HexColor('#FFFFFF'))
    para_border_color = config.get('para-border-color', colors.HexColor('#FFFFFF'))
    
    first_line_indent = config.get('first-line-indent', 0)
    left_indent = config.get('left-indent', 0)
    right_indent = config.get('right-indent', 0)
    alignment = config.get('alignment', TA_JUSTIFY)
    space_before = config.get('space-before', 0)
    space_after = config.get('space-after', 0)
    border_width = config.get('border-width', 0)
    border_padding = config.get('border-padding', 0)
    
    horizontal_scale = config.get('horizontal-scale', 1.0)
    dpi = config.get('dpi', 72)
    auto_crop_last_page = config.get('auto-crop-last-page', False)
    auto_crop_width = config.get('auto-crop-width', False)
    # newline_markup = config.get('newline-markup', '<font color="#FF0000"> \\n </font>')
    newline_markup = config.get('newline-markup', '<br/>')
    
    # 注册字体
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except:
        pass  # 字体已注册
    
    # 创建PDF
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=margin_y,
        bottomMargin=margin_y,
    )
    
    # 创建段落样式
    styles = getSampleStyleSheet()
    RE_CJK = re.compile(r'[\u4E00-\u9FFF]')
    
    custom = ParagraphStyle(
        name="Custom",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=font_size,
        leading=line_height,
        textColor=font_color,
        backColor=para_bg_color,
        borderColor=para_border_color,
        borderWidth=border_width,
        borderPadding=border_padding,
        firstLineIndent=first_line_indent,
        wordWrap="CJK" if RE_CJK.search(text) else None,
        leftIndent=left_indent,
        rightIndent=right_indent,
        alignment=alignment,
        spaceBefore=space_before,
        spaceAfter=space_after,
    )
    
    # 处理文本
    def replace_spaces(s):
        return re.sub(r' {2,}', lambda m: '&nbsp;'*len(m.group()), s)
    
    text = text.replace('\xad', '').replace('\u200b', '')
    processed_text = replace_spaces(escape(text))
    parts = processed_text.split('\n')
    
    # 批量创建段落
    story = []
    turns = 30
    for i in range(0, len(parts), turns):
        tmp_text = newline_markup.join(parts[i:i+turns])
        story.append(Paragraph(tmp_text, custom))
    
    # 构建PDF
    doc.build(
        story,
        onFirstPage=lambda c, d: (c.saveState(), c.setFillColor(page_bg_color), c.rect(0, 0, page_size[0], page_size[1], stroke=0, fill=1), c.restoreState()),
        onLaterPages=lambda c, d: (c.saveState(), c.setFillColor(page_bg_color), c.rect(0, 0, page_size[0], page_size[1], stroke=0, fill=1), c.restoreState())
    )
    
    pdf_bytes = buf.getvalue()
    buf.close()
    
    # 创建输出目录
    out_root = os.path.join(output_dir, unique_id)
    os.makedirs(out_root, exist_ok=True)
    
    # 将PDF转换为图像
    info = pdfinfo_from_bytes(pdf_bytes)
    num_pages = total = info["Pages"]
    batch = 20
    image_paths = []
    
    for start in range(1, total + 1, batch):
        end = min(start + batch - 1, total)
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=start, last_page=end)
        
        for offset, img in enumerate(images, start=start):
            w, h = img.size
            
            # 水平缩放
            if horizontal_scale != 1.0:
                img = img.resize((int(w * horizontal_scale), h))
            
            # 自适应裁剪
            if auto_crop_width or (auto_crop_last_page and offset == num_pages):
                gray = np.array(img.convert("L"))
                bg_gray = np.median(gray[:2, :2])
                tolerance = 5
                mask = np.abs(gray - bg_gray) > tolerance
                
                if auto_crop_width:  # 水平裁剪
                    cols = np.where(mask.any(axis=0))[0]
                    if cols.size:
                        rightmost_col = cols[-1] + 1
                        right = min(img.width, rightmost_col + margin_x)
                        img = img.crop((0, 0, right, img.height))
                
                if auto_crop_last_page and offset == num_pages:  # 最后一页垂直裁剪
                    rows = np.where(mask.any(axis=1))[0]
                    if rows.size:
                        last_row = rows[-1]
                        lower = min(img.height, last_row + margin_y)
                        img = img.crop((0, 0, img.width, lower))
            
            out_path = os.path.join(out_root, f"page_{offset:03d}.png")
            img.save(out_path, 'PNG')
            image_paths.append(os.path.abspath(out_path))
            img.close()
        
        images.clear()
        del images
    
    del pdf_bytes
    gc.collect()
    
    return image_paths


def process_one(item):
    """处理单个项目 - 用于批量处理"""
    global GLOBAL_CONFIG, OUTPUT_DIR, recover
    
    _id = item.get('unique_id')
    assert _id
    
    # 检查恢复模式
    if recover and os.path.exists(os.path.join(OUTPUT_DIR, _id)):
        item['image_paths'] = []
        return item
    
    # 解析配置
    item_config = item.get('config', {}) or {}
    config = {**GLOBAL_CONFIG, **item_config}
    
    # 处理项目配置中的特殊字段
    if 'page-size' in item_config and isinstance(item_config['page-size'], str):
        config['page-size'] = tuple(map(float, item_config['page-size'].split(',')))
    if 'page-bg-color' in item_config and isinstance(item_config['page-bg-color'], str):
        config['page-bg-color'] = colors.HexColor(item_config['page-bg-color'])
    if 'font-color' in item_config and isinstance(item_config['font-color'], str):
        config['font-color'] = colors.HexColor(item_config['font-color'])
    if 'para-bg-color' in item_config and isinstance(item_config['para-bg-color'], str):
        config['para-bg-color'] = colors.HexColor(item_config['para-bg-color'])
    if 'para-border-color' in item_config and isinstance(item_config['para-border-color'], str):
        config['para-border-color'] = colors.HexColor(item_config['para-border-color'])
    if 'alignment' in item_config and isinstance(item_config['alignment'], str):
        config['alignment'] = ALIGN_MAP.get(item_config['alignment'], TA_JUSTIFY)
    
    # 获取文本
    text = item.get('context', '')
    assert text
    
    # 调用推理函数
    image_paths = text_to_images(
        text=text,
        output_dir=OUTPUT_DIR,
        config_dict=config,
        unique_id=_id
    )
    
    item['image_paths'] = image_paths
    return item


def batch_process_to_images(json_path, output_dir, output_jsonl_path,
                            config_path, processes=16, is_recover=False, batch_size=100):
    """批量处理JSON数据生成图像"""
    global GLOBAL_CONFIG, OUTPUT_DIR, recover
    
    # 设置全局变量
    GLOBAL_CONFIG = load_config(config_path)
    OUTPUT_DIR = output_dir
    recover = is_recover
    
    print(f"Loaded config from: {config_path}")
    
    # 准备输出目录
    if not recover:
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        if os.path.exists(output_jsonl_path):
            os.remove(output_jsonl_path)
    
    # 读取数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data_to_process = json.load(f)
    
    # 获取已处理的ID
    processed_ids = set()
    if recover and os.path.exists(output_jsonl_path):
        with open(output_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    processed_ids.add(item.get('unique_id'))
                except:
                    continue
        print(f"Found {len(processed_ids)} already processed items")
    
    # 过滤已处理的项目
    data_to_process = [item for item in data_to_process 
                      if item.get('unique_id') not in processed_ids]
    print(f"Remaining items to process: {len(data_to_process)}")
    
    if not data_to_process:
        print("All items processed")
        return
    
    # 并行处理
    batch_buffer = []
    
    with Pool(processes=processes) as pool:
        for result_item in tqdm(pool.imap_unordered(process_one, data_to_process, chunksize=1), 
                               total=len(data_to_process)):
            if result_item:
                batch_buffer.append(result_item)
                _id = result_item.get('unique_id', 'UNKNOWN')
                count = len(result_item.get('image_paths', []))
                tqdm.write(f"{_id}: generated {count} pages")
                
                # 批量写入
                if len(batch_buffer) >= batch_size:
                    with open(output_jsonl_path, 'a', encoding='utf-8') as f:
                        for item in batch_buffer:
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    batch_buffer = []
    
    # 写入剩余项目
    if batch_buffer:
        with open(output_jsonl_path, 'a', encoding='utf-8') as f:
            for item in batch_buffer:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print("Processing complete")


if __name__ == '__main__':
    # 示例1：单文本推理
    CONFIG_PATH = '../config/config_en.json'
    text = "This is a test text\nSecond line of text\nThird line of text"

    with open("./jailbreak.txt", "r", encoding="utf-8") as f:
        text = f.read()
    OUTPUT_DIR = './jailbreak_images'
    images = text_to_images(
        text=text,
        output_dir=OUTPUT_DIR,
        config_path=CONFIG_PATH,
        unique_id='jailbreak_dpi_120',
    )
    print(f"Generated {len(images)} images:")
    for img in images:
        print(f"  {img}")
    
    # 示例2：批量处理
    # CONFIG_PATH = '../config/config.json'
    # JSON_PATH = '../evaluation/mrcr/data/processed_2needle_0-128k.json'
    # OUTPUT_JSONL_PATH = '../evaluation/mrcr/data/processed_2needle_0-128k.jsonl'
    # OUTPUT_DIR = '../evaluation/mrcr/rendered_images'
    
    # batch_process_to_images(
    #     json_path=JSON_PATH,
    #     output_dir=OUTPUT_DIR,
    #     output_jsonl_path=OUTPUT_JSONL_PATH,
    #     config_path=CONFIG_PATH,
    #     processes=16,
    #     is_recover=True,
    #     batch_size=100
    # )


