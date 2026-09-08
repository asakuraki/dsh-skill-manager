#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 SKILL-MANIFEST.md 给 ai_classify_task.json 填充分类+中文简介。"""
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent / "data" / "ai_classify_task.json"

# skill 名 -> (category, description, note)
DATA = {
    # ---------- A. 架构与基础 + 流程引擎 ----------
    "godot-master": ("架构·总指挥", "Godot 总指挥/全能入口，编排其余 92 个领域 skill，含架构决策矩阵、15 反模式、性能预算。新建项目或系统总览优先进它。", "几乎必备：Power of One 二选一推荐"),
    "godot-ai-navigation": ("架构·AI", "AI 移动决策路由：追敌/巡逻/人群 RVO/寻路烘焙。多与 godot-navigation-pathfinding 搭配。", ""),
    "godot-analyst": ("架构·流程", "分析师 persona（Anara）：给项目架构/现代化程度打分与认证。", ""),
    "godot-auditor": ("架构·流程", "审计 persona（Aurelius）：never-list 反模式强制审计。", ""),
    "godot-builder": ("架构·流程", "构建器 persona：headless CLI 场景搭建、构建编排、CI。", ""),
    "godot-autoload-architecture": ("架构·基础", "AutoLoad 全局单例架构：GameManager、SaveManager、场景切换、信号总线。", ""),
    "godot-composition": ("架构·基础", "游戏实体 Entity-Component 组合架构：NPC/武器/敌人/命中框，'Has-A' 关系。", ""),
    "godot-composition-apps": ("架构·基础", "应用/工具/EditorPlugin 的组合架构（非游戏实体，UI 为主）。", ""),
    "godot-debugging-profiling": ("架构·流程", "生产级调试/性能分析：内存泄漏、GPU Profiler、孤儿节点、headless CI QA。", ""),
    "godot-gdscript-mastery": ("架构·语言", "GDScript 各种雷区指南：静态类型、信号、@onready、Callable、typed 集合。", ""),
    "godot-project-foundations": ("架构·基础", "项目结构规范：feature 文件夹、命名约定、.gitignore、版本控制。", ""),
    "godot-project-templates": ("架构·基础", "类型项目脚手架导航：bootstrap、PCK、feature tags。", ""),
    "godot-resource-data-patterns": ("架构·基础", "Resource/数据驱动设计：道具库、角色属性、序列化。", ""),
    "godot-signal-architecture": ("架构·基础", "信号架构 'Signal Up, Call Down' 解耦。", ""),
    "godot-state-machine-advanced": ("架构·AI", "层级状态机 HSM + 下推自动机，用于复杂 AI 与角色行为。", ""),
    "godot-version-migration": ("架构·流程", "Godot 版本迁移枢纽：1.x→4.7 全历史升级。", ""),

    # ---------- B. 2D 系统 ----------
    "godot-2d-animation": ("2D 系统", "AnimatedSprite2D/SpriteFrames 帧动画、骨骼 cutout、程序化动画。", ""),
    "godot-2d-physics": ("2D 系统", "2D 碰撞层/掩码、Area2D、RayCast2D、DirectSpaceState 查询。", ""),
    "godot-animation-player": ("2D 系统", "AnimationPlayer 时间轴动画、root motion、RESET 轨道。", ""),
    "godot-animation-tree-mastery": ("2D 系统", "AnimationTree/StateMachine/BlendSpace2D 复杂动画。", ""),
    "godot-camera-systems": ("2D 系统", "2D/3D 相机跟随、震动(trauma)、死区、look-ahead。", ""),
    "godot-characterbody-2d": ("2D 系统", "CharacterBody2D 平台类移动：coyote time、jump buffer、单向平台。", ""),
    "godot-particles": ("2D 系统", "GPUParticles2D/3D 粒子特效、渐变、子发射器。", ""),
    "godot-shaders-basics": ("2D 系统", "CanvasItem shader、后处理、实例 uniform、批量安全。", ""),
    "godot-tilemap-mastery": ("2D 系统", "TileMapLayer/TileSet、地形自动连接、运行时编辑。", ""),
    "godot-tweening": ("2D 系统", "Tween 程序化动画、juice/手感、缓动函数。", "做 UI 动画常用"),

    # ---------- C. 3D 系统 ----------
    "godot-3d-lighting": ("3D 系统", "3D 光照：DirectionalLight3D、GI、LightmapGI、阴影级联。", ""),
    "godot-3d-materials": ("3D 系统", "StandardMaterial3D PBR、ORM 贴图、透明度模式。", ""),
    "godot-3d-world-building": ("3D 系统", "GridMap/CSG 关卡搭建、遮挡剔除。", ""),
    "godot-navigation-pathfinding": ("3D 系统", "NavigationAgent2D/3D 寻路、RVO 避障、NavMesh。", ""),
    "godot-physics-3d": ("3D 系统", "3D 物理：RigidBody3D、布娃娃、Joint3D、碰撞层。", ""),
    "godot-procedural-generation": ("3D 系统", "程序化生成：FastNoiseLite、BSP、WFC、种子随机。", ""),
    "godot-raycasting-queries": ("3D 系统", "RayCast/ShapeCast/DirectSpaceState 查询、鼠标拾取。", ""),

    # ---------- D. 玩法机制 ----------
    "godot-ability-system": ("玩法机制", "技能/能力系统：冷却、技能树、连招、升级路径。", ""),
    "godot-combat-system": ("玩法机制", "战斗系统：hitbox/hurtbox、伤害计算、无敌帧。", ""),
    "godot-dialogue-system": ("玩法机制", "分支对话系统：对话图、打字机、本地化。", ""),
    "godot-economy-system": ("玩法机制", "游戏经济：多货币、商店、动态定价、掉落表。", ""),
    "godot-game-loop-collection": ("玩法机制", "收集循环：寻宝、收集品、指北针 UI、完成度百分比。", ""),
    "godot-game-loop-harvest": ("玩法机制", "资源采集循环：挖矿/伐木/采集、工具等级。", ""),
    "godot-game-loop-time-trial": ("玩法机制", "计时赛/竞速 + 幽灵录像回放。", ""),
    "godot-game-loop-waves": ("玩法机制", "波次刷怪、难度缩放、回合管理。", ""),
    "godot-inventory-system": ("玩法机制", "背包系统：格子、堆叠、负重、拖拽 UI。", ""),
    "godot-mechanic-revival": ("玩法机制", "死亡/复活机制：魂系、尸魂、复活代价。", ""),
    "godot-mechanic-secrets": ("玩法机制", "秘籍/隐藏元素：Konami 码、输入序列缓冲、秘密持久化。", ""),
    "godot-monte-carlo-balancer": ("玩法机制", "蒙特卡洛数值平衡实验室：模拟玩家胜率/经济。", ""),
    "godot-quest-system": ("玩法机制", "任务系统：目标、奖励、分支链。", ""),
    "godot-rpg-stats": ("玩法机制", "RPG 属性/升级/modifier/伤害公式。", ""),
    "godot-save-load-systems": ("玩法机制", "存档/读档：JSON、序列化、版本迁移、加密。", ""),
    "godot-scene-management": ("玩法机制", "场景加载/转换/异步加载/对象池。", ""),
    "godot-turn-system": ("玩法机制", "回合制战斗：行动点、相位、ATB、时间轴。", ""),

    # ---------- E. UI & UX + 视觉质检 ----------
    "godot-agent-vision": ("UI·视觉质检", "AI 截屏看 UI/资源/编辑器做视觉质检（anti-slop 评分）。独特能力，无替代。", "唯一无替代的能力"),
    "godot-input-handling": ("UI·输入", "输入处理：InputMap、手柄、按键重绑、死区、输入缓冲。", ""),
    "godot-ui-containers": ("UI·布局", "响应式布局：Container 节点、锚点、size_flags。", ""),
    "godot-ui-rich-text": ("UI·文本", "RichTextLabel / BBCode 富文本。", ""),
    "godot-ui-theming": ("UI·主题", "Theme / StyleBox / 全局皮肤 / 深色模式。", ""),
    "godot-theme-easter": ("UI·主题", "节日主题覆盖：复活节彩蛋皮肤、StyleBox 注入。", ""),

    # ---------- F. 连接与平台 ----------
    "godot-audio-systems": ("平台·音频", "音频系统：AudioBus、空间音效、音乐交叉淡入、音频池。", ""),
    "godot-export-builds": ("平台·导出", "多平台导出 + CI/CD + 签名。", ""),
    "godot-multiplayer-networking": ("平台·联网", "多人网络：MultiplayerSynchronizer、客户端预测、回滚。", ""),
    "godot-performance-optimization": ("平台·性能", "性能分析/优化：draw call、MultiMesh、LOD、对象池。", ""),
    "godot-platform-console": ("平台·主机", "主机平台：PS/Xbox/Switch 认证、手柄优先 UI。", ""),
    "godot-platform-desktop": ("平台·桌面", "桌面平台：Steam、窗口管理、设置菜单。", ""),
    "godot-platform-mobile": ("平台·移动", "移动平台：触控、安全区、省电、应用商店。", ""),
    "godot-platform-vr": ("平台·VR", "VR 平台：OpenXR、舒适设置、手势追踪。", ""),
    "godot-platform-web": ("平台·Web", "Web/HTML5 导出：JavaScriptBridge、localStorage、WebGL2。", ""),
    "godot-server-architecture": ("平台·服务器", "专用/headless 多人服务器、权威校验、防作弊。", ""),
    "godot-testing-patterns": ("平台·测试", "测试决策树：GdUnit4、单测/场景/CI、快照、模拟网络。", ""),

    # ---------- G. 适配指南 ----------
    "godot-adapt-2d-to-3d": ("适配指南", "2D 游戏迁移到 3D。", ""),
    "godot-adapt-3d-to-2d": ("适配指南", "3D 简化/移植到 2D（2.5D、等距）。", ""),
    "godot-adapt-desktop-to-mobile": ("适配指南", "桌面移植到移动。", ""),
    "godot-adapt-mobile-to-desktop": ("适配指南", "移动移植到桌面。", ""),
    "godot-adapt-single-to-multiplayer": ("适配指南", "单机改多人/联机。", ""),

    # ---------- H. 类型蓝图 ----------
    "godot-genre-action-rpg": ("类型蓝图", "动作 RPG 蓝本：刷装、天赋、实时战斗、技能树。", ""),
    "godot-genre-fighting": ("类型蓝图", "格斗游戏：帧数据、指令输入、回滚网码。", ""),
    "godot-genre-platformer": ("类型蓝图", "平台跳跃：手感打磨、关卡设计。", "做 2D 平台跳跃推荐"),
    "godot-genre-shooter": ("类型蓝图", "TPS/混合射击：软锁定、掩体、拟真瞄准。", ""),
    "godot-genre-shooter-fps": ("类型蓝图", "第一人称射击：镜头晃动、武器摆动、命中判定。", ""),
    "godot-genre-moba": ("类型蓝图", "MOBA：分路、塔仇恨、战争迷雾。", ""),
    "godot-genre-rts": ("类型蓝图", "即时战略：单位选择、指令、战争迷雾。", ""),
    "godot-genre-tower-defense": ("类型蓝图", "塔防：波次、目标优先级、迷宫布局。", ""),
    "godot-genre-metroidvania": ("类型蓝图", "银河城：能力门、世界连通、地图揭示。", ""),
    "godot-genre-open-world": ("类型蓝图", "开放世界：区块流式、浮点原点、HLOD。", ""),
    "godot-genre-roguelike": ("类型蓝图", "肉鸽：程序生成、永久死亡、meta 进度。", ""),
    "godot-genre-survival": ("类型蓝图", "生存：需求系统、合成、基地建造。", ""),
    "godot-genre-card-game": ("类型蓝图", "卡牌游戏：牌组、效果结算、Command 模式。", ""),
    "godot-genre-educational": ("类型蓝图", "教育游戏：自适应难度、间隔重复。", ""),
    "godot-genre-horror": ("类型蓝图", "恐怖游戏：张力节奏、Director AI、理智系统。", ""),
    "godot-genre-puzzle": ("类型蓝图", "解谜：撤销、网格逻辑、非语言教学。", ""),
    "godot-genre-visual-novel": ("类型蓝图", "视觉小说：分支叙事、快退、持久 flag。", ""),
    "godot-genre-romance": ("类型蓝图", "恋爱/约会模拟：好感、多属性关系、路线。", ""),
    "godot-genre-battle-royale": ("类型蓝图", "吃鸡：缩圈、部署、相关性网络。", ""),
    "godot-genre-idle-clicker": ("类型蓝图", "放置/点击类：大数字、指数增长、飞升。", ""),
    "godot-genre-party": ("类型蓝图", "派对游戏：小游戏合集、本地多人、分屏。", ""),
    "godot-genre-racing": ("类型蓝图", "竞速：车辆物理、检查点、橡胶带 AI。", ""),
    "godot-genre-rhythm": ("类型蓝图", "音游：BPM 指挥、判定、延迟补偿。", ""),
    "godot-genre-sandbox": ("类型蓝图", "沙盒：体素、元胞自动机、涌现玩法。", ""),
    "godot-genre-simulation": ("类型蓝图", "模拟/经营：经济、时间推进、反馈循环。", ""),
    "godot-genre-sports": ("类型蓝图", "体育：球物理、队形 AI、裁判权威。", ""),
    "godot-genre-stealth": ("类型蓝图", "潜行：视野锥、警戒态、声音传播。", ""),

    # ---------- DSH 相关（非 godot）----------
    "author-agent-preset": ("DSH·开发", "在本 harness 里新建或修改 agent 预设(.agent-presets/<id>/)，读参考→写配置→挂载校验。", ""),
    "dsh-skill-ops": ("DSH·开发", "DSH skill 全生命周期运维剧本：加/删/禁用/恢复/导入 skill、需求转 skill。触发词：装 skill、skill 管理。", ""),
    "grill-me": ("DSH·开发", "帮你持续拷问一个计划/设计，逐分支深挖直到达成共识。用来打磨方案设计。", ""),
    "web-access": ("DSH·联网", "所有联网操作统一入口：网页搜索/抓取、登录后操作、动态渲染页面、社交媒体内容。", ""),
}

def main():
    if not TASK.exists():
        raise SystemExit(f"缺任务文件: {TASK}，请先 ①生成AI任务 或 template --all")
    d = json.loads(TASK.read_text(encoding="utf-8"))
    filled = 0
    missing = []
    for sid, payload in d["skills"].items():
        if sid not in DATA:
            missing.append(sid)
            continue
        cat, desc, note = DATA[sid]
        payload["category"] = cat
        payload["description"] = desc
        payload["note"] = note
        filled += 1
    TASK.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已填 {filled}/{len(DATA)} 个 skill。")
    if missing:
        print("任务文件里有但 DATA 里没定义的：", missing)

if __name__ == "__main__":
    main()