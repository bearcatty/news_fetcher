#!/usr/bin/env python
import unittest
import os
import sys
import json

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

"""
测试文本分块和进度跟踪功能
"""
from translator import split_text_into_chunks
from progress_tracker import TranslationProgress, TranslationStatus


def test_text_chunking():
    """测试文本分块功能"""
    print("=== 测试文本分块功能 ===\n")
    
    # 测试短文本
    short_text = "This is a short text."
    chunks = split_text_into_chunks(short_text, 2500)
    print(f"短文本 ({len(short_text)} 字符):")
    print(f"  分块数: {len(chunks)}")
    assert len(chunks) == 1, "短文本应该只有一块"
    print("  ✓ 通过\n")
    
    # 测试长文本
    long_text = "This is a paragraph.\n\n" * 200  # 约4000字符
    chunks = split_text_into_chunks(long_text, 2500)
    print(f"长文本 ({len(long_text)} 字符):")
    print(f"  分块数: {len(chunks)}")
    print(f"  各块大小: {[len(c) for c in chunks]}")
    assert len(chunks) > 1, "长文本应该被分成多块"
    assert all(len(c) <= 3000 for c in chunks), "每块不应超过最大限制"
    print("  ✓ 通过\n")
    
    # 测试超长段落
    very_long_para = "A" * 5000
    chunks = split_text_into_chunks(very_long_para, 2500)
    print(f"超长段落 ({len(very_long_para)} 字符):")
    print(f"  分块数: {len(chunks)}")
    print(f"  各块大小: {[len(c) for c in chunks]}")
    assert len(chunks) > 1, "超长段落应该被分割"
    print("  ✓ 通过\n")


def test_progress_tracking():
    """测试进度跟踪功能"""
    print("=== 测试进度跟踪功能 ===\n")
    
    # 创建测试进度跟踪器
    import os
    test_file = ".test_progress.json"
    if os.path.exists(test_file):
        os.remove(test_file)
    
    progress = TranslationProgress(test_file)
    
    # 测试设置状态
    test_url = "https://example.com/article1"
    progress.set_status(test_url, TranslationStatus.PENDING)
    print(f"设置状态为 PENDING")
    assert progress.get_status(test_url) == "pending"
    print("  ✓ 通过\n")
    
    # 测试更新状态
    progress.set_status(test_url, TranslationStatus.TRANSLATING)
    print(f"更新状态为 TRANSLATING")
    assert progress.get_status(test_url) == "translating"
    print("  ✓ 通过\n")
    
    # 测试完成状态
    progress.set_status(test_url, TranslationStatus.COMPLETED)
    print(f"更新状态为 COMPLETED")
    assert progress.is_completed(test_url)
    print("  ✓ 通过\n")
    
    # 测试失败状态
    test_url2 = "https://example.com/article2"
    progress.set_status(test_url2, TranslationStatus.FAILED, "Test error")
    print(f"设置失败状态")
    assert progress.is_failed(test_url2)
    failed = progress.get_failed_articles()
    assert test_url2 in failed
    print("  ✓ 通过\n")
    
    # 测试统计
    stats = progress.get_statistics()
    print(f"统计信息:")
    print(f"  总计: {stats['total']}")
    print(f"  完成: {stats['completed']}")
    print(f"  失败: {stats['failed']}")
    assert stats['total'] == 2
    assert stats['completed'] == 1
    assert stats['failed'] == 1
    print("  ✓ 通过\n")
    
    # 测试重置失败
    progress.reset_failed()
    print(f"重置失败状态")
    assert not progress.is_failed(test_url2)
    print("  ✓ 通过\n")
    
    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)
    print("清理测试文件完成\n")


def main():
    print("\n" + "="*50)
    print("MCP 服务可靠性改进 - 功能测试")
    print("="*50 + "\n")
    
    try:
        test_text_chunking()
        test_progress_tracking()
        
        print("="*50)
        print("✓ 所有测试通过!")
        print("="*50 + "\n")
        
        print("下一步:")
        print("1. 运行 'python scraper.py --stats' 查看当前进度")
        print("2. 运行 'python scraper.py' 开始抓取新闻")
        print("3. 如有失败，运行 'python scraper.py --retry' 重试")
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
