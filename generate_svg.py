import json
import random
import base64
import urllib.request

CELL_SIZE = 10
CELL_MARGIN = 4
STEP = CELL_SIZE + CELL_MARGIN

URLS = {
    "mario": "https://raw.githubusercontent.com/ARIIVIDERCHII/assets/main/8bit-mario-runing.gif",
    "bowser": "https://raw.githubusercontent.com/ARIIVIDERCHII/assets/main/bowser.gif",
    "monsters": [
        "https://raw.githubusercontent.com/ARIIVIDERCHII/assets/main/goomba-mario.gif",
        "https://raw.githubusercontent.com/ARIIVIDERCHII/assets/main/koopa-troopa-koopa.gif"
    ]
}

def get_base64(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            return f"data:image/gif;base64,{base64.b64encode(r.read()).decode('utf-8')}"
    except Exception:
        return url

MARIO_B64 = get_base64(URLS["mario"])
BOWSER_B64 = get_base64(URLS["bowser"])
MONSTERS_B64 = [get_base64(u) for u in URLS["monsters"]]

class Entity:
    def __init__(self, col, row, width, height, offset_x=0, offset_y=0):
        self.col = col
        self.row = row
        self.x = col * STEP + CELL_MARGIN + offset_x
        self.y = row * STEP + CELL_MARGIN + offset_y
        self.width = width
        self.height = height

class Block(Entity):
    def __init__(self, col, row, color, is_green):
        super().__init__(col, row, CELL_SIZE, CELL_SIZE)
        self.color = color
        self.is_green = is_green
        self.id = f"block-{col}-{row}"

class Monster(Entity):
    def __init__(self, col, row):
        super().__init__(col, row, 20, 20, -5, -10)
        self.sprite = random.choice(MONSTERS_B64)
        self.id = f"monster-{col}-{row}"

class Timeline:
    def __init__(self):
        self.points = []
        self.css = ""
        self.current_c = -2
        self.current_r = 0
        self.p_clear = None
        self.p_defeat = None

    def start(self, c, r):
        self.current_c, self.current_r = c, r
        self.points.append({'c': c, 'r': r})
        return self

    def move_to(self, c, r):
        self.current_c, self.current_r = c, r
        self.points.append({'c': c, 'r': r})
        return self

    def jump_on_monster(self, m_id):
        self.points[-1]['monster_id'] = m_id
        return self

    def break_block(self, b_id):
        self.points[-1]['break_id'] = b_id
        return self
        
    def trigger_clear(self):
        self.points[-1]['is_clear'] = True
        return self

    def trigger_boss(self, is_victory):
        self.points[-1]['boss_fight'] = True
        self.points[-1]['is_victory'] = is_victory
        return self

    def compile(self):
        total = len(self.points) - 1
        t_x = "@keyframes path-x {\n"
        t_y = "@keyframes path-y {\n"
        t_z = "@keyframes path-jump {\n  0% { transform: translateY(0); }\n"
        t_dir = "@keyframes path-dir {\n  0% { transform: scaleX(1); }\n"
        
        last_dir = 1
        
        for i, pt in enumerate(self.points):
            p = (i / total) * 100
            x, y = pt['c'] * STEP, pt['r'] * STEP
            
            t_x += f"  {p:.2f}% {{ transform: translateX({x}px); }}\n"
            t_y += f"  {p:.2f}% {{ transform: translateY({y}px); }}\n"

            if i < total:
                next_x = self.points[i+1]['c'] * STEP
                new_dir = -1 if next_x < x else (1 if next_x > x else last_dir)
                if new_dir != last_dir:
                    t_dir += f"  {p - 0.01:.2f}% {{ transform: scaleX({last_dir}); }}\n"
                    t_dir += f"  {p:.2f}% {{ transform: scaleX({new_dir}); }}\n"
                    last_dir = new_dir

            if pt.get('monster_id') or pt.get('break_id') or pt.get('boss_fight'):
                p_prev = max(0, ((i-1)/total)*100)
                p_mid = (p_prev + p) / 2
                jump_h = -40 if pt.get('boss_fight') else (-18 if pt.get('monster_id') else -10)
                
                t_z += f"  {max(0, p_prev - 0.01):.2f}% {{ transform: translateY(0); }}\n"
                t_z += f"  {p_prev:.2f}% {{ transform: translateY(0); animation-timing-function: ease-out; }}\n"
                t_z += f"  {p_mid:.2f}% {{ transform: translateY({jump_h}px); animation-timing-function: ease-in; }}\n"
                t_z += f"  {p:.2f}% {{ transform: translateY(0); }}\n"
                t_z += f"  {min(100, p + 0.01):.2f}% {{ transform: translateY(0); }}\n"

            if pt.get('break_id'):
                b_id = pt['break_id']
                self.css += f"@keyframes brk-{b_id} {{ 0%, {max(0, p-0.1):.2f}% {{ transform: scale(1); opacity: 1; }} {p:.2f}% {{ transform: scale(1.5); opacity: 0; }} 100% {{ transform: scale(0); opacity: 0; }} }}\n"
                self.css += f"#{b_id} {{ animation: brk-{b_id} var(--run-time) linear infinite; transform-box: fill-box; transform-origin: center; }}\n"
                
                c_id = f"coin-{b_id}"
                self.css += f"@keyframes pop-{c_id} {{ 0%, {max(0, p-0.1):.2f}% {{ transform: translateY(0) scale(0.5); opacity: 0; }} {p:.2f}% {{ transform: translateY(-20px) scale(1.2); opacity: 1; }} {min(100, p+1.0):.2f}%, 100% {{ transform: translateY(-40px) scale(0.5); opacity: 0; }} }}\n"
                self.css += f"#{c_id} {{ animation: pop-{c_id} var(--run-time) linear infinite; opacity: 0; transform-box: fill-box; transform-origin: center; }}\n"

            if pt.get('monster_id'):
                m_id = pt['monster_id']
                self.css += f"@keyframes kll-{m_id} {{ 0%, {max(0, p-0.1):.2f}% {{ transform: scaleY(1); opacity: 1; }} {p:.2f}% {{ transform: scaleY(0.1) translateY(10px); opacity: 0; }} 100% {{ transform: scaleY(0); opacity: 0; }} }}\n"
                self.css += f"#{m_id} {{ animation: kll-{m_id} var(--run-time) linear infinite; transform-box: fill-box; transform-origin: bottom center; }}\n"

            if pt.get('is_clear'):
                self.p_clear = p
                self.css += f"@keyframes clr-monsters {{ 0%, {p:.2f}% {{ opacity: 1; }} {min(100, p+1):.2f}%, 100% {{ opacity: 0; }} }}\n"
                self.css += f"#monsters {{ animation: clr-monsters var(--run-time) linear infinite; }}\n"

            if pt.get('boss_fight'):
                if pt['is_victory']:
                    self.p_defeat = p 
                    self.css += f"@keyframes boss-die {{ 0%, {self.p_clear:.2f}% {{ opacity: 0; transform: translateY(-50px) scale(0); }} {min(100, self.p_clear+1):.2f}%, {max(0, p-0.5):.2f}% {{ opacity: 1; transform: translateY(0) scale(1); filter: brightness(1); }} {p:.2f}% {{ transform: scaleY(0.3) scaleX(1.5) translateY(20px); filter: brightness(2) hue-rotate(-50deg); opacity: 0.8; }} {min(100, p+1.0):.2f}%, 100% {{ transform: scale(0); opacity: 0; }} }}\n"
                    self.css += f"#boss-entity {{ animation: boss-die var(--run-time) linear infinite; opacity: 0; }}\n"
                else:
                    self.css += f"@keyframes boss-win {{ 0%, {self.p_clear:.2f}% {{ opacity: 0; transform: translateY(-50px) scale(0); }} {min(100, self.p_clear+1):.2f}%, 100% {{ opacity: 1; transform: translateY(0) scale(1); }} }}\n"
                    self.css += f"#boss-entity {{ animation: boss-win var(--run-time) linear infinite; opacity: 0; }}\n"
                    
                    self.css += f"@keyframes mario-dmg {{ 0%, {max(0, p-0.1):.2f}% {{ opacity: 1; transform: translate(0,0) rotate(0); filter: none; }} {p:.2f}% {{ filter: hue-rotate(90deg) saturate(5); transform: translate(-20px, -20px) rotate(-45deg); opacity: 1; }} {min(100, p+4):.2f}% {{ transform: translate(-40px, 150px) rotate(-90deg); opacity: 0; filter: hue-rotate(90deg) saturate(5); }} 100% {{ opacity: 0; transform: translate(0, 150px); }} }}\n"
                    self.css += f"#mario-sprite {{ animation: mario-dmg var(--run-time) linear infinite; transform-box: fill-box; transform-origin: center; }}\n"
                    
                    self.css += f"@keyframes game-over-anim {{ 0%, {max(0, p-0.1):.2f}% {{ opacity: 0; transform: translateY(20px) scale(0.5); }} {min(100, p+2.0):.2f}%, 100% {{ opacity: 1; transform: translateY(0) scale(1); }} }}\n"
                    self.css += f"#game-over-screen {{ animation: game-over-anim var(--run-time) cubic-bezier(0.175, 0.885, 0.32, 1.275) infinite; transform-box: fill-box; transform-origin: center; }}\n"

        t_x += "}\n"
        t_y += "}\n"
        t_z += "  100% { transform: translateY(0); }\n}\n"
        t_dir += "  100% { transform: scaleX(" + str(last_dir) + "); }\n}\n"
        
        return t_x + t_y + t_z + t_dir + self.css

def generate():
    try:
        with open("contributions.json", "r") as f: data = json.load(f)
    except:
        return

    weeks = data['weeks']
    b_width = len(weeks) * STEP + CELL_MARGIN
    b_height = 7 * STEP + CELL_MARGIN

    blocks, green_blocks, empty_cells = [], [], []
    max_streak, curr_streak = 0, 0

    for x, week in enumerate(weeks):
        for y_idx, day in enumerate(week['contributionDays']):
            y = y_idx + (7 - len(week['contributionDays'])) if x == 0 and len(week['contributionDays']) < 7 else y_idx
            is_green = day['contributionCount'] > 0
            b = Block(x, y, day['color'], is_green)
            blocks.append(b)
            if is_green:
                green_blocks.append(b)
                curr_streak += 1
                max_streak = max(max_streak, curr_streak)
            else:
                empty_cells.append(b)
                curr_streak = 0

    monsters = [Monster(c.col, c.row) for c in random.sample(empty_cells, int(len(empty_cells) * 0.08))]
    m_dict = {(m.col, m.row): m for m in monsters}

    tl = Timeline().start(-2, 0)
    targets = list(green_blocks)
    
    while targets:
        n = min(targets, key=lambda b: abs(b.col - tl.current_c) + abs(b.row - tl.current_r))
        targets.remove(n)
        
        if n.col != tl.current_c:
            sx = 1 if n.col > tl.current_c else -1
            for c in range(tl.current_c + sx, n.col + sx, sx):
                tl.move_to(c, tl.current_r)
                if (c, tl.current_r) in m_dict: tl.jump_on_monster(m_dict[(c, tl.current_r)].id)

        if n.row != tl.current_r:
            sy = 1 if n.row > tl.current_r else -1
            for r in range(tl.current_r + sy, n.row + sy, sy):
                tl.move_to(tl.current_c, r)
                if (tl.current_c, r) in m_dict: tl.jump_on_monster(m_dict[(tl.current_c, r)].id)

        tl.break_block(n.id)

    tl.trigger_clear()
    boss_c, boss_r = len(weeks) // 2, 3
    tl.move_to(tl.current_c, boss_r).move_to(boss_c + (2 if tl.current_c > boss_c else -2), boss_r)

    is_victory = max_streak >= 10
    
    if is_victory:
        tl.move_to(boss_c, boss_r).trigger_boss(True)
        for c in range(boss_c + 1, len(weeks) + 3):
            tl.move_to(c, boss_r)
        for _ in range(10): 
            tl.move_to(len(weeks) + 3, boss_r)
    else:
        tl.move_to(boss_c - 0.5, boss_r).trigger_boss(False)
        for _ in range(15): tl.move_to(boss_c - 0.5, boss_r)

    run_time = max(20, len(tl.points) * 0.14)

    compiled_timeline = tl.compile()
    safe_p_defeat = tl.p_defeat if tl.p_defeat else 90.0

    svg_blocks = "".join([f'<rect id="{b.id}" x="{b.x}" y="{b.y}" width="{b.width}" height="{b.height}" fill="{b.color}" rx="2" ry="2" />' for b in blocks])
    svg_coins = "".join([f'<circle id="coin-{b.id}" cx="{b.x+5}" cy="{b.y+5}" r="4" fill="#FFD700" stroke="#DAA520" style="transform-box: fill-box; transform-origin: center;" />' for b in green_blocks])
    svg_monsters = "".join([f'<g id="{m.id}"><image href="{m.sprite}" x="{m.x}" y="{m.y}" width="{m.width}" height="{m.height}" style="animation: float 2s infinite alternate;"/></g>' for m in monsters])
    
    boss_x, boss_y = boss_c*STEP+CELL_MARGIN-15, boss_r*STEP+CELL_MARGIN-25

    game_over_screen = ""
    victory_screen = ""
    rain_css = ""
    rain_svg = ""

    if not is_victory:
        game_over_screen = f"""
        <g id="game-over-screen" style="opacity: 0;">
            <rect width="100%" height="100%" fill="#000" opacity="0.6" />
            <text x="50%" y="50%" font-family="'Courier New', monospace" font-size="64" font-weight="bold" fill="#ff4444" text-anchor="middle" stroke="#000" stroke-width="3">GAME OVER</text>
            <text x="50%" y="60%" font-family="'Courier New', monospace" font-size="20" fill="#fff" text-anchor="middle" stroke="#000" stroke-width="1">STREAK IS TOO LOW ({max_streak} DAYS)</text>
        </g>
        """
    else:
        for i in range(50):
            cx = random.randint(0, b_width)
            cy = random.randint(-80, -10)
            dur = round(random.uniform(1.0, 2.5), 2)
            delay = round(random.uniform(0, 2.0), 2)
            rain_svg += f'<circle cx="{cx}" cy="{cy}" r="3" fill="#FFD700" stroke="#DAA520" stroke-width="1" style="animation: coin-fall {dur}s linear {delay}s infinite;" />\n'

        victory_screen = f"""
        <g id="victory-screen" style="opacity: 0;">
            <rect width="100%" height="100%" fill="#000" opacity="0.5" />
            <text x="50%" y="50%" font-family="'Courier New', monospace" font-size="64" font-weight="bold" fill="#FFD700" text-anchor="middle" stroke="#000" stroke-width="3">VICTORY!</text>
            <text x="50%" y="60%" font-family="'Courier New', monospace" font-size="20" fill="#fff" text-anchor="middle" stroke="#000" stroke-width="1">EPIC STREAK: {max_streak} DAYS</text>
            <g id="coin-rain">
                {rain_svg}
            </g>
        </g>
        """
        
        rain_css = f"""
        @keyframes coin-fall {{
            0% {{ transform: translateY(0) rotate(0deg); }}
            100% {{ transform: translateY({b_height + 150}px) rotate(360deg); }}
        }}
        @keyframes show-victory {{
            0%, {safe_p_defeat:.2f}% {{ opacity: 0; }}
            {min(100, safe_p_defeat + 1.0):.2f}%, 100% {{ opacity: 1; }}
        }}
        #victory-screen {{ animation: show-victory var(--run-time) linear infinite; transform-box: fill-box; transform-origin: center; }}
        """

    css = f"""
    <style>
        :root {{ --run-time: {run_time}s; }}
        svg {{ image-rendering: pixelated; }}
        @keyframes float {{ 0% {{ transform: translateY(-2px); }} 100% {{ transform: translateY(2px); }} }}
        {compiled_timeline}
        {rain_css}
        #mario-x {{ animation: path-x var(--run-time) linear infinite; }}
        #mario-y {{ animation: path-y var(--run-time) linear infinite; }}
        #mario-jump {{ animation: path-jump var(--run-time) linear infinite; }}
        #mario-dir {{ animation: path-dir var(--run-time) linear infinite; transform-box: fill-box; transform-origin: center; }}
        #boss-entity {{ transform-box: fill-box; transform-origin: bottom center; }}
    </style>
    """

    svg = f"""<svg width="{b_width}" height="{b_height}" viewBox="0 0 {b_width} {b_height}" xmlns="http://www.w3.org/2000/svg">
    {css}
    <rect width="{b_width}" height="{b_height}" fill="#ffffff" />
    <g id="grid">{svg_blocks}</g>
    <g id="coins">{svg_coins}</g>
    <g id="monsters">{svg_monsters}</g>
    <g id="boss-entity" style="opacity: 0;"><image href="{BOWSER_B64}" x="{boss_x}" y="{boss_y}" width="40" height="40" style="animation: float 2s infinite alternate;"/></g>
    <g id="mario-x"><g id="mario-y"><g id="mario-jump"><g id="mario-dir"><image id="mario-sprite" href="{MARIO_B64}" x="-7" y="-14" width="24" height="24" /></g></g></g></g>
    {game_over_screen}
    {victory_screen}
    </svg>"""

    with open("mario-final.svg", "w") as f: f.write(svg)

if __name__ == "__main__":
    generate()