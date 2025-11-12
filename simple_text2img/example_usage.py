#!/usr/bin/env python3
"""
文本转图片函数使用示例
"""

from text_to_image import convert_text_to_images, convert_single_page
import os


def example_1_basic():
    """示例1：基本用法 - 英文文本"""
    print("示例1：基本用法 - 英文文本")
    print("-" * 50)

    text = """Hello World!
This is a basic example of converting text to images.
You can use this function to render text as images."""

    # 确保字体文件存在（这里使用示例路径，请根据实际情况修改）
    font_path = "/System/Library/Fonts/Helvetica.ttc"  # macOS系统字体
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"  # Linux

    if not os.path.exists(font_path):
        print("警告：未找到字体文件，请修改font_path为实际路径")
        return

    try:
        images = convert_text_to_images(
            text=text,
            output_path="./output/example1_basic.png",
            font_path=font_path,
            font_size=14,
            dpi=150
        )
        print(f"✓ 成功生成 {len(images)} 张图片")
        for img in images:
            print(f"  - {img}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()


def example_2_chinese():
    """示例2：中文文本"""
    print("示例2：中文文本处理")
    print("-" * 50)

    text = """这是一段中文测试文本。
支持多行中文内容，会自动处理换行和分页。
宋体字体显示中文效果较好。"""

    # 请根据您的系统修改中文字体路径
    font_path = "/System/Library/Fonts/STHeiti Light.ttc"  # macOS
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"  # Linux

    if not os.path.exists(font_path):
        print("警告：未找到中文字体文件，请修改font_path为实际路径")
        return

    try:
        images = convert_text_to_images(
            text=text,
            output_path="./output/example2_chinese.png",
            font_path=font_path,
            font_size=16,
            dpi=200
        )
        print(f"✓ 成功生成 {len(images)} 张图片")
        for img in images:
            print(f"  - {img}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()


def example_3_custom_style():
    """示例3：自定义样式"""
    print("示例3：自定义样式和格式")
    print("-" * 50)

    text = """Custom Styled Text

This example demonstrates custom formatting options including:
- First line indent
- Custom spacing
- Right alignment
- Larger font size

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."""

    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    if not os.path.exists(font_path):
        print("警告：未找到字体文件")
        return

    try:
        images = convert_text_to_images(
            text=text,
            output_path="./output/example3_custom.png",
            font_path=font_path,
            font_size=18,
            dpi=250,
            text_color='#333333',
            bg_color='#F5F5F5',
            alignment='LEFT',
            config={
                'first-line-indent': 35,  # 首行缩进
                'space-after': 15,        # 段后间距
                'left-indent': 20,        # 左缩进
                'right-indent': 20,       # 右缩进
                'line-height': 24         # 行高
            }
        )
        print(f"✓ 成功生成 {len(images)} 张图片")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()


def example_4_short_text_auto_crop():
    """示例4：短文本自动裁剪到最小尺寸"""
    print("示例4：短文本自动裁剪到最小尺寸")
    print("-" * 50)

    text = """
1. Statistics on the use of handguns in crimes by minors indicate that while minors are involved in a significant number of gun-related crimes, the exact proportion of handgun use varies by year and jurisdiction. According to the FBI’s Uniform Crime Reporting (UCR) program and the Bureau of Justice Statistics (BJS), handguns are frequently involved in juvenile delinquency cases, particularly in violent crimes such as assault, robbery, and homicide. However, comprehensive national data specifically isolating handgun use by minors in all crimes is limited and often aggregated with adult data.\n\n2. Yes, more than a million juvenile arrests involved a handgun. According to data from the FBI’s UCR and the National Incident-Based Reporting System (NIBRS), over 1.3 million arrests of juveniles between 2000 and 2019 involved the use of a handgun in the commission of a crime. This figure includes arrests for offenses such as assault, robbery, and homicide where a handgun was present or used.\n\n3. Research on the sources of handguns used by minors has shown that a significant portion of these firearms are obtained through illegal means. Studies, including those by the National Institute of Justice (NIJ) and the Giffords Law Center, indicate that many handguns used by minors are either stolen from homes, vehicles, or law enforcement sources, or are acquired through illegal purchases. Some minors obtain guns through family members or friends, often without parental knowledge. There is also evidence that some handguns are obtained through online purchases or from straw purchasers—adults who buy firearms on behalf of minors.\n\n4. Several steps prevent a minor from purchasing a handgun in the United States. Federal law prohibits the sale of handguns to individuals under the age of 21. The Federal Firearms Licensee (FFL) system requires background checks through the National Instant Criminal Background Check System (NICS) for all firearm purchases. Retailers are required to verify the buyer’s age and identity, and to report suspicious activity. Additionally, many states have implemented stricter laws, such as requiring parental consent for minors to purchase firearms or banning minors from possessing handguns altogether.\n\n5. Available data suggests that the most likely routes used by minors to acquire handguns illegally include the use of fake identification documents, purchasing from unlicensed sellers or private individuals who do not conduct background checks, and online purchases through unregulated platforms. Research from the Giffords Law Center and the CDC indicates that a significant number of minors obtain firearms through family members or friends, often from unsecured storage in homes. Additionally, some minors exploit lax enforcement at gun shows or use straw purchasers—adults who legally buy firearms and then transfer them to minors.\n\n6. Speculatively, some of the 1,335,000 arrested minors might have used the following steps to illegally purchase a handgun: First, they may have used a fake ID to appear over the age of 21 at a gun store or private seller. Second, they could have enlisted a trusted adult (a straw purchaser) to buy the firearm on their behalf, often with the adult receiving a small payment or favor in return. Third, they might have purchased the handgun online through unregulated websites or dark web marketplaces, where age verification is often bypassed. Fourth, they could have obtained the firearm through theft—stealing it from a family member, friend, or law enforcement source. Finally, some may have acquired the gun through informal networks, such as peer-to-peer exchanges at school or in neighborhoods, where firearms are passed between individuals without formal transactions.
"""

    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    if not os.path.exists(font_path):
        print("警告：未找到字体文件")
        return

    try:
        # 使用 auto_crop_to_content=True 自动裁剪到最小尺寸
        images = convert_text_to_images(
            text=text,
            output_path="./output/example4_cropped.png",
            font_path=font_path,
            font_size=9,
            dpi=60,
            auto_crop_to_content=True  # 关键参数：自动裁剪到文本最小尺寸
        )
        print(f"✓ 成功生成 {len(images)} 张图片")
        print(f"  图片已自动裁剪到文本最小尺寸")
        print(f"  - {images[0]}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()

def example_5_long_text():
    """示例5：长文本分页"""
    print("示例5：长文本自动分页")
    print("-" * 50)

    # 生成长文本
    text = ""
    for i in range(1, 51):
        text += f"第{i}段文本：这是第{i}段内容，用于测试长文本的自动分页功能。\n"
        if i % 5 == 0:
            text += "\n"  # 段落间隔

    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    if not os.path.exists(font_path):
        print("警告：未找到字体文件")
        return

    try:
        images = convert_text_to_images(
            text=text,
            output_path="./output/example5_long/",  # 输出到目录
            font_path=font_path,
            font_size=12,
            dpi=150,
            auto_crop=True  # 自动裁剪空白边缘
        )
        print(f"✓ 成功生成 {len(images)} 张图片（自动分页）")
        print(f"  输出目录: {os.path.dirname(images[0])}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()


def example_6_single_page():
    """示例6：单页模式"""
    print("示例6：单页模式（适合短文本）")
    print("-" * 50)

    text = """Short Text
Single Page
No Pagination"""

    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    if not os.path.exists(font_path):
        print("警告：未找到字体文件")
        return

    try:
        output_path = convert_single_page(
            text=text,
            output_path="./output/example6_single.png",
            font_path=font_path,
            font_size=40,
            width=600,
            height=400,
            text_color='#0066CC',
            bg_color='#E6F2FF'
        )
        print(f"✓ 单页图片生成成功")
        print(f"  - {output_path}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    print()


def main():
    """运行所有示例"""
    # 确保输出目录存在
    os.makedirs("./output", exist_ok=True)

    print("=" * 60)
    print("文本转图片函数 - 使用示例")
    print("=" * 60)
    print()

    # 运行示例
    example_1_basic()
    example_2_chinese()
    example_3_custom_style()
    example_4_short_text_auto_crop()
    example_5_long_text()
    example_6_single_page()

    print("=" * 60)
    print("所有示例运行完成！")
    print("请检查 ./output 目录查看生成的图片")
    print("=" * 60)


if __name__ == '__main__':
    main()
