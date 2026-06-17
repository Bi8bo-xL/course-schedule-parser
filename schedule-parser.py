import re
import json
import webbrowser
import os
from datetime import datetime

# ========== 星期映射 ==========
weekday_map = {
    "周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7, "天": 7
}


def parse_course_line(line):
    line = line.strip()
    if not line:
        return None
    header_pattern = r"([周一二三四五六日天]+)(\d+)-(\d+)节"
    header_match = re.match(header_pattern, line)
    if not header_match:
        return None
    weekday_str = header_match.group(1)
    start_slot = int(header_match.group(2))
    end_slot = int(header_match.group(3))
    rest = line[header_match.end():].strip()
    if ' ' in rest:
        parts = rest.rsplit(' ', 1)
        name = parts[0].strip()
        room = parts[1].strip()
    else:
        room_match = re.search(r'(\d+[A-Za-z]?|[A-Za-z]+\d+|\d+)$', rest)
        if room_match:
            room = room_match.group(1)
            name = rest[:room_match.start()].strip()
        else:
            name = rest
            room = "待定"
    weekday = None
    for key in weekday_map:
        if key in weekday_str:
            weekday = weekday_map[key]
            break
    return {
        "name": name,
        "weekday": weekday,
        "start_slot": start_slot,
        "end_slot": end_slot,
        "room": room,
    }


def parse_schedule(raw_text):
    courses = []
    for line in raw_text.strip().split('\n'):
        if not line.strip():
            continue
        course = parse_course_line(line)
        if course:
            courses.append(course)
    return courses


def generate_html(courses):
    # 统计
    weekday_courses = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for c in courses:
        if c['weekday'] in weekday_courses:
            weekday_courses[c['weekday']] += (c['end_slot'] - c['start_slot'] + 1)

    total_hours = 0
    for c in courses:
        total_hours += (c['end_slot'] - c['start_slot'] + 1) * 45 / 60

    weekday_names = ["", "周一", "周二", "周三", "周四", "周五"]
    busiest_day = max(weekday_courses, key=weekday_courses.get)
    freest_day = min(weekday_courses, key=weekday_courses.get)

    type_count = {"专业核心": 0, "体育": 0, "通识选修": 0, "思政": 0}
    for c in courses:
        if "体育" in c['name']:
            type_count["体育"] += 1
        elif "通核" in c['name'] or "通识" in c['name'] or "选修" in c['name'] or "传播心理学" in c['name']:
            type_count["通识选修"] += 1
        elif "毛泽东" in c['name'] or "中国特色" in c['name'] or "形势与政策" in c['name']:
            type_count["思政"] += 1
        else:
            type_count["专业核心"] += 1

    time_slots = [
        (1, 2, "08:00-09:40"), (3, 4, "09:50-11:30"), (5, 6, "13:30-15:10"),
        (7, 8, "15:20-17:00"), (9, 10, "18:30-20:10"), (11, 12, "20:20-22:00")
    ]

    course_grid = {}
    for c in courses:
        course_grid[(c['weekday'], c['start_slot'])] = c

    # 生成每日负荷进度条
    daily_bars = ""
    max_courses = max(weekday_courses.values()) or 1
    for day in range(1, 6):
        percent = weekday_courses[day] / max_courses * 100
        daily_bars += f'''
            <div class="stat-row">
                <span class="stat-day">{weekday_names[day]}</span>
                <div class="stat-bar">
                    <div class="stat-fill" style="width: {percent}%">{weekday_courses[day]}节</div>
                </div>
            </div>'''

    # 学习建议
    advice = []
    if weekday_courses[5] <= 2:
        advice.append("周五课少，可安排复习或自习")
    if type_count['体育'] == 0:
        advice.append("本周无体育课，记得自行安排运动")
    if total_hours > 20:
        advice.append("本周课程较多，注意劳逸结合")
    else:
        advice.append("课程压力适中，可适当参加社团活动")

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的课表</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', sans-serif;
            background: #f0f4f8;
            padding: 32px 20px;
            min-height: 100vh;
            color: #1a202c;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}

        /* 卡片 - 干净有层次 */
        .card {{
            background: #ffffff;
            border-radius: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
            border: 1px solid #e8ecf0;
            overflow: hidden;
            margin-bottom: 24px;
        }}

        /* 头部 */
        .header {{
            padding: 28px 32px 20px;
            border-bottom: 1px solid #e8ecf0;
            background: #fafbfc;
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.4px;
            color: #1a202c;
        }}
        .header h1 span {{ color: #2b6cb0; }}
        .header p {{
            font-size: 14px;
            color: #718096;
            margin-top: 4px;
        }}

        /* 统计卡片 - 突出数字 */
        .stats {{
            display: flex;
            gap: 16px;
            margin-top: 16px;
            flex-wrap: wrap;
        }}
        .stat-item {{
            background: white;
            padding: 6px 18px;
            border-radius: 40px;
            font-size: 13px;
            color: #4a5568;
            border: 1px solid #e8ecf0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}
        .stat-item strong {{
            font-weight: 700;
            color: #1a202c;
            font-size: 16px;
            margin-right: 2px;
        }}
        .stat-item .highlight {{ color: #2b6cb0; }}

        /* 导航按钮 */
        .nav-grid {{
            display: flex;
            gap: 12px;
            padding: 16px 32px;
            background: #fafbfc;
            border-bottom: 1px solid #e8ecf0;
            flex-wrap: wrap;
        }}
        .nav-btn {{
            background: white;
            padding: 8px 22px;
            border-radius: 40px;
            text-decoration: none;
            color: #4a5568;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            border: 1px solid #e8ecf0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}
        .nav-btn:hover {{
            border-color: #2b6cb0;
            color: #2b6cb0;
            box-shadow: 0 4px 12px rgba(43,108,176,0.08);
        }}
        .nav-btn.primary {{
            background: #2b6cb0;
            color: white;
            border: none;
        }}
        .nav-btn.primary:hover {{
            background: #1a4f7a;
            box-shadow: 0 4px 16px rgba(43,108,176,0.25);
        }}

        /* ========== 课表表格 ========== */
        .schedule-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .schedule-table th {{
            padding: 14px 8px;
            background: #f7fafc;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #e8ecf0;
            font-size: 13px;
        }}
        .schedule-table td {{
            border: 1px solid #e8ecf0;
            padding: 10px 8px;
            vertical-align: top;
            height: 82px;
            background: white;
        }}
        .time-cell {{
            background: #f7fafc;
            font-weight: 500;
            width: 100px;
            text-align: center;
            font-size: 12px;
            color: #4a5568;
            border-right: 2px solid #e8ecf0;
        }}
        .course-block {{
            background: #ebf5ff;
            border-radius: 14px;
            padding: 6px 10px;
            height: 100%;
            transition: all 0.15s;
            border-left: 4px solid #2b6cb0;
        }}
        .course-block:hover {{
            background: #dbeafe;
            transform: scale(1.01);
        }}
        .course-name {{
            font-weight: 600;
            color: #1a202c;
            font-size: 13px;
        }}
        .course-room {{
            font-size: 11px;
            color: #718096;
            margin-top: 4px;
        }}
        .empty-cell {{
            color: #cbd5e0;
            text-align: center;
            font-size: 12px;
        }}

        /* ========== 周报区域 ========== */
        .report-section {{
            padding: 24px 32px;
            border-bottom: 1px solid #e8ecf0;
        }}
        .report-section:last-child {{ border-bottom: none; }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 16px;
        }}

        .stat-row {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .stat-day {{
            width: 50px;
            font-weight: 500;
            color: #4a5568;
            font-size: 13px;
        }}
        .stat-bar {{
            flex: 1;
            height: 24px;
            background: #edf2f7;
            border-radius: 20px;
            overflow: hidden;
        }}
        .stat-fill {{
            height: 100%;
            background: #2b6cb0;
            border-radius: 20px;
            color: white;
            line-height: 24px;
            padding-left: 12px;
            font-size: 11px;
            font-weight: 500;
        }}

        .type-grid {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .type-tag {{
            background: #edf2f7;
            padding: 6px 18px;
            border-radius: 30px;
            font-size: 13px;
            color: #4a5568;
            font-weight: 500;
        }}
        .type-tag .num {{
            font-weight: 700;
            color: #2b6cb0;
            margin-right: 2px;
        }}

        .advice-box {{
            background: #f7fafc;
            border-radius: 16px;
            padding: 14px 18px;
            line-height: 1.8;
            color: #4a5568;
            font-size: 13px;
            border: 1px solid #e8ecf0;
        }}
        .advice-box .item {{
            display: inline-block;
            margin-right: 20px;
        }}

        .footer {{
            text-align: center;
            padding: 14px;
            font-size: 11px;
            color: #a0aec0;
            border-top: 1px solid #e8ecf0;
            background: #fafbfc;
        }}

        /* ========== 响应式 ========== */
        @media (max-width: 700px) {{
            .header {{ padding: 20px 20px 16px; }}
            .header h1 {{ font-size: 20px; }}
            .nav-grid {{ padding: 12px 16px; }}
            .report-section {{ padding: 16px 20px; }}
            .course-name {{ font-size: 11px; }}
            .time-cell {{ width: 70px; font-size: 10px; }}
            td {{ padding: 6px; height: 70px; }}
            .stats {{ gap: 10px; }}
            .stat-item {{ font-size: 12px; padding: 4px 12px; }}
            .stat-item strong {{ font-size: 14px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="header">
            <h1> 我的课表</h1>
            <p>课程安排 · 学业周报</p>
            <div class="stats">
                <div class="stat-item">📖 总课 <strong>{len(courses)}</strong> 门</div>
                <div class="stat-item">周一 <strong>{weekday_courses[1]}</strong> 节</div>
                <div class="stat-item">周二 <strong>{weekday_courses[2]}</strong> 节</div>
                <div class="stat-item">周三 <strong>{weekday_courses[3]}</strong> 节</div>
                <div class="stat-item">周四 <strong>{weekday_courses[4]}</strong> 节</div>
                <div class="stat-item">周五 <strong>{weekday_courses[5]}</strong> 节</div>
            </div>
        </div>

        <div class="nav-grid">
            <a href="study_buddy.html" class="nav-btn primary"> 找学习搭子</a>
            <a href="group_project.html" class="nav-btn"> 小组作业看板</a>
        </div>

        <table class="schedule-table">
            <thead>
                <tr><th></th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th></tr>
            </thead>
            <tbody>'''

    for start, end, time_range in time_slots:
        html += f'<tr><td class="time-cell">{time_range}<br><span style="font-size:9px">第{start}-{end}节</span></td>'
        for day in range(1, 6):
            course = course_grid.get((day, start))
            if course:
                html += f'<td><div class="course-block"><div class="course-name">{course["name"]}</div><div class="course-room">{course["room"]}</div></div></td>'
            else:
                html += '<td><div class="empty-cell">—</div></td>'
        html += '</tr>'

    html += f'''
            </tbody>
        </table>
    </div>

    <!-- 周报 -->
    <div class="card">
        <div class="header" style="border-bottom: none; padding-bottom: 0;">
            <h1> 学业周报</h1>
            <p>本周学习数据一览</p>
        </div>

        <div class="report-section">
            <div class="section-title">⏱ 课时统计</div>
            <div class="stat-row">
                <span class="stat-day">总课时</span>
                <div class="stat-bar"><div class="stat-fill" style="width:100%">{sum(weekday_courses.values())}节</div></div>
            </div>
            <div class="stat-row">
                <span class="stat-day">总时长</span>
                <div class="stat-bar"><div class="stat-fill" style="width:{min(total_hours / 30 * 100, 100)}%">{total_hours:.1f}小时</div></div>
            </div>
        </div>

        <div class="report-section">
            <div class="section-title">📅 每日负荷</div>
            {daily_bars}
            <div style="margin-top:12px; font-size:13px; color:#4a5568;">
            </div>
        </div>

        <div class="report-section">
            <div class="section-title"> 课程类型</div>
            <div class="type-grid">
                <div class="type-tag"> 专业核心 <span class="num">{type_count['专业核心']}</span> 门</div>
                <div class="type-tag"> 体育 <span class="num">{type_count['体育']}</span> 门</div>
                <div class="type-tag"> 通识选修 <span class="num">{type_count['通识选修']}</span> 门</div>
                <div class="type-tag"> 思政 <span class="num">{type_count['思政']}</span> 门</div>
            </div>
        </div>

        <div class="report-section">
            <div class="section-title">💡 学习建议</div>
            <div class="advice-box">{" · ".join(advice)}</div>
        </div>

        <div class="footer">生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
</div>
</body>
</html>'''

    with open("course_schedule.html", "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open("course_schedule.html")
    print("已生成 course_schedule.html")


# ========== 主程序 ==========
my_schedule = """周一1-2节 计算机网络 n113
周一3-4节 人工智能 n522
周一5-6节 五彩缤纷的现代多媒体生活（通核）8302
周二1-2节 计算机组成原理 n217
周二3-4节 数据库原理 n213
周二5-6节 社会调查方法（混合课堂）7307
周二7-8节 毛泽东思想和中国特色社会主义 n111
周三1-2节 Java语言程序设计 n213
周三3-4节 机器学习 n323
周三5-6节 形势与政策（4）n215
周四1-2节 Java语言程序设计 n213
周四3-4节 数据库原理 n213
周四5-6节 计算机网络 n217
周四11-12节 计算机组成原理 n112
周五1-2节 Python程序设计 n113
周五3-4节 毛泽东思想和中国特色社会主义 n111
周五5-6节 传播心理学 8214
周五7-8节 大学体育4 舞二"""

if __name__ == "__main__":
    courses = parse_schedule(my_schedule)
    print(f"解析 {len(courses)} 门课程")
    with open("courses.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    generate_html(courses)