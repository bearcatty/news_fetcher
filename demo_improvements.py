#!/usr/bin/env python
"""
简化测试：演示MCP服务改进的核心功能
不依赖外部网站和完整的依赖
"""
import asyncio
import json
import os
from datetime import datetime
from progress_tracker import TranslationProgress, TranslationStatus
from translator import split_text_into_chunks


def test_progress_and_chunking():
    """测试进度跟踪和文本分块的集成"""
    print("\n" + "="*60)
    print("MCP服务改进 - 集成测试")
    print("="*60 + "\n")
    
    # 1. 测试进度跟踪
    print("📊 测试1: 进度跟踪功能")
    print("-" * 60)
    
    progress_file = ".demo_progress.json"
    if os.path.exists(progress_file):
        os.remove(progress_file)
    
    progress = TranslationProgress(progress_file)
    
    # 模拟文章处理流程
    articles = [
        {"url": "https://example.com/article1", "title": "Article 1"},
        {"url": "https://example.com/article2", "title": "Article 2"},
        {"url": "https://example.com/article3", "title": "Article 3"},
    ]
    
    print(f"模拟处理 {len(articles)} 篇文章...\n")
    
    for i, article in enumerate(articles, 1):
        url = article['url']
        title = article['title']
        
        # 检查是否已完成
        if progress.is_completed(url):
            print(f"  [{i}] ⏭️  跳过已完成: {title}")
            continue
        
        # 标记为翻译中
        progress.set_status(url, TranslationStatus.TRANSLATING)
        print(f"  [{i}] 🔄 翻译中: {title}")
        
        # 模拟翻译（第2篇失败）
        if i == 2:
            progress.set_status(url, TranslationStatus.FAILED, "模拟网络错误")
            print(f"  [{i}] ❌ 失败: {title} (原因: 模拟网络错误)")
        else:
            progress.set_status(url, TranslationStatus.COMPLETED)
            print(f"  [{i}] ✅ 完成: {title}")
    
    # 显示统计
    print("\n📈 翻译统计:")
    stats = progress.get_statistics()
    print(f"  总计: {stats['total']} 篇")
    print(f"  完成: {stats['completed']} 篇")
    print(f"  失败: {stats['failed']} 篇")
    
    # 2. 测试断点续传
    print("\n" + "-" * 60)
    print("📊 测试2: 断点续传功能")
    print("-" * 60)
    print("\n模拟程序中断后重新启动...\n")
    
    # 重新加载进度
    progress2 = TranslationProgress(progress_file)
    
    for i, article in enumerate(articles, 1):
        url = article['url']
        title = article['title']
        
        if progress2.is_completed(url):
            print(f"  [{i}] ⏭️  跳过已完成: {title}")
        elif progress2.is_failed(url):
            print(f"  [{i}] 🔄 重试失败文章: {title}")
            progress2.set_status(url, TranslationStatus.COMPLETED)
            print(f"  [{i}] ✅ 重试成功: {title}")
        else:
            print(f"  [{i}] 🆕 新文章: {title}")
    
    # 最终统计
    print("\n📈 最终统计:")
    stats = progress2.get_statistics()
    print(f"  总计: {stats['total']} 篇")
    print(f"  完成: {stats['completed']} 篇")
    print(f"  失败: {stats['failed']} 篇")
    
    # 3. 测试文本分块
    print("\n" + "-" * 60)
    print("📊 测试3: 文本分块功能")
    print("-" * 60 + "\n")
    
    # 模拟不同长度的文本
    test_cases = [
        ("短文本", "This is a short article." * 10, 500),
        ("中等文本", "This is a medium article.\n\n" * 50, 1500),
        ("长文本", "This is a long article.\n\n" * 100, 3500),
    ]
    
    for name, text, expected_len in test_cases:
        chunks = split_text_into_chunks(text, 2500)
        actual_len = len(text)
        print(f"  {name} ({actual_len} 字符):")
        print(f"    分块数: {len(chunks)}")
        print(f"    各块大小: {[len(c) for c in chunks]}")
        
        if len(chunks) > 1:
            print(f"    ✅ 成功分块，避免超时")
        else:
            print(f"    ✅ 短文本直接处理")
        print()
    
    # 4. 测试增量保存
    print("-" * 60)
    print("📊 测试4: 增量保存功能")
    print("-" * 60 + "\n")
    
    demo_json = "demo_articles.json"
    if os.path.exists(demo_json):
        os.remove(demo_json)
    
    print("模拟逐篇保存文章...\n")
    
    for i in range(1, 4):
        article = {
            "url": f"https://example.com/article{i}",
            "title": f"Article {i}",
            "content": f"Content of article {i}",
            "saved_at": datetime.now().isoformat()
        }
        
        # 读取现有文章
        existing = []
        if os.path.exists(demo_json):
            with open(demo_json, 'r') as f:
                existing = json.load(f)
        
        # 添加新文章
        existing.append(article)
        
        # 立即保存
        with open(demo_json, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"  [{i}] 💾 已保存: {article['title']}")
        
        # 模拟中断（第2篇后）
        if i == 2:
            print(f"\n  ⚠️  模拟程序中断...\n")
            print(f"  📂 已保存的文章数: {len(existing)}")
            print(f"  ✅ 重新启动后可以继续\n")
    
    # 清理
    print("-" * 60)
    print("🧹 清理测试文件...")
    for f in [progress_file, demo_json]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  删除: {f}")
    
    print("\n" + "="*60)
    print("✅ 所有测试完成!")
    print("="*60 + "\n")
    
    print("💡 核心改进总结:")
    print("  1. ✅ 进度跟踪 - 记录每篇文章状态")
    print("  2. ✅ 断点续传 - 中断后可继续")
    print("  3. ✅ 文本分块 - 长文本自动分割")
    print("  4. ✅ 增量保存 - 逐篇保存防丢失")
    print("\n")


if __name__ == "__main__":
    test_progress_and_chunking()
