"""
功能：这节课值多少钱？
计算每节课的价值，让你知道逃一节课亏多少钱
"""

import json
import os


def calculate_class_value(tuition=6000, weeks=18):
    """
    计算每节课的价值

    参数:
        tuition: 一学年学费（元），默认6000
        weeks: 一学期教学周数，默认18周
    """

    # 读取课表数据
    courses_file = "courses.json"
    if not os.path.exists(courses_file):
        print("❌ 未找到 courses.json，请先运行主程序生成课表")
        return None

    with open(courses_file, "r", encoding="utf-8") as f:
        courses = json.load(f)

    if not courses:
        print("❌ 课表为空")
        return None

    # 计算每周总节数
    total_weekly_classes = 0
    for c in courses:
        total_weekly_classes += (c['end_slot'] - c['start_slot'] + 1)

    # 计算每学期的总节数
    total_semester_classes = total_weekly_classes * weeks

    # 计算每节课的价值
    class_value = tuition / total_semester_classes if total_semester_classes > 0 else 0

    # 计算每天的价值
    weekday_classes = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    for c in courses:
        weekday_classes[c['weekday']] += (c['end_slot'] - c['start_slot'] + 1)

    weekday_names = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # 生成HTML报告
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>这节课值多少钱 - 课程价值计算器</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }}
        .card-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            text-align: center;
        }}
        .card-header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .value-number {{
            font-size: 72px;
            font-weight: bold;
            color: #e67e22;
            margin: 20px 0;
        }}
        .info-box {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .warning-box {{
            background: #fff3e0;
            border-left: 4px solid #e67e22;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .day-value {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .footer {{
            text-align: center;
            padding: 15px;
            font-size: 12px;
            color: #888;
        }}
        button {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="card-header">
            <h1>💰 这节课值多少钱？</h1>
            <p>认真上课就是给自己赚钱</p>
        </div>
        <div class="report-content" style="padding: 30px; text-align: center;">

            <div class="value-number">¥{class_value:.2f}</div>
            <p style="color: #666; margin-bottom: 10px;">每节课的价值</p>

            <div class="info-box">
                <p><strong>📊 计算依据</strong></p>
                <p>学年学费：¥{tuition:,} 元</p>
                <p>每周课程：{total_weekly_classes} 节</p>
                <p>学期周数：{weeks} 周</p>
                <p>一学期总课时：{total_semester_classes} 节</p>
            </div>

            <div class="warning-box">
                <strong>💡 逃课成本</strong><br>
                🔥 逃一节课 = 白扔 <strong style="color: #e67e22; font-size: 20px;">¥{class_value:.2f}</strong><br>
                🎉 一学期全勤 = 赚回 <strong style="color: #27ae60;">¥{tuition:,}</strong>
            </div>

            <div class="info-box">
                <p><strong>📅 每天的价值</strong></p>
'''

    for day in range(1, 6):
        if weekday_classes[day] > 0:
            day_value = weekday_classes[day] * class_value
            html += f'''
                <div class="day-value">
                    <span>{weekday_names[day]}</span>
                    <span>{weekday_classes[day]}节课</span>
                    <span style="color: #e67e22;">¥{day_value:.2f}</span>
                </div>
'''

    # 逃课一年能省多少钱？（反向刺激）
    skip_5_percent = class_value * 0.05 * total_semester_classes

    html += f'''
            </div>

            <div class="warning-box">
                <strong>🤔 换个角度</strong><br>
                如果每门课逃课5% <span style="font-size: 12px;">（约{int(total_semester_classes * 0.05)}节课）</span><br>
                你将浪费约 <strong style="color: #e74c3c;">¥{skip_5_percent:.2f}</strong><br>
                <span style="font-size: 12px;">≈ {int(skip_5_percent / 20)} 杯奶茶 / {int(skip_5_percent / 10)} 顿食堂午饭</span>
            </div>

            <button onclick="location.reload()">🔄 重新计算</button>
            <p style="margin-top: 20px; font-size: 12px; color: #999;">
                💡 提示：可以修改本文件第13-14行的 tuition 和 weeks 参数
            </p>
        </div>
    </div>
    <div class="footer">
        数据来源：courses.json | 生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</div>
</body>
</html>'''

    # 保存HTML文件
    output_file = "class_value.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    # 在控制台也打印一下
    print("\n" + "=" * 50)
    print("💰 课程价值计算器")
    print("=" * 50)
    print(f"📊 每周课程：{total_weekly_classes} 节")
    print(f"💰 每节课价值：¥{class_value:.2f}")
    print(f"🔥 逃一节课亏：¥{class_value:.2f}")
    print(f"🎉 一学期全勤赚：¥{tuition:,}")
    print("=" * 50)
    print(f"✅ 已生成HTML报告：{output_file}")

    # 自动打开浏览器
    import webbrowser
    webbrowser.open(output_file)

    return class_value


# ========== 主程序 ==========
if __name__ == "__main__":
    # 可以在这里修改你的学费和学期周数
    TUITION = 6000  # ← 修改成你的学年学费（元）
    WEEKS = 18  # ← 修改成一学期教学周数

    calculate_class_value(TUITION, WEEKS)

    input("\n按回车键退出...")