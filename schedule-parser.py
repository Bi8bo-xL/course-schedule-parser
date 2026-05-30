import re
import json
import webbrowser
import os

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

    # 改进：尝试从末尾提取教室（可能没有空格）
    if ' ' in rest:
        parts = rest.rsplit(' ', 1)
        name = parts[0].strip()
        room = parts[1].strip()
    else:
        # 没有空格时，尝试提取末尾的教室（数字+字母组合）
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
        "raw": line
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
    """生成HTML课表"""
    # 课程时间槽位定义（1-12节）
    time_slots = [
        (1, 2, "08:00-09:40"), (3, 4, "09:50-11:30"), (5, 6, "13:30-15:10"),
        (7, 8, "15:20-17:00"), (9, 10, "18:30-20:10"), (11, 12, "20:20-22:00")
    ]

    # 按星期和节次建立索引
    course_grid = {}
    for c in courses:
        key = (c['weekday'], c['start_slot'])
        course_grid[key] = c

    # 生成HTML
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的课程表</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 14px;
        }
        .stat-card strong { font-size: 20px; margin-right: 5px; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 15px 10px;
            font-size: 16px;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
        }
        td {
            border: 1px solid #e0e0e0;
            padding: 12px 8px;
            vertical-align: top;
            min-width: 120px;
            height: 100px;
        }
        .time-col {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            width: 120px;
            text-align: center;
        }
        .course {
            background: #e8f0fe;
            border-radius: 8px;
            padding: 8px;
            height: 100%;
            transition: transform 0.2s;
        }
        .course:hover { transform: scale(1.02); background: #d4e4fc; }
        .course-name { font-weight: 700; color: #1a73e8; font-size: 14px; margin-bottom: 5px; }
        .course-room { font-size: 11px; color: #666; margin-top: 5px; }
        .empty { color: #ccc; font-size: 12px; text-align: center; padding: 20px 0; }
        .footer {
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #888;
        }
        @media (max-width: 768px) {
            .course-name { font-size: 11px; }
            .time-col { width: 80px; font-size: 11px; }
            td { padding: 6px; height: 80px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📚 我的课程表</h1>
        <p>智能解析 · 一键生成</p>
'''

    # 统计信息
    total_courses = len(courses)
    weekdays_count = {i: 0 for i in range(1, 6)}
    for c in courses:
        if 1 <= c['weekday'] <= 5:
            weekdays_count[c['weekday']] += 1

    html += f'''
        <div class="stats">
            <div class="stat-card">📖 总课程 <strong>{total_courses}</strong> 门</div>
            <div class="stat-card">📅 周一 <strong>{weekdays_count[1]}</strong> 节</div>
            <div class="stat-card">📅 周二 <strong>{weekdays_count[2]}</strong> 节</div>
            <div class="stat-card">📅 周三 <strong>{weekdays_count[3]}</strong> 节</div>
            <div class="stat-card">📅 周四 <strong>{weekdays_count[4]}</strong> 节</div>
            <div class="stat-card">📅 周五 <strong>{weekdays_count[5]}</strong> 节</div>
        </div>
    </div>
    <table>
        <thead>
            <tr><th></th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th></tr>
        </thead>
        <tbody>
'''

    for start, end, time_range in time_slots:
        html += f'''
            <tr>
                <td class="time-col">{time_range}<br><span style="font-size:10px">第{start}-{end}节</span></td>
'''
        for day in range(1, 6):
            course = course_grid.get((day, start))
            if course:
                html += f'''
                <td>
                    <div class="course">
                        <div class="course-name">{course['name']}</div>
                        <div class="course-room">📍 {course['room']}</div>
                    </div>
                </td>
'''
            else:
                html += '<td><div class="empty">—</div></td>'
        html += '</tr>\n'

    html += '''
        </tbody>
    </table>
    <div class="footer">
        生成时间: ''' + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
    </div>
</div>
</body>
</html>
'''

    # 保存并打开
    with open("course_schedule.html", "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open("file://" + os.path.abspath("course_schedule.html"))
    print("\n✅ HTML课表已生成: course_schedule.html")
    print("🌐 正在浏览器中打开...")


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

print("=" * 40)
print("📅 课表解析系统")
print("=" * 40)

courses = parse_schedule(my_schedule)
print(f"\n✅ 成功解析 {len(courses)} 门课程")

# 保存JSON
with open("courses.json", "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)
print("💾 已保存到 courses.json")

# 生成HTML课表
generate_html(courses)

print("\n🎉 完成！按回车键退出...")
input()