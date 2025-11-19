import asyncio
import time
import re
from typing import List
from mcp_server import LMStudioClient

# 翻译配置
MAX_TOKENS = 4000
QA_MAX_ATTEMPTS = 3  # 质量检查最大尝试次数
MAX_ENGLISH_RATIO = 0.2  # 译文中英文字符占比阈值
CHUNK_SIZE = 2500  # 每块文本的目标字符数
MAX_CHUNK_SIZE = 3000  # 每块文本的最大字符数
MAX_RETRIES = 3  # 翻译重试次数
RETRY_DELAY = 2  # 重试延迟（秒）


def english_char_ratio(text: str) -> float:
    """估算文本中英文字母占比"""
    if not text:
        return 0.0
    english_chars = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return english_chars / max(len(text), 1)


def analyze_translation_quality(source_text: str, translated_text: str) -> List[str]:
    """简单启发式检测翻译质量问题"""
    issues: List[str] = []
    stripped = translated_text.strip()
    
    if not stripped:
        issues.append("译文为空或仅包含空白。")
    
    ratio = english_char_ratio(stripped)
    if ratio > MAX_ENGLISH_RATIO:
        issues.append(
            f"译文包含过多英文字符（占比 {ratio:.0%}），请全部翻译成中文。"
        )
    
    if stripped and stripped.strip() == source_text.strip():
        issues.append("输出与原文相同，看起来未翻译。")
    
    if "Translation" in translated_text or "翻译：" in translated_text:
        issues.append("译文中包含提示词或'Translation'字样，请去除。")
    
    return issues


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    将长文本智能分割成小块，保持段落完整性
    
    Args:
        text: 要分割的文本
        chunk_size: 目标块大小（字符数）
    
    Returns:
        文本块列表
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    for para in paragraphs:
        # 如果单个段落就超过最大限制，需要按句子分割
        if len(para) > MAX_CHUNK_SIZE:
            # 先保存当前块
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # 按句子分割长段落
            sentences = para.replace('。', '。\n').replace('. ', '.\n').split('\n')
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # 如果单个句子也超过最大限制，强制分割
                if len(sentence) > MAX_CHUNK_SIZE:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                    
                    # 将超长句子按固定大小分割
                    for i in range(0, len(sentence), MAX_CHUNK_SIZE):
                        chunk_part = sentence[i:i + MAX_CHUNK_SIZE]
                        chunks.append(chunk_part)
                elif len(current_chunk) + len(sentence) > MAX_CHUNK_SIZE:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
        else:
            # 检查添加这个段落是否会超过限制
            if len(current_chunk) + len(para) + 2 > chunk_size:
                # 保存当前块，开始新块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
    
    # 添加最后一块
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


async def _call_llm_with_retry(client, messages, max_retries=MAX_RETRIES):
    """
    带重试机制的LLM调用函数
    """
    for attempt in range(max_retries):
        try:
            return await client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=MAX_TOKENS
            )
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"LLM调用失败，已重试 {max_retries} 次: {e}")
                raise
            
            delay = RETRY_DELAY * (2 ** attempt)  # 指数退避
            print(f"LLM调用失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
            await asyncio.sleep(delay)
    
    return {}


def _protect_images(text: str) -> tuple[str, dict[str, str]]:
    """
    Replaces markdown image syntax with placeholders to prevent LLM from altering them.
    Returns the text with placeholders and a dictionary mapping placeholders to original image syntax.
    """
    placeholders = {}
    # Regex to find markdown image syntax: ![alt text](url) or ![alt text](url "title")
    pattern = re.compile(r'!\[.*?\]\(.*?\)')
    
    def replace_match(match):
        original = match.group(0)
        placeholder = f"[[IMG_{len(placeholders)}]]"
        placeholders[placeholder] = original
        return placeholder
        
    protected_text = pattern.sub(replace_match, text)
    return protected_text, placeholders

def _restore_images(text: str, placeholders: dict[str, str]) -> str:
    """
    Restores original markdown image syntax from placeholders.
    """
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text


async def _translate_text(client: LMStudioClient, text: str, target_lang: str = "Chinese") -> str:
    """
    Translates text to the target language using LM Studio.
    Handles long text by splitting into chunks.
    Preserves markdown images.
    """
    if not text:
        return ""

    # Protect images
    protected_text, placeholders = _protect_images(text)
    
    # Split into chunks if necessary
    chunks = split_text_into_chunks(protected_text)
    translated_chunks = []
    
    total_chunks = len(chunks)
    if total_chunks > 1:
        print(f"文本较长({len(text)}字符)，将分块翻译...")
        print(f"分成 {total_chunks} 块进行翻译")
    
    for i, chunk in enumerate(chunks):
        if total_chunks > 1:
            print(f"翻译第 {i+1}/{total_chunks} 块 ({len(chunk)}字符)...")
            
        prompt = f"""请将以下英文新闻翻译成地道的中文。
要求：
1. 保持专业、准确，符合中文阅读习惯。
2. 保留所有特殊符号、数字和专有名词。
3. 不要翻译代码块或技术参数。
4. **绝对不要修改或翻译任何 [[IMG_N]] 格式的占位符，保留它们在原文中的位置。**
5. 直接输出翻译结果，不要包含"翻译："或"Translation:"等前缀。

原文：
{chunk}

翻译："""
        
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的翻译助手，擅长将英文翻译成{target_lang}。请保留文中的 [[IMG_N]] 占位符。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await _call_llm_with_retry(client, messages)
            translated_content = response['choices'][0]['message']['content'].strip()
            # Clean up potential prefixes
            if translated_content.startswith("翻译："):
                translated_content = translated_content[3:].strip()
            translated_chunks.append(translated_content)
        except Exception as e:
            print(f"Error translating chunk {i+1}: {e}")
            # If translation fails, keep original chunk to avoid data loss
            translated_chunks.append(chunk)

    # Join chunks
    full_translation = "\n\n".join(translated_chunks)
    
    # Restore images
    final_translation = _restore_images(full_translation, placeholders)
    
    return final_translation


async def _ensure_translation_quality(
    client,
    source_text: str,
    initial_translation: str,
) -> str:
    """调用LLM进行质量复查，如不合格则请求改写"""
    candidate = initial_translation
    
    for attempt in range(QA_MAX_ATTEMPTS):
        issues = analyze_translation_quality(source_text, candidate)
        if not issues:
            return candidate
        
        if attempt == QA_MAX_ATTEMPTS - 1:
            print(f"质量检查仍存在问题：{' ; '.join(issues)}，返回最新结果。")
            return candidate
        
        print(f"质量检查发现问题（{issues}），尝试自动修复 {attempt + 1}/{QA_MAX_ATTEMPTS - 1}")
        candidate = await _request_translation_revision(
            client, source_text, candidate, issues
        )
        candidate = candidate.replace('\x00', '').strip()
    
    return candidate


async def _request_translation_revision(
    client,
    source_text: str,
    current_translation: str,
    issues: List[str],
) -> str:
    """请求LLM基于反馈重新润色译文"""
    messages = [
        {
            "role": "system",
            "content": "你是一名资深的中英翻译审校专家，需要确保输出严格为流畅、准确的中文。",
        },
        {
            "role": "user",
            "content": (
                "请根据以下原文和当前译文，修复列出的问题，输出改进后的中文译文。"
                "不要重复原文，不要添加额外解释或提示词，只输出修改后的译文正文。\n"
                f"原文：\n{source_text}\n\n"
                f"当前译文：\n{current_translation}\n\n"
                f"需修复的问题：\n- " + "\n- ".join(issues)
            ),
        },
    ]
    
    try:
        response = await client.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=MAX_TOKENS,
        )
        
        if "choices" in response and response["choices"]:
            revised = response["choices"][0].get("message", {}).get("content", "").strip()
            if revised:
                return revised
    except Exception as e:
        print(f"质量修复调用失败: {e}")
    
    print("质量修复调用失败，返回原译文。")
    return current_translation


async def _translate_article_async(article):
    """
    Async function to translate article title and content with quality assurance.
    """
    client = LMStudioClient()
    try:
        print(f"Translating article: {article.get('title', 'No Title')}")
        
        # Translate title with retry
        title_translation = await _translate_text(client, article.get('title', ''))
        title_zh = await _ensure_translation_quality(
            client, article.get('title', ''), title_translation
        )
        
        # Translate content with retry and chunking
        content_translation = await _translate_text(client, article.get('content', ''))
        content_zh = await _ensure_translation_quality(
            client, article.get('content', ''), content_translation
        )
        
        article['title_zh'] = title_zh
        article['content_zh'] = content_zh
    finally:
        await client.close()
    
    return article


def translate_article(article):
    """
    Synchronous wrapper to translate an article.
    Adds 'title_zh' and 'content_zh' fields to the article dictionary.
    """
    return asyncio.run(_translate_article_async(article))
