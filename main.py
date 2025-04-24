# -- coding: utf-8 --
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import a2s
import os
import python-a2s
from email.policy import default
from playwright.async_api import async_playwright
import platform
import textwrap

class ServerStatusRenderer:
    def __init__(self):
        # 继承Status插件的背景系统
        self.background_paths = [
            os.path.join(os.path.dirname(__file__), 'htmlmaterial/ba.txt')
        ]
        
        # 样式配置
        self.config = {
            "botName": "服务器状态查询",
            "HTML_setting": {
                "Backgroundblurs": 0.1,
                "Backgroundcolor": "rgba(230, 215, 235, 0.692)",
                "dashboardTextColor1": "rgba(29,131,190,1)",
                "dashboardTextColor2": "rgba(149,40,180,1)",
                "textfont1": "./font/Gugi-Regular.ttf",
                "textfont2": "./font/HachiMaruPop-Regular.ttf"
            }
        }

    def get_random_background(self):
        """从Status插件继承的背景选择逻辑"""
        background_path = random.choice(self.background_paths)
        
        if background_path.startswith(('http://', 'https://')):
            return background_path
        elif background_path.endswith('.txt'):
            with open(background_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            return random.choice(lines).replace('\\', '/')
        else:
            files = [f for f in os.listdir(background_path) 
                    if f.lower().endswith(('.jpg', '.png', '.gif', '.bmp'))]
            return os.path.join(background_path, random.choice(files)).replace('\\', '/')

    def rgba_to_hex(self, rgba):
        """RGBA转HEX"""
        rgba = rgba.replace("rgba(", "").replace(")", "")
        r, g, b, _ = [int(x.strip()) for x in rgba.split(",")]
        return f"#{r:02x}{g:02x}{b:02x}"

    def generate_html(self, host, port, info, players):
        """生成服务器状态HTML"""
        bg_image = self.get_random_background()
        player_list = self._format_players(players)
        platform_icon = "🖥️" if platform.system() == "Windows" else "🐧"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @font-face {{ font-family: Gugi; src: url('{self.config["HTML_setting"]["textfont1"]}'); }}
        @font-face {{ font-family: HachiMaruPop; src: url('{self.config["HTML_setting"]["textfont2"]}'); }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: HachiMaruPop;
            background-color: #f5f5f5;
        }}
        
        .status-container {{
            width: 100%;
            min-height: 100vh;
            position: relative;
            background-image: url('{bg_image}');
            background-size: cover;
            background-position: center;
            padding: 40px 0;
        }}
        
        .status-container::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            backdrop-filter: blur({self.config["HTML_setting"]["Backgroundblurs"]}px);
            background: {self.config["HTML_setting"]["Backgroundcolor"]};
            z-index: 1;
        }}
        
        .status-card {{
            position: relative;
            z-index: 2;
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .server-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid {self.rgba_to_hex(self.config["HTML_setting"]["dashboardTextColor1"])};
            padding-bottom: 15px;
        }}
        
        .server-icon {{
            font-size: 50px;
            margin-right: 20px;
        }}
        
        .server-title {{
            font-family: Gugi;
            font-size: 28px;
            color: {self.rgba_to_hex(self.config["HTML_setting"]["dashboardTextColor2"])};
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .info-item {{
            display: flex;
            align-items: center;
            font-size: 18px;
        }}
        
        .info-icon {{
            margin-right: 10px;
            font-size: 24px;
        }}
        
        .players-title {{
            font-family: Gugi;
            color: {self.rgba_to_hex(self.config["HTML_setting"]["dashboardTextColor1"])};
            border-top: 2px dashed #ccc;
            padding-top: 15px;
            margin-top: 20px;
        }}
        
        .player-list {{
            max-height: 300px;
            overflow-y: auto;
            padding-right: 10px;
        }}
        
        .player-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 15px;
            margin: 8px 0;
            background: rgba(100, 100, 100, 0.05);
            border-radius: 8px;
            transition: all 0.3s;
        }}
        
        .player-item:hover {{
            background: rgba(100, 100, 100, 0.1);
            transform: translateX(5px);
        }}
        
        .footer {{
            margin-top: 20px;
            text-align: right;
            font-size: 14px;
            color: #666;
        }}
        
        .env-badge {{
            display: inline-block;
            padding: 3px 8px;
            background: {'#4CAF50' if info.platform == "w" else '#F44336'};
            color: white;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="status-container">
        <div class="status-card">
            <div class="server-header">
                <div class="server-icon">🌐</div>
                <div>
                    <h1 class="server-title">{info.server_name[:30]}</h1>
                    <div>📍 {host}:{port} • ⏱️ 延迟: {info.ping*1000:.0f}ms</div>
                </div>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-icon">🗺️</span>
                    <span>地图: {info.map_name}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">👥</span>
                    <span>玩家: {info.player_count}/{info.max_players}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">🎮</span>
                    <span>游戏: {info.game}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">🛡️</span>
                    <span>VAC: {'✅ 启用' if info.vac_enabled else '❌ 关闭'}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">🔒</span>
                    <span>密码: {'🔐 有' if info.password_protected else '无'}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">{platform_icon}</span>
                    <span>环境: 
                        <span class="env-badge">
                            {'Windows' if info.platform == "w" else 'Linux'}
                        </span>
                    </span>
                </div>
            </div>
            
            <h3 class="players-title">👑 玩家排行榜 (TOP 5)</h3>
            <div class="player-list">
                {player_list}
            </div>
            
            <div class="footer">
                {self.config["botName"]} • 运行环境: {platform.system()} {platform.release()}
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html

    def _format_players(self, players):
        """格式化玩家列表"""
        if not players:
            return '<div style="text-align:center;padding:20px;">🌙 暂无玩家在线</div>'
        
        sorted_players = sorted(players, key=lambda x: x.score, reverse=True)[:10]
        html = ""
        for idx, player in enumerate(sorted_players, 1):
            duration = self._format_duration(player.duration)
            html += f"""
            <div class="player-item">
                <span>#{idx-1} {player.name[:20]}</span>
                <span>🎯 {player.score} ⏳ {duration}</span>
            </div>
            """
        return html

    def _format_duration(self, seconds):
        """格式化游戏时长"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

async def render_to_image(html, output="server_status.png"):
    """渲染HTML为图片"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        await page.screenshot(path=output, full_page=True)
        await browser.close()
    return output

@register("server_info", "服务器查询", "A2S协议服务器状态查询插件", "2.0.0")
class ServerQuery(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.renderer = ServerStatusRenderer()

    def format_response(self, host, port, info, players):
        """优化后的纯文本排版格式"""
        header = "服 务 器 信 息："
        
        base_info = textwrap.dedent(f"""│ ▎🔍 地址：{host}:{port} ▏ ⏱️ 延迟：{info.ping*1000}ms
        │ ▎🔖 名称：{info.server_name[:28]:<30}
        │ ▎🌐 地图：{info.map_name:<12} ▏ 👥 玩家：{info.player_count}/{info.max_players} ▏ 🤖 智能人：{info.bot_count}
        │ ▎🎮 游戏模式：{info.game:<12} ▏ 🖥️ 类型：{['⚙️ 专用服务器', '🔗 监听服务器'][info.server_type == 'l']} ▏ 📜 版本：{info.version}
        │ ▎🔒 保护：{'🛡️ VAC已启用' if info.vac_enabled else '⚠️ 无保护'} ▏ 🔑 密码：{'🔐 有' if info.password_protected else '🔓 无'} ▏ 🧾 环境：{'✅ 可信任环境' if info.platform == "w" else '❌ 不可信任环境'}
        ─────玩 家 排 行─────""").strip()

        player_list = ""
        if players:
            top_players = sorted(players, key=lambda x: x.score, reverse=True)[:5]
            for idx, player in enumerate(top_players, 1):
                mins, secs = divmod(int(player.duration), 60)
                hours, mins = divmod(mins, 60)
                player_list += (
                    f"#{idx} {player.name[:16]:<16} "
                    f"🎯{player.score:<4} ⏳{hours:02d}:{mins:02d}\n"
                )
        else:
            player_list += "🌙 暂无玩家在线\n"

        rules_section = ""
        important_rules = {
            'tv_port': 'STV端口',
            'mp_timelimit': '回合时间',
            'sv_region': '服务器地区'
        }
        """
        for rule, desc in important_rules.items():
            if rule in rules:
                rules_section += f"▎{desc}: {rules[rule]}\n"
        """
        return textwrap.dedent(f"""
        {header}
        {base_info}
        {player_list}
        """)

    async def _query_server(self, host, port):
        """通用查询方法"""
        address = (host, port)
        info = await a2s.ainfo(address)
        players = await a2s.aplayers(address)
        html = self.renderer.generate_html(host, port, info, players)
        image_path = await render_to_image(html)
        return image_path

    @filter.command("ip")
    async def query_server(self, event: AstrMessageEvent, *, name: str):
        try:
            if ":" not in name:
                yield event.plain_result("格式: /ip 地址:端口")
                return
                
            host, port = name.rsplit(":", 1)
            if not port.isdigit():
                raise ValueError("端口必须是数字")
                
            image_path = await self._query_server(host, int(port))
            yield event.image_result(image_path)
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            yield event.plain_result(
                "⛔ 查询失败，请检查：\n"
                "1. 服务器是否在线\n"
                "2. 输入地址是否正确\n"
                "3. 稍后重试"
            )

    @filter.command("ipt")
    async def query_text_server(self, event: AstrMessageEvent, *, name: str):
        try:
            if ":" not in name:
                yield event.plain_result("格式: /ip 地址:端口")
                return
                
            host, port = name.rsplit(":", 1)
            if not port.isdigit():
                raise ValueError("端口必须是数字")
            
            address = host, int(port)
            info = await a2s.ainfo(address)
            players = await a2s.aplayers(address)
            #rules = await a2s.arules(address)
            yield event.plain_result(self.format_response(host, port, info, players))
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            yield event.plain_result(
                "⛔ 查询失败，请检查：\n"
                "1. 服务器是否在线\n"
                "2. 输入地址是否正确\n"
                "3. 稍后重试"
            )
            
    @filter.command("a2s_help")
    async def query_server_help(self, event: AstrMessageEvent):
        yield event.plain_result("AS2S协议服务器状态查询插件\n"
                           "指令：\n"
                           "/ip ip:port (image)\n"
                           "/ipt ip:port (text)\n"
                           "作者：ZvZPvz\n"
                           "版本：1.0.0\n"
                           "Github：https://github.com/ZvZPvz/astrbot_plugin_a2s")
