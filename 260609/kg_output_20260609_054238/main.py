#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm
import os
import sys
import shutil
from datetime import datetime

def create_output_directory():
    """创建带时间戳的输出目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"kg_output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ 创建输出目录: {output_dir}")
    return output_dir

def copy_source_and_font(output_dir):
    """复制源代码和字体文件到输出目录"""
    # 获取当前脚本路径
    script_path = os.path.abspath(__file__)
    script_name = os.path.basename(script_path)
    
    # 复制源代码
    dest_script = os.path.join(output_dir, script_name)
    shutil.copy2(script_path, dest_script)
    print(f"✓ 已复制源代码: {dest_script}")
    
    # 查找并复制字体文件
    local_fonts = [
        'wqy-microhei.ttc',
        'wqy-zenhei.ttc',
        'SimHei.ttf',
        'msyh.ttc',
        'NotoSansCJK-Regular.ttc',
        'DroidSansFallback.ttf'
    ]
    
    current_dir = os.path.dirname(script_path)
    copied_fonts = []
    
    for font_file in local_fonts:
        font_path = os.path.join(current_dir, font_file)
        if os.path.exists(font_path):
            dest_font = os.path.join(output_dir, font_file)
            shutil.copy2(font_path, dest_font)
            copied_fonts.append(font_file)
            print(f"✓ 已复制字体文件: {font_file}")
    
    if not copied_fonts:
        print("⚠ 未找到字体文件，仅复制源代码")
    
    return copied_fonts

def load_local_font():
    """加载本地字体文件"""
    # 本地字体文件列表（按优先级排序）
    local_fonts = [
        'wqy-microhei.ttc',      # 文泉驿微米黑
        'wqy-zenhei.ttc',        # 文泉驿正黑
        'SimHei.ttf',            # 黑体
        'msyh.ttc',              # 微软雅黑
        'NotoSansCJK-Regular.ttc',  # 思源黑体
        'DroidSansFallback.ttf'     # Android备用字体
    ]
    
    # 当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for font_file in local_fonts:
        font_path = os.path.join(current_dir, font_file)
        if os.path.exists(font_path):
            try:
                # 添加字体文件
                fm.fontManager.addfont(font_path)
                # 获取字体名称
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()
                # 设置全局字体
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['font.sans-serif'] = [font_name]
                plt.rcParams['axes.unicode_minus'] = False
                print(f"✓ 成功加载本地字体: {font_file} -> {font_name}")
                return True, font_name
            except Exception as e:
                print(f"✗ 加载字体失败 {font_file}: {e}")
                continue
    
    print("✗ 未找到本地字体文件")
    print("请下载字体文件到当前目录:")
    print("  wget https://github.com/anthonyfok/fonts-wqy-microhei/raw/master/wqy-microhei.ttc")
    return False, None

def load_knowledge_graph(json_file_path):
    """加载知识图谱JSON文件（指定UTF-8编码）"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def create_graph_from_data(data):
    """从数据创建NetworkX图"""
    G = nx.Graph()
    
    # 添加节点（角色）
    characters = data['characters']
    for char in characters:
        node_attrs = {
            'name': char['name'],
            'alias': ', '.join(char['alias']) if char['alias'] else '无',
            'species': char['species'],
            'identity': ', '.join(char['identity']),
            'personality': ', '.join(char['personality']),
            'chapter_role': char['chapter_role'],
            'groups': char['groups']
        }
        G.add_node(char['name'], **node_attrs)
    
    # 添加边（关系）
    relationships = data['relationships']
    for rel in relationships:
        role_desc = f"{', '.join(rel['role_1_to_2'])} → {', '.join(rel['role_2_to_1'])}"
        edge_attrs = {
            'description': rel['description'],
            'role_1_to_2': ', '.join(rel['role_1_to_2']),
            'role_2_to_1': ', '.join(rel['role_2_to_1']),
            'story_section': rel['story_section'],
            'label': role_desc[:30]
        }
        G.add_edge(rel['character1'], rel['character2'], **edge_attrs)
    
    return G

def assign_node_colors_by_group(G, groups_data):
    """根据群体分配节点颜色"""
    group_colors = {
        '取经团队': '#FF6B6B',
        '白骨洞势力': '#4ECDC4',
        '白骨精化身': '#95E77E',
        '天庭神祇': '#FFE66D',
        '佛教体系': '#C7B9FF'
    }
    
    default_color = '#D3D3D3'
    
    node_colors = []
    node_group_mapping = {}
    
    for node in G.nodes(data=True):
        node_groups = node[1].get('groups', [])
        if node_groups:
            primary_group = node_groups[0]
            color = group_colors.get(primary_group, default_color)
            node_group_mapping[node[0]] = primary_group
        else:
            color = default_color
            node_group_mapping[node[0]] = '未分组'
        node_colors.append(color)
    
    return node_colors, node_group_mapping

def visualize_knowledge_graph(G, groups_data, chapter_info, output_dir):
    """可视化知识图谱（使用本地字体）"""
    
    # 加载本地字体
    font_loaded, font_name = load_local_font()
    
    if not font_loaded:
        print("\n警告: 未找到中文字体，将生成英文版")
        return None
    
    # 创建大图
    fig = plt.figure(figsize=(20, 14), facecolor='white')
    
    # 主图区域
    ax_main = plt.axes([0.05, 0.15, 0.60, 0.75])
    
    # 计算节点布局
    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)
    
    # 分配节点颜色
    node_colors, node_group_mapping = assign_node_colors_by_group(G, groups_data)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=1.5, edge_color='gray', ax=ax_main)
    
    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2500, 
                          alpha=0.9, edgecolors='black', linewidths=2, ax=ax_main)
    
    # 绘制节点标签（使用中文字体）
    labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold', 
                           font_family=font_name, ax=ax_main)
    
    # 添加边的标签
    edge_labels = {}
    for edge in G.edges(data=True):
        role_text = edge[2].get('role_1_to_2', '')
        if len(role_text) < 20 and role_text:
            edge_labels[(edge[0], edge[1])] = role_text[:15]
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7, ax=ax_main, 
                                 label_pos=0.5, rotate=False, font_family=font_name)
    
    # 设置标题
    title = f"{chapter_info.get('chapter_name', '知识图谱')}\n{chapter_info.get('chapter_full_title', '')}"
    ax_main.set_title(title, fontsize=16, fontweight='bold', pad=20, fontfamily=font_name)
    ax_main.axis('off')
    
    # === 创建图例区域 ===
    ax_legend = plt.axes([0.68, 0.15, 0.30, 0.75])
    ax_legend.axis('off')
    
    group_colors = {
        '取经团队': '#FF6B6B',
        '白骨洞势力': '#4ECDC4',
        '白骨精化身': '#95E77E',
        '天庭神祇': '#FFE66D',
        '佛教体系': '#C7B9FF'
    }
    
    y_offset = 0.95
    ax_legend.text(0.05, y_offset, "角色群体（按颜色区分）", fontsize=14, 
                   fontweight='bold', transform=ax_legend.transAxes, fontfamily=font_name)
    y_offset -= 0.05
    
    for group_name, color in group_colors.items():
        rect = Rectangle((0.05, y_offset - 0.03), 0.04, 0.04, facecolor=color, 
                        edgecolor='black', transform=ax_legend.transAxes)
        ax_legend.add_patch(rect)
        ax_legend.text(0.12, y_offset - 0.02, group_name, fontsize=11, 
                      transform=ax_legend.transAxes, verticalalignment='top', 
                      fontfamily=font_name)
        y_offset -= 0.05
    
    # 添加群体详细信息
    y_offset -= 0.05
    ax_legend.text(0.05, y_offset, "群体详情", fontsize=14, fontweight='bold', 
                  transform=ax_legend.transAxes, fontfamily=font_name)
    y_offset -= 0.05
    
    for group in groups_data[:3]:  # 只显示前3个群体，避免溢出
        members = '、'.join(group['members'][:3])
        if len(group['members']) > 3:
            members += f" 等{len(group['members'])}人"
        
        ax_legend.text(0.05, y_offset, f"【{group['name']}】", fontsize=11, 
                      fontweight='bold', transform=ax_legend.transAxes, 
                      color=group_colors.get(group['name'], '#000000'),
                      fontfamily=font_name)
        y_offset -= 0.035
        ax_legend.text(0.08, y_offset, f"类型: {group['type']}", fontsize=9, 
                      transform=ax_legend.transAxes, fontfamily=font_name)
        y_offset -= 0.03
        ax_legend.text(0.08, y_offset, f"成员: {members}", fontsize=9, 
                      transform=ax_legend.transAxes, fontfamily=font_name)
        y_offset -= 0.03
        ax_legend.text(0.08, y_offset, f"描述: {group['description'][:40]}...", fontsize=8, 
                      transform=ax_legend.transAxes, style='italic', fontfamily=font_name)
        y_offset -= 0.06
        
        if y_offset < 0.05:
            break
    
    # 添加故事章节信息
    y_offset -= 0.05
    ax_legend.text(0.05, y_offset, f"故事章节: 第{chapter_info.get('chapter_number', '?')}回", 
                  fontsize=10, transform=ax_legend.transAxes, style='italic', fontfamily=font_name)
    y_offset -= 0.03
    desc_text = chapter_info.get('description', '')[:60]
    ax_legend.text(0.05, y_offset, f"概述: {desc_text}...", fontsize=9, 
                  transform=ax_legend.transAxes, style='italic', fontfamily=font_name)
    
    # 添加统计信息
    y_offset -= 0.08
    ax_legend.text(0.05, y_offset, "统计信息", fontsize=11, fontweight='bold', 
                  transform=ax_legend.transAxes, fontfamily=font_name)
    y_offset -= 0.04
    ax_legend.text(0.08, y_offset, f"总角色数: {G.number_of_nodes()}", fontsize=10, 
                  transform=ax_legend.transAxes, fontfamily=font_name)
    y_offset -= 0.03
    ax_legend.text(0.08, y_offset, f"总关系数: {G.number_of_edges()}", fontsize=10, 
                  transform=ax_legend.transAxes, fontfamily=font_name)
    
    plt.suptitle("《西游记》第27回「三打白骨精」知识图谱可视化", 
                fontsize=18, fontweight='bold', y=0.98, fontfamily=font_name)
    
    plt.tight_layout()
    
    # 保存图片到输出目录
    output_file = os.path.join(output_dir, 'knowledge_graph.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ 知识图谱已保存到: {output_file}")
    
    # 也保存一个PDF版本
    pdf_file = os.path.join(output_dir, 'knowledge_graph.pdf')
    plt.savefig(pdf_file, bbox_inches='tight', facecolor='white')
    print(f"✓ PDF版本已保存到: {pdf_file}")
    
    plt.show()
    return fig

def save_graph_to_file(G, output_dir):
    """将图谱数据保存为文本文件（UTF-8编码）"""
    output_file = os.path.join(output_dir, 'graph_data_export.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("知识图谱数据导出\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"节点数量（角色）: {G.number_of_nodes()}\n")
        f.write(f"边数量（关系）: {G.number_of_edges()}\n\n")
        
        f.write("节点列表:\n")
        f.write("-"*40 + "\n")
        for node, attrs in G.nodes(data=True):
            f.write(f"  • {node}\n")
            f.write(f"    身份: {attrs.get('identity', '')}\n")
            f.write(f"    种族: {attrs.get('species', '')}\n")
            f.write(f"    性格: {attrs.get('personality', '')}\n")
            f.write(f"    群体: {', '.join(attrs.get('groups', []))}\n\n")
        
        f.write("\n关系列表:\n")
        f.write("-"*40 + "\n")
        for u, v, attrs in G.edges(data=True):
            f.write(f"  • {u} ↔ {v}\n")
            f.write(f"    关系: {attrs.get('role_1_to_2', '')} → {attrs.get('role_2_to_1', '')}\n")
            f.write(f"    描述: {attrs.get('description', '')}\n")
            f.write(f"    情节: {attrs.get('story_section', '')}\n\n")
    
    print(f"✓ 图谱数据已保存到: {output_file}")

def print_graph_info(G):
    """打印图谱信息"""
    print("\n" + "="*60)
    print("知识图谱信息统计")
    print("="*60)
    print(f"节点数量（角色）: {G.number_of_nodes()}")
    print(f"边数量（关系）: {G.number_of_edges()}")
    
    print("\n节点列表:")
    for node, attrs in G.nodes(data=True):
        print(f"  - {node}: {attrs.get('identity', '')[:30]}")
    
    print("\n关系列表:")
    for u, v, attrs in G.edges(data=True):
        print(f"  - {u} ↔ {v}: {attrs.get('description', '')[:50]}...")

def save_json_to_output(data, output_dir):
    """保存JSON数据到输出目录"""
    output_file = os.path.join(output_dir, 'knowledge_graph_backup.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON数据已备份到: {output_file}")

def main():
    json_file_path = 'knowledge_graph.json'
    
    # 设置标准输出编码
    if sys.stdout.encoding != 'utf-8':
        print("警告: 控制台编码不是UTF-8")
    
    try:
        # 创建输出目录
        output_dir = create_output_directory()
        
        # 复制源代码和字体文件
        print("\n正在复制文件到输出目录...")
        copied_fonts = copy_source_and_font(output_dir)
        
        # 加载数据
        print("\n正在加载知识图谱数据...")
        data = load_knowledge_graph(json_file_path)
        
        # 保存JSON备份到输出目录
        save_json_to_output(data, output_dir)
        
        # 创建图
        print("正在创建图谱...")
        G = create_graph_from_data(data)
        
        # 提取章节信息
        chapter_info = {
            'chapter_name': data.get('chapter_name', ''),
            'chapter_full_title': data.get('chapter_full_title', ''),
            'chapter_number': data.get('chapter_number', ''),
            'description': data.get('description', '')
        }
        
        # 打印信息
        print_graph_info(G)
        
        # 保存文本数据到输出目录
        save_graph_to_file(G, output_dir)
        
        # 可视化
        print("\n正在生成中文可视化图表...")
        fig = visualize_knowledge_graph(G, data['groups'], chapter_info, output_dir)
        
        if fig:
            print(f"\n✅ 完成！所有文件已保存到: {output_dir}")
            print(f"   - 图片: {output_dir}/knowledge_graph.png")
            print(f"   - PDF: {output_dir}/knowledge_graph.pdf")
            print(f"   - 数据: {output_dir}/graph_data_export.txt")
            print(f"   - JSON备份: {output_dir}/knowledge_graph_backup.json")
            print(f"   - 源代码: {output_dir}/{os.path.basename(__file__)}")
            if copied_fonts:
                for font in copied_fonts:
                    print(f"   - 字体: {output_dir}/{font}")
        else:
            print(f"\n❌ 图表生成失败，但文本数据已保存到: {output_dir}")
            print("   请查看 graph_data_export.txt 文件了解中文内容")
        
        print("\n完成！")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file_path}")
        print("请确保JSON文件在当前目录下，并命名为 'knowledge_graph.json'")
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()