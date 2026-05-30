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


# ========== 解析单行课程 ==========
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
        "raw": line
    }


# ========== 解析全部课表 ==========
def parse_schedule(raw_text):
    courses = []
    for line in raw_text.strip().split('\n'):
        if not line.strip():
            continue
        course = parse_course_line(line)
        if course:
            courses.append(course)
    return courses


# ========== 作业管理函数 ==========
HOMEWORK_FILE = "homework.json"


def load_homework():
    """从JSON文件加载作业"""
    if os.path.exists(HOMEWORK_FILE):
        with open(HOMEWORK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_homework(homework_list):
    """保存作业到JSON文件"""
    with open(HOMEWORK_FILE, "w", encoding="utf-8") as f:
        json.dump(homework_list, f, ensure_ascii=False, indent=2)


def add_homework(name, course, due):
    """添加新作业"""
    homework_list = load_homework()
    homework_list.append({
        "name": name,
        "course": course if course else "未分类",
        "due": due,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_homework(homework_list)


def delete_homework(index):
    """删除指定索引的作业"""
    homework_list = load_homework()
    if 0 <= index < len(homework_list):
        removed = homework_list.pop(index)
        save_homework(homework_list)
        return removed
    return None


# ========== 生成完整HTML（课表+周报+作业） ==========
def generate_full_html(courses, homework_list):
    """生成包含课表、周报、作业倒计时的完整HTML页面"""

    # 计算周报数据
    weekday_courses = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for c in courses:
        if c['weekday'] in weekday_courses:
            weekday_courses[c['weekday']] += (c['end_slot'] - c['start_slot'] + 1)

    total_hours = 0
    for c in courses:
        hours = (c['end_slot'] - c['start_slot'] + 1) * 45 / 60
        total_hours += hours

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
        key = (c['weekday'], c['start_slot'])
        course_grid[key] = c

    # 生成每日负荷条
    daily_bars = ""
    max_courses = max(weekday_courses.values()) if max(weekday_courses.values()) > 0 else 1
    for day in range(1, 6):
        percent = weekday_courses[day] / max_courses * 100
        daily_bars += f'''
            <div class="bar-container">
                <div class="bar-label">{weekday_names[day]}</div>
                <div class="bar"><div class="bar-fill" style="width: {percent}%">{weekday_courses[day]}节</div></div>
            </div>'''

    # 生成作业表格和紧急提醒
    homework_rows = ""
    urgent_items = []

    for i, hw in enumerate(homework_list):
        due_date = datetime.strptime(hw['due'], "%Y-%m-%d")
        days_left = (due_date - datetime.now()).days

        if days_left < 0:
            status = f'<span class="status-overdue">⏰ 已过期{abs(days_left)}天</span>'
            status_class = "overdue"
        elif days_left == 0:
            status = '<span class="status-urgent">🔥 今天截止！</span>'
            status_class = "urgent"
            urgent_items.append(f'🔥 {hw["name"]} 今天截止！')
        elif days_left <= 3:
            status = f'<span class="status-warning">⚠️ 还剩{days_left}天</span>'
            status_class = "warning"
            urgent_items.append(f'⚠️ {hw["name"]} 还剩 {days_left} 天')
        else:
            status = f'<span class="status-normal">📅 还剩{days_left}天</span>'
            status_class = "normal"

        homework_rows += f'''
            <tr class="homework-row {status_class}" data-index="{i}">
                <td>{hw['name']}</td>
                <td>{hw.get('course', '未分类')}</td>
                <td>{hw['due']}</td>
                <td>{status}</td>
                <td><button class="delete-btn" data-index="{i}">删除</button></td>
            </tr>
        '''

    if not homework_list:
        homework_rows = '<tr><td colspan="5" style="text-align:center; color:#999;">暂无作业，下方添加吧～</td></tr>'
        urgent_html = '<li>📭 暂无作业，添加后会自动显示倒计时</li>'
    elif not urgent_items:
        urgent_html = '<li>✅ 太棒了！没有即将截止的作业</li>'
    else:
        urgent_html = ''.join([f'<li>{item}</li>' for item in urgent_items])

    # 生成建议内容
    advice_html = ""
    if weekday_courses[5] <= 2:
        advice_html += "✅ 周五课少，建议提前预习下周内容<br>"
    if type_count['体育'] == 0:
        advice_html += "🏃 本周没有体育课，记得自行安排运动<br>"
    if total_hours > 20:
        advice_html += "⚠️ 本周课程较多，注意劳逸结合<br>"
    else:
        advice_html += "👍 课程压力适中，可以适当参加社团活动<br>"

    # 将作业数据转为JSON嵌入页面（供JavaScript使用）
    homework_json = json.dumps(homework_list, ensure_ascii=False)

    # 生成完整HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能课表系统 | 课表+周报+作业</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1400px;
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
            padding: 20px 30px;
        }}
        .card-header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        .card-header p {{ opacity: 0.9; font-size: 14px; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.2);
            padding: 6px 18px;
            border-radius: 30px;
            font-size: 13px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px 10px;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }}
        td {{
            border: 1px solid #e0e0e0;
            padding: 10px 8px;
            vertical-align: top;
            height: 85px;
        }}
        .time-col {{
            background: #f8f9fa;
            font-weight: 600;
            width: 110px;
            text-align: center;
            font-size: 12px;
        }}
        .course {{
            background: #e8f0fe;
            border-radius: 8px;
            padding: 6px;
            height: 100%;
        }}
        .course-name {{ font-weight: 700; color: #1a73e8; font-size: 13px; }}
        .course-room {{ font-size: 10px; color: #666; margin-top: 4px; }}
        .empty {{ color: #ccc; text-align: center; font-size: 12px; }}

        .report-content, .homework-content {{
            padding: 25px 30px;
        }}
        .report-section {{
            margin-bottom: 25px;
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
        }}
        .report-section h3 {{
            color: #667eea;
            margin-bottom: 12px;
            font-size: 18px;
        }}
        .bar-container {{
            display: flex;
            align-items: center;
            margin: 8px 0;
        }}
        .bar-label {{
            width: 50px;
            font-weight: 600;
        }}
        .bar {{
            flex: 1;
            height: 24px;
            background: #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            margin: 0 10px;
        }}
        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 12px;
            color: white;
            line-height: 24px;
            padding-left: 8px;
            font-size: 12px;
        }}
        .type-grid {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .type-item {{
            background: #f0f0f0;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}
        .type-item span {{ font-weight: 700; color: #667eea; }}
        .advice {{
            background: #e8f0fe;
            padding: 15px 20px;
            border-radius: 12px;
            margin-top: 10px;
            line-height: 1.8;
        }}

        /* 作业表格样式 */
        .homework-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .homework-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .homework-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
            height: auto;
        }}
        .homework-row.overdue {{ background: #ffe0e0; }}
        .homework-row.urgent {{ background: #fff0e0; }}
        .homework-row.warning {{ background: #fffbe0; }}
        .status-overdue {{ color: #e74c3c; font-weight: bold; }}
        .status-urgent {{ color: #e67e22; font-weight: bold; }}
        .status-warning {{ color: #f39c12; }}
        .status-normal {{ color: #27ae60; }}

        .delete-btn {{
            background: #e74c3c;
            color: white;
            border: none;
            padding: 5px 12px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
        }}
        .delete-btn:hover {{ background: #c0392b; }}

        .urgent-box {{
            background: #fee;
            border-left: 4px solid #e74c3c;
            padding: 12px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }}
        .urgent-box ul {{
            margin-left: 20px;
            margin-top: 8px;
        }}
        .urgent-box li {{
            margin: 5px 0;
            color: #e74c3c;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 12px;
            text-align: center;
            font-size: 11px;
            color: #888;
        }}

        .btn-group {{
            display: flex;
            gap: 15px;
            margin-top: 20px;
            justify-content: center;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 30px;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{ opacity: 0.9; }}

        .add-form {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
        }}
        .add-form h3 {{ margin-bottom: 15px; color: #333; }}
        .add-form input, .add-form button {{
            padding: 10px;
            margin-right: 10px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}
        .add-form input {{
            width: 200px;
        }}
        .add-form button {{
            background: #27ae60;
            color: white;
            border: none;
            cursor: pointer;
        }}

        @media (max-width: 768px) {{
            .course-name {{ font-size: 10px; }}
            .time-col {{ width: 70px; font-size: 9px; }}
            td {{ padding: 4px; height: 65px; }}
            .report-content, .homework-content {{ padding: 15px; }}
            .add-form input {{ width: 100%; margin-bottom: 10px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <!-- 课表部分 -->
    <div class="card">
        <div class="card-header">
            <h1>📚 我的课程表</h1>
            <p>智能解析 · 一键生成</p>
            <div class="stats">
                <div class="stat-card">📖 总课程 <strong>{len(courses)}</strong> 门</div>
                <div class="stat-card">周一 <strong>{weekday_courses[1]}</strong> 节</div>
                <div class="stat-card">周二 <strong>{weekday_courses[2]}</strong> 节</div>
                <div class="stat-card">周三 <strong>{weekday_courses[3]}</strong> 节</div>
                <div class="stat-card">周四 <strong>{weekday_courses[4]}</strong> 节</div>
                <div class="stat-card">周五 <strong>{weekday_courses[5]}</strong> 节</div>
            </div>
        </div>
        <table>
            <thead>
                <tr><th></th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th></tr>
            </thead>
            <tbody>
'''

    for start, end, time_range in time_slots:
        html += f'<tr><td class="time-col">{time_range}<br><span style="font-size:9px">第{start}-{end}节</span></td>'
        for day in range(1, 6):
            course = course_grid.get((day, start))
            if course:
                html += f'''<td><div class="course">
                    <div class="course-name">{course['name']}</div>
                    <div class="course-room">📍 {course['room']}</div>
                </div></td>'''
            else:
                html += '<td><div class="empty">—</div></td>'
        html += '</tr>\n'

    html += f'''
            </tbody>
        </table>
    </div>

    <!-- 周报部分 -->
    <div class="card">
        <div class="card-header">
            <h1>📊 学业周报</h1>
            <p>本周学习数据统计与分析</p>
        </div>
        <div class="report-content">
            <div class="report-section">
                <h3>📖 课时统计</h3>
                <div class="bar-container">
                    <div class="bar-label">总课时</div>
                    <div class="bar"><div class="bar-fill" style="width: 100%">{sum(weekday_courses.values())} 节</div></div>
                </div>
                <div class="bar-container">
                    <div class="bar-label">总时长</div>
                    <div class="bar"><div class="bar-fill" style="width: {min(total_hours / 30 * 100, 100)}%">{total_hours:.1f} 小时</div></div>
                </div>
            </div>

            <div class="report-section">
                <h3>📅 每日负荷</h3>
                {daily_bars}
                <div style="margin-top: 15px;">
                    🔥 最忙的一天：{weekday_names[busiest_day]}（{weekday_courses[busiest_day]}节）<br>
                    😴 最轻松的一天：{weekday_names[freest_day]}（{weekday_courses[freest_day]}节）
                </div>
            </div>

            <div class="report-section">
                <h3>📚 课程类型分布</h3>
                <div class="type-grid">
                    <div class="type-item">💻 专业核心课 <span>{type_count['专业核心']}</span> 门</div>
                    <div class="type-item">🏃 体育课 <span>{type_count['体育']}</span> 门</div>
                    <div class="type-item">🎨 通识选修课 <span>{type_count['通识选修']}</span> 门</div>
                    <div class="type-item">📜 思政课 <span>{type_count['思政']}</span> 门</div>
                </div>
            </div>

            <div class="report-section">
                <h3>💡 学习建议</h3>
                <div class="advice">{advice_html}</div>
            </div>
        </div>
    </div>

    <!-- 作业倒计时部分 -->
    <div class="card">
        <div class="card-header">
            <h1>📝 作业倒计时</h1>
            <p>DDL提醒 · 拒绝拖延</p>
        </div>
        <div class="homework-content">
            <div class="urgent-box">
                <strong>⚠️ 紧急提醒</strong>
                <ul id="urgentList">
                    {urgent_html}
                </ul>
            </div>

            <h3 style="margin-bottom: 15px; color: #333;">📋 作业列表</h3>
            <table class="homework-table" id="homeworkTable">
                <thead>
                    <tr>
                        <th>作业名称</th>
                        <th>所属课程</th>
                        <th>截止日期</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="homeworkBody">
                    {homework_rows}
                </tbody>
            </table>

            <!-- 添加作业表单 -->
            <div class="add-form">
                <h3>➕ 添加新作业</h3>
                <input type="text" id="newName" placeholder="作业名称" style="width: 200px;">
                <input type="text" id="newCourse" placeholder="所属课程（可选）" style="width: 150px;">
                <input type="date" id="newDue" style="width: 150px;">
                <button id="addBtn">添加作业</button>
                <span id="addMsg" style="margin-left: 10px; color: green;"></span>
            </div>
        </div>
    </div>

    <div class="footer">
        📝 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</div>

<script>
    // 作业数据（从后端注入）
    let homeworkData = {homework_json};

    // 更新显示作业列表
    function updateHomeworkDisplay() {{
        const tbody = document.getElementById('homeworkBody');
        const urgentList = document.getElementById('urgentList');

        if (!homeworkData || homeworkData.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#999;">暂无作业，上方添加吧～</td></tr>';
            urgentList.innerHTML = '<li>📭 暂无作业，添加后会自动显示倒计时</li>';
            return;
        }}

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        let urgentItems = [];
        let rows = '';

        for (let i = 0; i < homeworkData.length; i++) {{
            const hw = homeworkData[i];
            const dueDate = new Date(hw.due);
            dueDate.setHours(0, 0, 0, 0);
            const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));

            let status = '';
            let statusClass = '';

            if (daysLeft < 0) {{
                status = `<span class="status-overdue">⏰ 已过期${{-daysLeft}}天</span>`;
                statusClass = 'overdue';
            }} else if (daysLeft === 0) {{
                status = '<span class="status-urgent">🔥 今天截止！</span>';
                statusClass = 'urgent';
                urgentItems.push(`🔥 ${{hw.name}} 今天截止！`);
            }} else if (daysLeft <= 3) {{
                status = `<span class="status-warning">⚠️ 还剩${{daysLeft}}天</span>`;
                statusClass = 'warning';
                urgentItems.push(`⚠️ ${{hw.name}} 还剩 ${{daysLeft}} 天`);
            }} else {{
                status = `<span class="status-normal">📅 还剩${{daysLeft}}天</span>`;
                statusClass = 'normal';
            }}

            rows += `
                <tr class="homework-row ${{statusClass}}" data-index="${{i}}">
                    <td>${{hw.name}}</td>
                    <td>${{hw.course || '未分类'}}</td>
                    <td>${{hw.due}}</td>
                    <td>${{status}}</td>
                    <td><button class="delete-btn" data-index="${{i}}">删除</button></td>
                </tr>
            `;
        }}

        tbody.innerHTML = rows;

        if (urgentItems.length === 0) {{
            urgentList.innerHTML = '<li>✅ 太棒了！没有即将截止的作业</li>';
        }} else {{
            urgentList.innerHTML = urgentItems.map(item => `<li>${{item}}</li>`).join('');
        }}

        // 绑定删除按钮事件
        document.querySelectorAll('.delete-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                const idx = parseInt(this.dataset.index);
                if (confirm('确定要删除这个作业吗？')) {{
                    homeworkData.splice(idx, 1);
                    saveHomeworkToServer();
                }}
            }});
        }});
    }}

    // 保存作业到服务器（通过后端API）
    function saveHomeworkToServer() {{
        fetch('/save_homework', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(homeworkData)
        }}).then(() => {{
            updateHomeworkDisplay();
        }}).catch(() => {{
            // 如果fetch失败，尝试表单提交方式
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/save_homework';
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'data';
            input.value = JSON.stringify(homeworkData);
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        }});
    }}

    // 添加作业
    document.getElementById('addBtn').addEventListener('click', function() {{
        const name = document.getElementById('newName').value.trim();
        const course = document.getElementById('newCourse').value.trim();
        const due = document.getElementById('newDue').value;

        if (!name) {{
            alert('请填写作业名称');
            return;
        }}
        if (!due) {{
            alert('请填写截止日期');
            return;
        }}

        // 添加到本地数据
        homeworkData.push({{
            name: name,
            course: course || '未分类',
            due: due,
            created: new Date().toISOString()
        }});

        // 保存并刷新显示
        saveHomeworkToServer();

        // 清空表单
        document.getElementById('newName').value = '';
        document.getElementById('newCourse').value = '';
        document.getElementById('newDue').value = '';

        const msg = document.getElementById('addMsg');
        msg.textContent = '✅ 添加成功！';
        setTimeout(() => {{ msg.textContent = ''; }}, 2000);
    }});

    // 初始化显示
    updateHomeworkDisplay();
</script>
</body>
</html>'''

    with open("course_schedule.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n✅ 完整页面已生成: course_schedule.html")


# ========== 启动本地服务器（支持作业保存） ==========
def start_server():
    """启动简单的HTTP服务器，支持作业数据的保存"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import urllib.parse

    class CustomHandler(SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/save_homework':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                # 如果是从表单提交的
                if isinstance(data, dict) and 'data' in data:
                    data = json.loads(data['data'])

                save_homework(data)

                self.send_response(302)
                self.send_header('Location', '/course_schedule.html')
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def do_GET(self):
            if self.path == '/':
                self.path = '/course_schedule.html'
            return SimpleHTTPRequestHandler.do_GET(self)

    # 切换到当前目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    port = 8080
    print(f"\n🌐 启动本地服务器...")
    print(f"📎 打开浏览器访问: http://localhost:{port}")
    print("💡 提示：作业添加/删除会自动保存，不要关闭此窗口")
    print("❌ 按 Ctrl+C 停止服务器\n")

    with HTTPServer(("", port), CustomHandler) as server:
        webbrowser.open(f"http://localhost:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 服务器已关闭")


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


def main():
    print("=" * 50)
    print("📅 智能课表解析系统 - 大二课程设计")
    print("=" * 50)

    # 解析课表
    courses = parse_schedule(my_schedule)
    print(f"\n✅ 成功解析 {len(courses)} 门课程")

    # 保存JSON
    with open("courses.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    print("💾 已保存到 courses.json")

    # 加载现有作业
    homework_list = load_homework()

    # 生成完整HTML
    generate_full_html(courses, homework_list)

    print("\n" + "=" * 50)
    print("🎉 页面生成完成！")
    print("=" * 50)
    print("\n生成的文件：")
    print("  📄 course_schedule.html - 主页面（课表+周报+作业）")
    print("  📄 courses.json - 课表数据备份")
    print("  📄 homework.json - 作业数据")

    # 启动服务器
    start_server()


if __name__ == "__main__":
    main()